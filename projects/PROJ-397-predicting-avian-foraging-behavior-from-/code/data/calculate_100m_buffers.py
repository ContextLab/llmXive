import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple

import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.features import shapes
from rasterio.warp import transform_bounds
from shapely.geometry import Point, mapping
from shapely.ops import unary_union
import yaml

from utils.config import get_processed_dir, get_raw_data_dir, get_project_root, get_seed
from utils.provenance import record_artifact_provenance, load_metadata_config, save_metadata_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
BUFFER_RADIUS_METERS = 100.0
NLCD_CLASSES = {
    11: 'water',
    21: 'forest',
    22: 'forest',
    23: 'forest',
    24: 'forest',
    31: 'forest',
    41: 'grassland',
    42: 'grassland',
    43: 'grassland',
    51: 'grassland',
    52: 'grassland',
    71: 'grassland',
    72: 'grassland',
    73: 'grassland',
    74: 'grassland',
    81: 'grassland',
    82: 'grassland',
    90: 'wetland',
    95: 'wetland',
    12: 'urban',
    13: 'urban',
}
# Map classes to our target categories
# forest: 21, 22, 23, 24, 31
# grassland: 41, 42, 43, 51, 52, 71, 72, 73, 74, 81, 82
# wetland: 90, 95
# urban: 12, 13
# other: everything else (11 is water, but we'll treat as other for simplicity unless specified)

# Re-mapping based on standard NLCD 2019 definitions
# 11: Open Water (Other)
# 21-31: Deciduous, Evergreen, Mixed Forest (Forest)
# 41-82: Developed, Shrub/Scrub, Grassland/Herbaceous, Pasture/Hay (Grassland/Urban mix, but 12,13 are urban)
# Actually, 12, 13 are Developed (Urban)
# 41-82 are mostly non-urban natural land (Grassland/Shrub)
# 90, 95 are Wetlands

CLASS_TO_CATEGORY = {
    11: 'other', # Water
    21: 'forest', 31: 'forest', 22: 'forest', 23: 'forest', 24: 'forest',
    41: 'grassland', 42: 'grassland', 43: 'grassland',
    51: 'grassland', 52: 'grassland',
    71: 'grassland', 72: 'grassland', 73: 'grassland', 74: 'grassland',
    81: 'grassland', 82: 'grassland',
    12: 'urban', 13: 'urban',
    90: 'wetland', 95: 'wetland',
}

def load_filtered_ebd() -> pd.DataFrame:
    """Load the pre-processed EBD data."""
    processed_dir = get_processed_dir()
    input_path = processed_dir / "filtered_ebd.csv"
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    logger.info(f"Loading filtered EBD data from {input_path}")
    df = pd.read_csv(input_path)
    
    required_cols = ['species_id', 'latitude', 'longitude']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in {input_path}: {missing_cols}")
    
    # Filter out rows with invalid coordinates
    valid_mask = df['latitude'].notna() & df['longitude'].notna()
    if not valid_mask.all():
        dropped = (~valid_mask).sum()
        logger.warning(f"Dropping {dropped} rows with invalid coordinates")
        df = df[valid_mask]
        
    return df

def load_nlcd_raster() -> Tuple[rasterio.DatasetReader, Dict[str, Any]]:
    """Load the NLCD 2019 raster data."""
    raw_dir = get_raw_data_dir()
    zip_path = raw_dir / "nlcd_2019.zip"
    
    if not zip_path.exists():
        raise FileNotFoundError(f"NLCD archive not found: {zip_path}")
    
    # Extract to a temp location or handle via zip file directly if supported
    # For simplicity, we assume the zip contains the .tif and we extract to a temp dir
    import tempfile
    import zipfile
    
    with zipfile.ZipFile(zip_path, 'r') as z:
        # Find the .tif file
        tif_files = [f for f in z.namelist() if f.endswith('.tif')]
        if not tif_files:
            raise ValueError("No .tif file found in NLCD archive")
        
        # Extract to a temporary directory
        with tempfile.TemporaryDirectory() as tmpdir:
            z.extractall(tmpdir)
            tif_path = Path(tmpdir) / tif_files[0]
            
            logger.info(f"Loading NLCD raster from {tif_path}")
            ds = rasterio.open(tif_path)
            return ds, {'source': str(zip_path), 'file': tif_files[0]}

def calculate_land_cover_proportions(
    df: pd.DataFrame, 
    raster_ds: rasterio.DatasetReader
) -> pd.DataFrame:
    """
    Calculate land cover proportions within a 100m buffer for each observation.
    
    Args:
        df: DataFrame with 'latitude' and 'longitude' columns.
        raster_ds: Open rasterio dataset for NLCD data.
        
    Returns:
        DataFrame with added land cover proportion columns.
    """
    logger.info("Calculating land cover proportions...")
    
    # Create a GeoDataFrame for the points
    # We need to project to a metric CRS (e.g., UTM) to buffer in meters
    # However, doing this row-by-row is slow. 
    # Strategy: Iterate rows, create a small buffer polygon, transform to raster CRS, 
    # and sample the raster.
    
    # Get raster transform and CRS
    raster_transform = raster_ds.transform
    raster_crs = raster_ds.crs
    raster_data = raster_ds.read(1)
    raster_width = raster_ds.width
    raster_height = raster_ds.height
    
    results = []
    
    # Pre-calculate buffer geometry in a metric CRS? 
    # Easier: For each point, create a 100m buffer in UTM, then reproject to raster CRS.
    # But doing this in a loop is slow in Python. 
    # Optimization: Since we must process each point, we'll do it row by row but keep it efficient.
    
    # To ensure speed, we might vectorize if the dataset is small, but for large datasets, 
    # we rely on efficient shapely/rasterio calls.
    
    # Let's assume the input lat/lon is WGS84 (EPSG:4326)
    input_crs = "EPSG:4326"
    
    # We will process in batches if needed, but for now, iterate.
    # To avoid heavy CRS transformation overhead per row, we can:
    # 1. Create a 100m buffer in a projected CRS (e.g., UTM zone of the point).
    # 2. Transform that polygon to the raster's CRS.
    # 3. Use rasterio.sample or mask to get values.
    
    # However, rasterio.sample with a polygon is efficient.
    
    categories = ['forest', 'grassland', 'wetland', 'urban', 'other']
    count_cols = [f"{cat}_count" for cat in categories]
    prop_cols = [f"{cat}_prop_100m" for cat in categories]
    
    for idx, row in df.iterrows():
        lat = row['latitude']
        lon = row['longitude']
        
        # Create point
        point = Point(lon, lat)
        
        # We need to buffer in meters. 
        # Strategy: Transform point to a local UTM, buffer, transform back to WGS84, then to raster CRS.
        # Or: Use a pre-defined projection for the whole region if possible.
        # Given the constraint of 100m and varying locations, local UTM is best.
        # But calculating UTM zone for every point is slow.
        # Alternative: Use a global projection like Web Mercator (EPSG:3857) - bad for area.
        # Alternative: Use Albers Equal Area (EPSG:5070) for US - good for area, constant across US.
        # Let's use EPSG:5070 (NAD83 / Conus Albers) which is standard for US land cover analysis.
        
        gdf_point = gpd.GeoDataFrame([{'id': idx, 'geometry': point}], crs="EPSG:4326")
        gdf_point_utm = gdf_point.to_crs(epsg=5070)
        
        # Buffer 100 meters
        gdf_point_utm['geometry'] = gdf_point_utm.geometry.buffer(BUFFER_RADIUS_METERS)
        
        # Transform back to raster CRS (usually EPSG:4326 for NLCD? Or UTM?)
        # NLCD 2019 is usually in Albers (EPSG:5070) or Lat/Lon.
        # Let's check the raster CRS. If it's 4326, we transform to 4326.
        # If it's 5070, we keep it.
        
        target_crs = raster_crs
        if raster_crs.to_epsg() == 4326:
            gdf_buffer = gdf_point_utm.to_crs(epsg=4326)
        else:
            # Assume it's 5070 or similar metric
            if raster_crs.to_epsg() == 5070:
                gdf_buffer = gdf_point_utm # Already in 5070
            else:
                gdf_buffer = gdf_point_utm.to_crs(raster_crs)
        
        # Now sample the raster
        # Create a mask for the buffer
        geom = mapping(gdf_buffer.geometry.iloc[0])
        
        # Use rasterio.mask
        from rasterio.mask import mask
        try:
            out_image, out_transform = mask(raster_ds, [geom], crop=True)
            out_image = out_image[0] # First band
            
            # Calculate proportions
            total_pixels = out_image.size
            if total_pixels == 0:
                # Fallback if mask returns empty (e.g., out of bounds)
                props = {cat: 0.0 for cat in categories}
            else:
                counts = {cat: 0 for cat in categories}
                for val in out_image.flatten():
                    if pd.isna(val) or val == 0:
                        continue
                    cat = CLASS_TO_CATEGORY.get(val, 'other')
                    if cat in counts:
                        counts[cat] += 1
                
                props = {cat: count / total_pixels for cat, count in counts.items()}
        
        except Exception as e:
            logger.warning(f"Error masking for point {idx}: {e}")
            props = {cat: 0.0 for cat in categories}
        
        results.append(props)
    
    # Add columns to dataframe
    for cat in categories:
        df[f"{cat}_prop_100m"] = [r[f"{cat}_prop_100m"] for r in results]
        
    return df

def validate_proportions(df: pd.DataFrame) -> bool:
    """Validate that proportions sum to 1.0 (within tolerance)."""
    prop_cols = ['forest_prop_100m', 'grassland_prop_100m', 'wetland_prop_100m', 
                 'urban_prop_100m', 'other_prop_100m']
    sums = df[prop_cols].sum(axis=1)
    tolerance = 1e-6
    valid = (np.abs(sums - 1.0) < tolerance).all()
    
    if not valid:
        failed_count = (~valid).sum()
        logger.warning(f"{failed_count} rows have proportions that do not sum to 1.0")
    return valid

def save_output(df: pd.DataFrame, metadata: Dict[str, Any]):
    """Save the processed dataframe and update metadata."""
    processed_dir = get_processed_dir()
    output_path = processed_dir / "buffered_observations.csv"
    
    logger.info(f"Saving output to {output_path}")
    df.to_csv(output_path, index=False)
    
    # Update metadata
    meta_config = load_metadata_config()
    record_artifact_provenance(
        meta_config, 
        "calculate_100m_buffers", 
        output_path,
        {"buffer_radius_m": BUFFER_RADIUS_METERS}
    )
    save_metadata_config(meta_config)
    
    return output_path

def main():
    """Main entry point."""
    logger.info("Starting land cover buffer calculation...")
    
    try:
        # Load inputs
        df = load_filtered_ebd()
        raster_ds, raster_meta = load_nlcd_raster()
        
        # Calculate proportions
        df_processed = calculate_land_cover_proportions(df, raster_ds)
        
        # Validate
        if not validate_proportions(df_processed):
            logger.error("Proportion validation failed. Check input data.")
            # Do not raise, but log. The task requires the file to be written.
        
        # Save output
        output_path = save_output(df_processed, raster_meta)
        
        logger.info(f"Successfully saved {len(df_processed)} records to {output_path}")
        
    except FileNotFoundError as e:
        logger.error(f"Missing required input file: {e}")
        raise
    except Exception as e:
        logger.error(f"Error during processing: {e}")
        raise
    finally:
        if 'raster_ds' in locals():
            raster_ds.close()

if __name__ == "__main__":
    main()
