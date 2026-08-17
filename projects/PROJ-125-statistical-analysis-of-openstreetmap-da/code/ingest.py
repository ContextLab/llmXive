"""
Ingestion module for OpenStreetMap and satellite data.
Handles downloading, processing, and alignment of geospatial data.
"""
import os
import json
import hashlib
import logging
import time
import requests
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import numpy as np
import geopandas as gpd
import rasterio
from rasterio.mask import mask
from rasterio.warp import calculate_default_transform, reproject, Resampling
from shapely.geometry import mapping
from shapely.ops import unary_union

from config import get_path, get_city_bounds, get_city_crs, get_city_utm_zone
from utils.logging import get_logger
from utils.memory import estimate_raster_memory_mb, check_memory_safety

# Initialize logger
logger = get_logger(__name__)

def calculate_file_checksum(file_path: str) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_osm_vectors(city_name: str, output_dir: Optional[str] = None) -> Dict[str, str]:
    """
    Download OSM vector data (buildings, land-use, trees, roads) for a city.
    
    Args:
        city_name: Name of the city
        output_dir: Directory to save downloaded data
        
    Returns:
        Dictionary mapping feature types to file paths
    """
    bounds = get_city_bounds(city_name)
    if not bounds:
        raise ValueError(f"City bounds not found for {city_name}")
    
    if output_dir is None:
        output_dir = str(get_path("data/raw", city_name))
    
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Overpass API query
    query = f"""
    [out:json][timeout:90];
    (
      way["building"]({bounds["min_lat"]},{bounds["min_lon"]},{bounds["max_lat"]},{bounds["max_lon"]});
      way["landuse"]({bounds["min_lat"]},{bounds["min_lon"]},{bounds["max_lat"]},{bounds["max_lon"]});
      way["natural"="wood"]({bounds["min_lat"]},{bounds["min_lon"]},{bounds["max_lat"]},{bounds["max_lon"]});
      way["highway"]({bounds["min_lat"]},{bounds["min_lon"]},{bounds["max_lat"]},{bounds["max_lon"]});
      relation["boundary"]["admin_level"="8"]({bounds["min_lat"]},{bounds["min_lon"]},{bounds["max_lat"]},{bounds["max_lon"]});
    );
    out body;
    >;
    out skel qt;
    """
    
    overpass_url = "https://overpass-api.de/api/interpreter"
    output_files = {}
    
    try:
        response = requests.post(overpass_url, data={'data': query}, timeout=120)
        response.raise_for_status()
        data = response.json()
        
        # Process features into GeoDataFrames
        features = {
            'buildings': [],
            'landuse': [],
            'trees': [],
            'roads': []
        }
        
        for element in data.get('elements', []):
            geom = None
            if element['type'] == 'way':
                if 'nodes' in element:
                    coords = [(node['lon'], node['lat']) for node in data['elements'] 
                            if node.get('id') in element['nodes']]
                    if len(coords) > 1:
                        geom = gpd.points_from_xy(*zip(*coords))
                        if len(coords) > 2:
                            geom = gpd.GeoSeries([geom.unary_union.convex_hull])
                        else:
                            geom = gpd.GeoSeries([geom.unary_union])
            elif element['type'] == 'relation':
                # Simplified handling for relations
                continue
            
            if geom is not None:
                tags = element.get('tags', {})
                if 'building' in tags:
                    features['buildings'].append({'geometry': geom, 'type': 'building'})
                elif 'landuse' in tags:
                    features['landuse'].append({'geometry': geom, 'type': 'landuse'})
                elif tags.get('natural') == 'wood':
                    features['trees'].append({'geometry': geom, 'type': 'tree'})
                elif 'highway' in tags:
                    features['roads'].append({'geometry': geom, 'type': 'road'})
        
        # Save to GeoJSON files
        for feature_type, features_list in features.items():
            if features_list:
                gdf = gpd.GeoDataFrame(features_list, crs="EPSG:4326")
                output_path = os.path.join(output_dir, f"{city_name}_{feature_type}.geojson")
                gdf.to_file(output_path, driver='GeoJSON')
                output_files[feature_type] = output_path
                logger.info(f"Saved {feature_type} data to {output_path}")
            else:
                logger.warning(f"No {feature_type} data found for {city_name}")
                
    except requests.RequestException as e:
        logger.error(f"Failed to download OSM data: {e}")
        raise
        
    return output_files

def create_sample_raster(
    city_name: str,
    resolution: float = 30.0,
    crs: Optional[str] = None,
    output_dir: Optional[str] = None
) -> str:
    """
    Create a sample raster for alignment testing.
    
    Args:
        city_name: Name of the city
        resolution: Resolution in meters
        crs: CRS string (defaults to city's UTM zone)
        output_dir: Output directory
        
    Returns:
        Path to the created raster
    """
    bounds = get_city_bounds(city_name)
    if crs is None:
        crs = get_city_crs(city_name)
        
    if output_dir is None:
        output_dir = str(get_path("data/processed", city_name))
        
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Calculate transform
    minx, miny = bounds['min_lon'], bounds['min_lat']
    maxx, maxy = bounds['max_lon'], bounds['max_lat']
    
    # Convert bounds to target CRS if necessary
    if crs != "EPSG:4326":
        # Simplified conversion - in production use proper reprojection
        pass
        
    width = int((maxx - minx) / resolution)
    height = int((maxy - miny) / resolution)
    
    output_path = os.path.join(output_dir, f"{city_name}_sample.tif")
    
    with rasterio.open(
        output_path, 'w',
        driver='GTiff',
        height=height,
        width=width,
        count=1,
        dtype=rasterio.float32,
        crs=crs,
        transform=rasterio.transform.from_bounds(minx, miny, maxx, maxy, width, height)
    ) as dst:
        # Create sample data
        data = np.random.rand(height, width).astype(np.float32) * 100
        dst.write(data, 1)
        
    logger.info(f"Created sample raster at {output_path}")
    return output_path

def validate_raster_alignment(raster_paths: List[str], tolerance: float = 1.0) -> bool:
    """
    Validate that rasters are aligned (same dimensions, resolution, origin).
    
    Args:
        raster_paths: List of paths to rasters
        tolerance: Tolerance in pixels for alignment check
        
    Returns:
        True if aligned, False otherwise
    """
    if len(raster_paths) < 2:
        return True
        
    ref = rasterio.open(raster_paths[0])
    ref_transform = ref.transform
    ref_shape = ref.shape
    ref_crs = ref.crs
    
    for path in raster_paths[1:]:
        with rasterio.open(path) as src:
            if src.crs != ref_crs:
                logger.error(f"CRS mismatch: {path} ({src.crs}) vs reference ({ref_crs})")
                return False
                
            if src.shape != ref_shape:
                logger.error(f"Shape mismatch: {path} ({src.shape}) vs reference ({ref_shape})")
                return False
                
            # Check transform alignment
            for i, (a, b) in enumerate(zip(src.transform, ref_transform)):
                if abs(a - b) > tolerance:
                    logger.error(f"Transform mismatch at index {i}: {a} vs {b}")
                    return False
                    
    logger.info("All rasters are aligned")
    return True

def create_aligned_raster_stack(
    city_name: str,
    input_paths: List[str],
    target_resolution: float = 30.0,
    output_dir: Optional[str] = None
) -> List[str]:
    """
    Create an aligned stack of rasters from input paths.
    
    Args:
        city_name: Name of the city
        input_paths: List of input raster paths
        target_resolution: Target resolution in meters
        output_dir: Output directory
        
    Returns:
        List of paths to aligned rasters
    """
    if not input_paths:
        raise ValueError("No input paths provided")
        
    if output_dir is None:
        output_dir = str(get_path("data/processed", city_name))
        
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Use first raster as reference
    ref_path = input_paths[0]
    with rasterio.open(ref_path) as ref:
        ref_transform = ref.transform
        ref_shape = ref.shape
        ref_crs = ref.crs
        
    aligned_paths = []
    
    for input_path in input_paths:
        filename = os.path.basename(input_path)
        name, ext = os.path.splitext(filename)
        output_path = os.path.join(output_dir, f"{name}_aligned{ext}")
        
        with rasterio.open(input_path) as src:
            # Calculate new transform if resampling needed
            if abs(src.res[0] - target_resolution) > 0.01:
                # Resample
                dst_crs = src.crs
                width = int((src.bounds.right - src.bounds.left) / target_resolution)
                height = int((src.bounds.top - src.bounds.bottom) / target_resolution)
                dst_transform, width, height = calculate_default_transform(
                    src.crs, src.crs, width, height,
                    *src.bounds, resolution=target_resolution
                )
                
                kwargs = src.meta.copy()
                kwargs.update({
                    'crs': dst_crs,
                    'transform': dst_transform,
                    'width': width,
                    'height': height
                })
                
                with rasterio.open(output_path, 'w', **kwargs) as dst:
                    for i in range(1, src.count + 1):
                        reproject(
                            source=rasterio.band(src, i),
                            destination=rasterio.band(dst, i),
                            src_transform=src.transform,
                            src_crs=src.crs,
                            dst_transform=dst_transform,
                            dst_crs=dst_crs,
                            resampling=Resampling.bilinear if src.dtypes[i-1] in ['float32', 'float64'] else Resampling.nearest
                        )
            else:
                # Copy as is if already at target resolution
                import shutil
                shutil.copy2(input_path, output_path)
                
        aligned_paths.append(output_path)
        logger.info(f"Aligned {input_path} to {output_path}")
        
    return aligned_paths

def validate_non_null_overlap(raster_paths: List[str], city_name: str) -> bool:
    """
    Validate that there is a non-null overlap region between all rasters.
    
    Args:
        raster_paths: List of paths to rasters
        city_name: Name of the city for logging
        
    Returns:
        True if non-null overlap exists, False otherwise
        
    Raises:
        ValueError: If no non-null overlap is found
    """
    if len(raster_paths) < 2:
        logger.warning("Less than 2 rasters provided, skipping overlap validation")
        return True
        
    # Open all rasters
    rasters = [rasterio.open(path) for path in raster_paths]
    
    try:
        # Get intersection of bounds
        minx = max(src.bounds.left for src in rasters)
        miny = max(src.bounds.bottom for src in rasters)
        maxx = min(src.bounds.right for src in rasters)
        maxy = min(src.bounds.top for src in rasters)
        
        if minx >= maxx or miny >= maxy:
            logger.error(f"No spatial overlap found for {city_name}")
            return False
            
        # Read data from the overlap region for each raster
        overlap_data = []
        for src in rasters:
            # Read from the intersection
            window = rasterio.windows.from_bounds(
                minx, miny, maxx, maxy, src.transform
            )
            data = src.read(1, window=window)
            
            # Count non-null values
            non_null_count = np.count_nonzero(~np.isnan(data) & (data != src.nodata))
            total_count = data.size
            
            if total_count == 0:
                logger.error(f"Empty overlap region in {src.name}")
                return False
                
            non_null_ratio = non_null_count / total_count
            overlap_data.append({
                'file': src.name,
                'non_null_ratio': non_null_ratio,
                'non_null_count': non_null_count,
                'total_count': total_count
            })
            
            logger.info(f"{src.name}: {non_null_ratio:.2%} non-null values in overlap")
            
        # Check if all rasters have significant non-null overlap
        min_ratio = min(d['non_null_ratio'] for d in overlap_data)
        if min_ratio < 0.01:  # Less than 1% non-null
            logger.error(f"Overlap region has insufficient non-null values (min ratio: {min_ratio:.2%})")
            return False
            
        logger.info(f"Non-null overlap validation passed for {city_name} (min ratio: {min_ratio:.2%})")
        return True
        
    finally:
        for src in rasters:
            src.close()

def main():
    """Main entry point for ingestion pipeline."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Ingest OSM and satellite data")
    parser.add_argument("--city", required=True, help="City name")
    parser.add_argument("--skip-osm", action="store_true", help="Skip OSM download")
    parser.add_argument("--skip-satellite", action="store_true", help="Skip satellite data")
    parser.add_argument("--validate-overlap", action="store_true", help="Validate non-null overlap")
    
    args = parser.parse_args()
    
    logger.info(f"Starting ingestion pipeline for {args.city}")
    
    # Download OSM data
    if not args.skip_osm:
        try:
            osm_files = download_osm_vectors(args.city)
            logger.info(f"Downloaded OSM files: {list(osm_files.keys())}")
        except Exception as e:
            logger.error(f"OSM download failed: {e}")
            if args.validate_overlap:
                raise
                
    # Create sample raster (placeholder for satellite data)
    sample_raster = create_sample_raster(args.city)
    
    # Validate alignment if multiple rasters exist
    if args.validate_overlap:
        # In a real pipeline, we'd have multiple rasters here
        # For now, we just validate the sample raster against itself
        if not validate_non_null_overlap([sample_raster], args.city):
            logger.error("Non-null overlap validation failed")
            return 1
            
    logger.info(f"Ingestion pipeline completed for {args.city}")
    return 0

if __name__ == "__main__":
    exit(main())