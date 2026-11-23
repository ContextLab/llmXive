import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional, Generator
from logger import get_logger, get_project_root
import geopandas as gpd
from shapely.geometry import Point
import json

# Initialize logger
logger = get_logger(__name__)

def load_synthetic_data_chunked(data_dir: Optional[Path] = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load synthetic noise and covariate data from disk in chunks.
    
    Args:
        data_dir: Directory containing synthetic data files. Defaults to data/raw.
        
    Returns:
        Tuple of (noise_df, covariate_df) DataFrames.
    """
    if data_dir is None:
        data_dir = get_project_root() / "data" / "raw"
    
    logger.info(f"Loading synthetic data from {data_dir}")
    
    noise_files = list(data_dir.glob("noise_*.csv"))
    covariate_files = list(data_dir.glob("covariates_*.csv"))
    
    if not noise_files:
        raise FileNotFoundError(f"No noise data files found in {data_dir}")
    if not covariate_files:
        raise FileNotFoundError(f"No covariate data files found in {data_dir}")
    
    # Load noise data
    noise_dfs = []
    for file in sorted(noise_files):
        logger.info(f"Loading noise chunk: {file}")
        chunk = pd.read_csv(file)
        noise_dfs.append(chunk)
    
    noise_df = pd.concat(noise_dfs, ignore_index=True)
    
    # Load covariate data
    covariate_dfs = []
    for file in sorted(covariate_files):
        logger.info(f"Loading covariate chunk: {file}")
        chunk = pd.read_csv(file)
        covariate_dfs.append(chunk)
    
    covariate_df = pd.concat(covariate_dfs, ignore_index=True)
    
    logger.info(f"Loaded {len(noise_df)} noise records and {len(covariate_df)} covariate records")
    return noise_df, covariate_df

def harmonize_spatial_data(noise_df: pd.DataFrame, covariate_df: pd.DataFrame) -> gpd.GeoDataFrame:
    """
    Merge noise and covariate data into a unified spatial grid.
    
    Args:
        noise_df: DataFrame with noise measurements and grid_id, date.
        covariate_df: DataFrame with covariate data and grid_id.
        
    Returns:
        GeoDataFrame with merged data and geometry.
    """
    logger.info("Starting spatial harmonization.")
    
    # Ensure grid_id types match
    noise_df['grid_id'] = noise_df['grid_id'].astype(int)
    covariate_df['grid_id'] = covariate_df['grid_id'].astype(int)
    
    # Merge noise and covariates
    merged_df = noise_df.merge(covariate_df, on='grid_id', how='left')
    
    # Generate geometry for each grid_id (200m grid cells)
    # Assuming grid_id corresponds to a regular grid
    def generate_geometry(grid_id: int) -> Point:
        """Generate a point geometry based on grid_id."""
        # Simple deterministic mapping: grid_id -> coordinates
        # In a real scenario, this would use actual grid definitions
        x = (grid_id % 1000) * 200  # 200m spacing
        y = (grid_id // 1000) * 200
        return Point(x, y)
    
    # Create GeoDataFrame
    geometry = [generate_geometry(gid) for gid in merged_df['grid_id']]
    gdf = gpd.GeoDataFrame(merged_df, geometry=geometry, crs="EPSG:4326")
    
    # Log warnings for missing covariates
    missing_covariates = gdf['traffic_volume'].isna().sum()
    if missing_covariates > 0:
        logger.warning(f"Found {missing_covariates} rows with missing covariates. These will be excluded in preprocessing.")
    
    logger.info(f"Spatial harmonization complete. Output rows: {len(gdf)}")
    return gdf

def main():
    """Main entry point for data ingestion."""
    logger.info("Starting data ingestion pipeline.")
    
    try:
        # Load data
        noise_df, covariate_df = load_synthetic_data_chunked()
        
        # Harmonize
        harmonized_gdf = harmonize_spatial_data(noise_df, covariate_df)
        
        # Save output
        output_path = get_project_root() / "data" / "processed" / "harmonized.parquet"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        harmonized_gdf.to_parquet(output_path, index=False)
        
        logger.info(f"Harmonized data saved to {output_path}")
        
    except Exception as e:
        logger.error(f"Data ingestion failed: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()