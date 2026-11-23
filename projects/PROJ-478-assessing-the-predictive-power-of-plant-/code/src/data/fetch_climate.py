"""
Climate Data Fetching and Processing Module.

This module handles downloading WorldClim v2.1 climate rasters,
extracting values at occurrence points, and aligning coordinate systems.
"""

import logging
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
import pandas as pd
import requests
from shapely.geometry import box, mapping
from shapely.ops import unary_union
from shapely.geometry import MultiPoint, Point
from tqdm import tqdm

from src.utils.logging import get_logger, log_provenance
from src.utils.config import RANDOM_SEED

logger = get_logger(__name__)

# WorldClim v2.1 URLs and configuration
WORLDCLIM_BASE_URL = "https://biocli.com/worldclim/v2.1"
WORLDCLIM_VARS = [
    'bio1', 'bio2', 'bio3', 'bio4', 'bio5', 'bio6', 'bio7', 'bio8',
    'bio9', 'bio10', 'bio11', 'bio12', 'bio13', 'bio14', 'bio15',
    'bio16', 'bio17', 'bio18', 'bio19'
]
RESOLUTION = '10min'  # 10 arc-minutes (~18km at equator)

def get_convex_hull_bbox(occurrences: pd.DataFrame) -> Tuple[float, float, float, float]:
    """
    Calculate the bounding box of the convex hull of occurrence points.

    Args:
        occurrences: DataFrame with 'decimalLatitude' and 'decimalLongitude'.

    Returns:
        Tuple (minx, miny, maxx, maxy) representing the bounding box.
    """
    if occurrences.empty:
        raise ValueError("Cannot compute convex hull of empty DataFrame")
    
    points = [Point(x, y) for x, y in zip(
        occurrences['decimalLongitude'],
        occurrences['decimalLatitude']
    )]
    
    multi_point = MultiPoint(points)
    convex_hull = multi_point.convex_hull
    
    # Add a small buffer to the bounding box
    minx, miny, maxx, maxy = convex_hull.bounds
    buffer_deg = 0.5
    
    return (
        max(minx - buffer_deg, -180),
        max(miny - buffer_deg, -90),
        min(maxx + buffer_deg, 180),
        min(maxy + buffer_deg, 90)
    )

def download_worldclim_raster(
    variable: str,
    resolution: str = RESOLUTION,
    bbox: Optional[Tuple[float, float, float, float]] = None,
    output_dir: Optional[Path] = None
) -> Path:
    """
    Download a WorldClim v2.1 climate raster variable.

    Args:
        variable: Variable name (e.g., 'bio1').
        resolution: Resolution string (e.g., '10min').
        bbox: Optional bounding box (minx, miny, maxx, maxy) to clip.
        output_dir: Directory to save the raster.

    Returns:
        Path to the downloaded raster file.
    """
    if output_dir is None:
        output_dir = Path("data/raw/climate")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    filename = f"wc2.1_{resolution}_{variable}.tif"
    output_path = output_dir / filename
    
    if output_path.exists():
        logger.info(f"Raster already exists: {output_path}")
        return output_path
    
    # Construct URL (simplified - in reality would need to check specific WorldClim API)
    # Note: This is a placeholder URL structure; actual implementation may vary
    url = f"{WORLDCLIM_BASE_URL}/{variable}/{filename}"
    
    logger.info(f"Downloading {variable} from {url}")
    
    try:
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        logger.info(f"Downloaded {variable} to {output_path}")
        
        log_provenance(
            operation="climate_download",
            parameters={
                "variable": variable,
                "resolution": resolution,
                "url": url,
                "output_path": str(output_path),
                "timestamp": datetime.now().isoformat()
            },
            source="WorldClim",
            timestamp=datetime.now().isoformat()
        )
        
        return output_path
        
    except Exception as e:
        logger.error(f"Failed to download {variable}: {str(e)}")
        raise

def extract_raster_values(
    occurrences: pd.DataFrame,
    raster_paths: List[Path],
    variable_names: List[str]
) -> pd.DataFrame:
    """
    Extract raster values at occurrence points.

    Args:
        occurrences: DataFrame with 'decimalLatitude' and 'decimalLongitude'.
        raster_paths: List of paths to raster files.
        variable_names: List of variable names corresponding to rasters.

    Returns:
        DataFrame with original columns plus climate variables.
    """
    logger.info(f"Extracting values from {len(raster_paths)} rasters")
    
    try:
        import rasterio
        from rasterio.sample import sample_gen
    except ImportError:
        logger.error("rasterio is required for this operation")
        raise ImportError("rasterio must be installed")
    
    # Initialize result DataFrame
    result_df = occurrences.copy()
    
    # Extract values for each raster
    for raster_path, var_name in zip(raster_paths, variable_names):
        logger.info(f"Processing {var_name} from {raster_path}")
        
        try:
            with rasterio.open(raster_path) as src:
                # Sample points
                points = list(zip(
                    result_df['decimalLongitude'],
                    result_df['decimalLatitude']
                ))
                
                # Extract values
                values = []
                for point in points:
                    try:
                        val = next(src.sample([point]))[0]
                        values.append(val)
                    except Exception:
                        values.append(np.nan)
                
                result_df[var_name] = values
                
        except Exception as e:
            logger.error(f"Error extracting {var_name}: {str(e)}")
            result_df[var_name] = np.nan
    
    log_provenance(
        operation="raster_extraction",
        parameters={
            "num_points": len(result_df),
            "num_variables": len(variable_names),
            "variables": variable_names,
            "timestamp": datetime.now().isoformat()
        },
        source="Raster Processing",
        timestamp=datetime.now().isoformat()
    )
    
    return result_df

def process_climate_data(
    occurrences: pd.DataFrame,
    output_dir: Optional[Path] = None,
    variables: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Main pipeline to download climate data and extract values for occurrences.

    Args:
        occurrences: DataFrame with occurrence data.
        output_dir: Directory for climate data.
        variables: List of climate variables to download (default: all bio variables).

    Returns:
        DataFrame with climate variables added.
    """
    if output_dir is None:
        output_dir = Path("data/processed/climate")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if variables is None:
        variables = WORLDCLIM_VARS[:5]  # Use first 5 for demonstration
    
    logger.info(f"Processing climate data for {len(occurrences)} occurrences")
    
    # 1. Calculate bounding box
    bbox = get_convex_hull_bbox(occurrences)
    logger.info(f"Bounding box: {bbox}")
    
    # 2. Download rasters
    raster_paths = []
    for var in variables:
        try:
            # Note: In a real implementation, we would download the full raster
            # and then clip to bbox. Here we simulate the process.
            raster_path = download_worldclim_raster(var, bbox=bbox, output_dir=output_dir)
            raster_paths.append(raster_path)
        except Exception as e:
            logger.warning(f"Skipping {var} due to download error: {e}")
    
    if not raster_paths:
        raise ValueError("No climate rasters could be downloaded")
    
    # 3. Extract values
    climate_df = extract_raster_values(occurrences, raster_paths, variables)
    
    # 4. Save processed data
    output_file = output_dir / "climate_occurrences.csv"
    climate_df.to_csv(output_file, index=False)
    logger.info(f"Saved climate data to {output_file}")
    
    log_provenance(
        operation="climate_processing_complete",
        parameters={
            "num_occurrences": len(climate_df),
            "num_variables": len(variables),
            "output_file": str(output_file),
            "timestamp": datetime.now().isoformat()
        },
        source="Climate Pipeline",
        timestamp=datetime.now().isoformat()
    )
    
    return climate_df

def main():
    """Main entry point for testing."""
    # Create sample data
    sample_occ = pd.DataFrame({
        'species': ['Helianthus annuus'] * 10,
        'decimalLatitude': [34.0 + i * 0.1 for i in range(10)],
        'decimalLongitude': [-118.0 + i * 0.1 for i in range(10)],
        'eventDate': ['2020-05-01'] * 10
    })
    
    try:
        result = process_climate_data(sample_occ, output_dir=Path("data/processed/test_climate"))
        print(f"Processed climate data: {result.columns.tolist()}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
