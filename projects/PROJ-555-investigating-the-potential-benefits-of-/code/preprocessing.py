import os
import logging
import numpy as np
import pandas as pd
import xarray as xr
import rasterio
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import json
from datetime import datetime

from config import ensure_directories
from logging_config import get_logger

logger = get_logger(__name__)

def calculate_ndvi_from_raster(raster_path: str, red_band: int, nir_band: int) -> Optional[np.ndarray]:
    """
    Calculate NDVI from a single Landsat raster file.
    NDVI = (NIR - Red) / (NIR + Red)
    """
    try:
        with rasterio.open(raster_path) as src:
            red = src.read(red_band).astype(float)
            nir = src.read(nir_band).astype(float)
            
            # Mask no-data values
            mask = (red != src.nodata) & (nir != src.nodata)
            
            ndvi = np.zeros_like(red, dtype=float)
            np.divide(nir - red, nir + red, out=ndvi, where=(nir + red) != 0)
            
            ndvi[~mask] = np.nan
            return ndvi
    except Exception as e:
        logger.error(f"Failed to calculate NDVI from {raster_path}: {e}")
        return None

def calculate_ndvi_from_scene_id(scene_id: str, data_dir: str) -> Optional[np.ndarray]:
    """
    Calculate NDVI from a Landsat scene ID by constructing the expected file path.
    Assumes standard Landsat Level-2 file naming convention.
    """
    # Example: LC08_L2SP_044034_20200101_20200101_02_T1
    # We assume the file is in data_dir with .tif extension
    # This is a simplified path; actual implementation might need to search or use metadata
    file_path = os.path.join(data_dir, f"{scene_id}_SR_B4.tif") # Red band
    if not os.path.exists(file_path):
        # Try common alternative naming
        file_path = os.path.join(data_dir, f"{scene_id}_B4.tif")
    
    if not os.path.exists(file_path):
        logger.warning(f"Could not find raster for {scene_id}")
        return None
        
    # Landsat 8/9: Band 4 = Red, Band 5 = NIR
    return calculate_ndvi_from_raster(file_path, red_band=1, nir_band=2)

def batch_process_ndvi(scene_ids: List[str], data_dir: str, output_path: str) -> pd.DataFrame:
    """
    Process multiple scenes and return a DataFrame of NDVI time series.
    """
    ensure_directories([output_path])
    results = []
    
    for scene_id in scene_ids:
        ndvi = calculate_ndvi_from_scene_id(scene_id, data_dir)
        if ndvi is not None:
            # Calculate mean NDVI for the scene (simplified; real implementation would use site geometry)
            mean_ndvi = np.nanmean(ndvi)
            results.append({
                'scene_id': scene_id,
                'ndvi_mean': mean_ndvi,
                'timestamp': datetime.now() # In real impl, extract from scene_id or metadata
            })
    
    df = pd.DataFrame(results)
    df.to_parquet(output_path, index=False)
    logger.info(f"Batch processed {len(df)} scenes to {output_path}")
    return df

def pair_sites_and_filter(
    ndvi_df: pd.DataFrame, 
    site_metadata: pd.DataFrame, 
    output_ndvi_path: str, 
    output_meta_path: str
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Pair sites based on biome and initial NDVI drop, filter out gaps > 50%.
    """
    # This is a placeholder for the complex pairing logic described in T017
    # In a real implementation, this would join on biome, calculate initial drops,
    # and filter based on data completeness.
    
    ensure_directories([output_ndvi_path, output_meta_path])
    
    # For now, just pass through the data (T017 implementation would go here)
    ndvi_df.to_parquet(output_ndvi_path, index=False)
    site_metadata.to_csv(output_meta_path, index=False)
    
    return ndvi_df, site_metadata

def fetch_and_validate_ecotourism_data(
    input_csv: str, 
    output_csv: str, 
    metadata_json: str
) -> pd.DataFrame:
    """
    Fetch ecotourism data, handle missing revenue/visitor logic, and validate.
    
    Logic:
    1. Load data from input_csv.
    2. If 'revenue' is null, use 'visitor_count'.
    3. If both 'revenue' and 'visitor_count' are null, exclude the row.
    4. Log substitutions in metadata_json.
    5. Output cleaned data to output_csv.
    """
    ensure_directories([output_csv, metadata_json])
    
    logger.info(f"Loading ecotourism data from {input_csv}")
    if not os.path.exists(input_csv):
        raise FileNotFoundError(f"Input file not found: {input_csv}")
    
    df = pd.read_csv(input_csv)
    
    # Ensure columns exist
    required_cols = ['site_id']
    if 'revenue' not in df.columns:
        df['revenue'] = np.nan
    if 'visitor_count' not in df.columns:
        df['visitor_count'] = np.nan
        
    substitution_log = []
    excluded_count = 0
    
    # Apply logic: if revenue null, use visitor_count
    # We create a 'metric_value' column for the final output representing the economic proxy
    df['metric_value'] = df['revenue']
    df['metric_source'] = 'revenue'
    
    # Identify rows where revenue is null
    revenue_null_mask = df['revenue'].isna()
    
    # For those rows, try to use visitor_count
    visitor_count_available = ~df['visitor_count'].isna()
    
    # Rows where we can substitute
    substitute_mask = revenue_null_mask & visitor_count_available
    
    # Rows where both are null (exclude)
    exclude_mask = revenue_null_mask & ~visitor_count_available
    
    # Log substitutions
    if substitute_mask.any():
        sites_substituted = df.loc[substitute_mask, 'site_id'].tolist()
        substitution_log.extend([
            {
                "site_id": site,
                "action": "revenue_substituted_with_visitor_count",
                "timestamp": datetime.now().isoformat()
            }
            for site in sites_substituted
        ])
        df.loc[substitute_mask, 'metric_value'] = df.loc[substitute_mask, 'visitor_count']
        df.loc[substitute_mask, 'metric_source'] = 'visitor_count'
    
    # Log exclusions
    if exclude_mask.any():
        sites_excluded = df.loc[exclude_mask, 'site_id'].tolist()
        substitution_log.extend([
            {
                "site_id": site,
                "action": "excluded_missing_revenue_and_visitor_count",
                "timestamp": datetime.now().isoformat()
            }
            for site in sites_excluded
        ])
        excluded_count = len(sites_excluded)
    
    # Filter out excluded rows
    df_clean = df[~exclude_mask].copy()
    
    # Save cleaned data
    df_clean.to_csv(output_csv, index=False)
    
    # Save metadata
    metadata = {
        "source_file": input_csv,
        "output_file": output_csv,
        "substitutions": substitution_log,
        "total_rows_input": len(df),
        "total_rows_output": len(df_clean),
        "rows_excluded": excluded_count,
        "generated_at": datetime.now().isoformat()
    }
    
    with open(metadata_json, 'w') as f:
        json.dump(metadata, f, indent=2)
        
    logger.info(f"Processed {len(df)} rows, excluded {excluded_count}, saved to {output_csv}")
    return df_clean

def main():
    """
    Entry point for preprocessing pipeline.
    """
    # Example execution flow for T029 (assuming T018 has generated the input file)
    # In a real pipeline, paths would come from config or command line args
    input_path = "data/ecotourism/revenue_data.csv"
    output_path = "data/processed/ecotourism_data.csv"
    meta_path = "data/ecotourism/metadata.json"
    
    # Ensure directories exist
    ensure_directories([output_path, meta_path])
    
    if os.path.exists(input_path):
        try:
            fetch_and_validate_ecotourism_data(input_path, output_path, meta_path)
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            raise
    else:
        logger.warning(f"Input file {input_path} not found. Skipping ecotourism data processing.")
        # Create empty output and metadata to prevent downstream errors
        pd.DataFrame(columns=['site_id', 'metric_value', 'metric_source']).to_csv(output_path, index=False)
        with open(meta_path, 'w') as f:
            json.dump({"status": "skipped", "reason": "input_file_not_found"}, f)

if __name__ == "__main__":
    main()