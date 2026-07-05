import os
import json
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
import numpy as np
import requests

from config import DATA_RAW_DIR, DATA_PROCESSED_DIR, STATE_DIR, FARS_URL, NOAA_URL
from logging_config import log_data_drop_counts, log_processing_step
from schema_validation import validate_raw_fars, validate_raw_noaa, validate_merged_dataset
from utils import optimize_memory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def download_file(url: str, dest_path: Path) -> Tuple[bool, str]:
    """
    Download a file from a URL and compute its SHA-256 checksum.
    
    Args:
        url: The URL to download from.
        dest_path: The local path to save the file to.
        
    Returns:
        Tuple of (success: bool, checksum: str)
    """
    try:
        logger.info(f"Downloading {url} to {dest_path}")
        response = requests.get(url, stream=True, timeout=300)
        response.raise_for_status()
        
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        sha256_hash = hashlib.sha256()
        with open(dest_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                sha256_hash.update(chunk)
        
        checksum = sha256_hash.hexdigest()
        logger.info(f"Downloaded {dest_path.name}, SHA-256: {checksum}")
        return True, checksum
    except Exception as e:
        logger.error(f"Failed to download {url}: {e}")
        return False, ""

def validate_and_load_fars(path: Path) -> Optional[pd.DataFrame]:
    """
    Validate and load the FARS dataset.
    
    Args:
        path: Path to the FARS CSV file.
        
    Returns:
        DataFrame if validation passes, None otherwise.
    """
    try:
        logger.info(f"Loading and validating FARS data from {path}")
        df = pd.read_csv(path)
        
        if not validate_raw_fars(df):
            logger.error("FARS data validation failed")
            return None
        
        df = optimize_memory(df)
        logger.info(f"FARS data loaded: {len(df)} rows, {len(df.columns)} columns")
        return df
    except Exception as e:
        logger.error(f"Failed to load FARS data: {e}")
        return None

def validate_and_load_noaa(path: Path) -> Optional[pd.DataFrame]:
    """
    Validate and load the NOAA dataset.
    
    Args:
        path: Path to the NOAA CSV file.
        
    Returns:
        DataFrame if validation passes, None otherwise.
    """
    try:
        logger.info(f"Loading and validating NOAA data from {path}")
        df = pd.read_csv(path)
        
        if not validate_raw_noaa(df):
            logger.error("NOAA data validation failed")
            return None
        
        df = optimize_memory(df)
        logger.info(f"NOAA data loaded: {len(df)} rows, {len(df.columns)} columns")
        return df
    except Exception as e:
        logger.error(f"Failed to load NOAA data: {e}")
        return None

def merge_datasets(fars_df: pd.DataFrame, noaa_df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """
    Merge FARS and NOAA datasets on timestamp and location.
    
    Args:
        fars_df: FARS DataFrame.
        noaa_df: NOAA DataFrame.
        
    Returns:
        Tuple of (merged DataFrame, drop_counts dict)
    """
    logger.info("Merging FARS and NOAA datasets")
    
    # Ensure timestamp columns are datetime
    fars_df['ACCIDENT_DATE'] = pd.to_datetime(fars_df['ACCIDENT_DATE'], errors='coerce')
    noaa_df['DATE'] = pd.to_datetime(noaa_df['DATE'], errors='coerce')
    
    # Merge on date and location (LAT, LON)
    # We'll use a tolerance for location matching if needed
    merged = pd.merge(
        fars_df,
        noaa_df,
        left_on=['ACCIDENT_DATE', 'LATITUDE', 'LONGITUDE'],
        right_on=['DATE', 'LAT', 'LON'],
        how='inner'
    )
    
    # Count dropped rows (structural only: missing ID, Lat/Lon)
    fars_total = len(fars_df)
    noaa_total = len(noaa_df)
    merged_total = len(merged)
    
    dropped_fars = fars_total - merged_total
    dropped_noaa = noaa_total - merged_total
    
    drop_counts = {
        'fars_dropped': dropped_fars,
        'noaa_dropped': dropped_noaa,
        'total_merged': merged_total
    }
    
    logger.info(f"Merged dataset: {merged_total} rows (Dropped {dropped_fars} FARS, {dropped_noaa} NOAA)")
    
    return merged, drop_counts

def apply_winsorization(df: pd.DataFrame, columns: List[str], lower_percentile: float = 1, upper_percentile: float = 99) -> pd.DataFrame:
    """
    Apply winsorization to specified columns to handle extreme outliers.
    
    Args:
        df: Input DataFrame.
        columns: List of column names to winsorize.
        lower_percentile: Lower percentile for clipping.
        upper_percentile: Upper percentile for clipping.
        
    Returns:
        DataFrame with winsorized columns.
    """
    df_winsorized = df.copy()
    
    for col in columns:
        if col in df_winsorized.columns:
            lower = df_winsorized[col].quantile(lower_percentile / 100)
            upper = df_winsorized[col].quantile(upper_percentile / 100)
            df_winsorized[col] = df_winsorized[col].clip(lower, upper)
            logger.info(f"Winsorized {col}: [{lower:.2f}, {upper:.2f}]")
    
    return df_winsorized

def run_ingestion_pipeline() -> Optional[pd.DataFrame]:
    """
    Run the full data ingestion pipeline: download, validate, merge, winsorize, and save.
    
    Returns:
        Merged DataFrame if successful, None otherwise.
    """
    log_processing_step("Starting data ingestion pipeline")
    
    # 1. Download data
    fars_path = DATA_RAW_DIR / "fars_data.csv"
    noaa_path = DATA_RAW_DIR / "noaa_data.csv"
    
    # Check if files exist (in a real scenario, we'd download them)
    if not fars_path.exists():
        logger.error(f"FARS data not found at {fars_path}. Please download first.")
        return None
    if not noaa_path.exists():
        logger.error(f"NOAA data not found at {noaa_path}. Please download first.")
        return None
    
    # 2. Validate and load
    fars_df = validate_and_load_fars(fars_path)
    noaa_df = validate_and_load_noaa(noaa_path)
    
    if fars_df is None or noaa_df is None:
        logger.error("Failed to load or validate one or more datasets")
        return None
    
    # 3. Merge datasets
    merged_df, drop_counts = merge_datasets(fars_df, noaa_df)
    
    if merged_df.empty:
        logger.error("Merged dataset is empty")
        return None
    
    # 4. Log dropped record counts (structural only)
    log_data_drop_counts(drop_counts)
    
    # 5. Apply winsorization to temperature and precipitation columns
    weather_columns = ['TEMP', 'PRCP']  # Adjust based on actual column names
    weather_columns = [col for col in weather_columns if col in merged_df.columns]
    
    if weather_columns:
        merged_df = apply_winsorization(merged_df, weather_columns)
        logger.info(f"Applied winsorization to {weather_columns}")
    
    # 6. Save interim merged dataset
    output_path = DATA_PROCESSED_DIR / "merged_data_interim.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    merged_df.to_csv(output_path, index=False)
    logger.info(f"Saved interim merged dataset to {output_path}")
    
    # 7. Verify output
    if output_path.exists() and output_path.stat().st_size > 0:
        logger.info(f"Verification: {output_path} exists and is non-empty ({output_path.stat().st_size} bytes)")
        log_processing_step("Data ingestion pipeline completed successfully")
        return merged_df
    else:
        logger.error(f"Verification failed: {output_path} does not exist or is empty")
        return None

if __name__ == "__main__":
    result = run_ingestion_pipeline()
    if result is not None:
        print(f"Pipeline completed successfully. Output saved to {DATA_PROCESSED_DIR / 'merged_data_interim.csv'}")
    else:
        print("Pipeline failed.")
        exit(1)