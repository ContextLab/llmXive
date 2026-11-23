import os
import sys
import logging
import json
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

import pandas as pd
import numpy as np

from config import get_path_env_override
from setup_logging import get_data_quality_logger, get_exclusion_logger
from loaders import load_parquet_as_df

# Configuration imports
from config import (
    TEMPERATURE_MIN,
    TEMPERATURE_MAX,
    RESPONSE_TIME_MIN_MS,
    RESPONSE_TIME_MAX_MS,
    DISTANCE_THRESHOLD_KM
)

def setup_logging_custom():
    """Setup logging for the ingestion module."""
    logger = logging.getLogger("ingestion")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

def ensure_directories():
    """Ensure all required directories exist."""
    dirs = [
        "data/processed",
        "results/logs",
        "results/figures",
        "data/raw"
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)

def ensure_exclusion_log_exists():
    """Ensure the exclusion log file exists."""
    log_path = Path("results/logs/exclusion_log.csv")
    if not log_path.exists():
        log_path.touch()

def load_moral_machine_data(input_path: str) -> pd.DataFrame:
    """Load the Moral Machine dataset."""
    logger = setup_logging_custom()
    logger.info(f"Loading Moral Machine data from {input_path}")
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    try:
        # Handle both .csv and .csv.gz
        if input_path.endswith('.gz'):
            df = pd.read_csv(input_path, compression='gzip')
        else:
            df = pd.read_csv(input_path)
        
        logger.info(f"Loaded {len(df)} records from {input_path}")
        return df
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        raise

def apply_column_mapping(df: pd.DataFrame) -> pd.DataFrame:
    """Apply standard column mapping."""
    mapping = {
        'lat': 'latitude',
        'lon': 'longitude',
        'response_time_ms': 'response_time'
    }
    # Only rename if columns exist
    for old, new in mapping.items():
        if old in df.columns:
            df = df.rename(columns={old: new})
    return df

def filter_missing_location(df: pd.DataFrame, exclusion_logger: logging.Logger) -> Tuple[pd.DataFrame, int]:
    """Filter out records with missing latitude/longitude."""
    initial_count = len(df)
    mask = df['latitude'].notna() & df['longitude'].notna()
    filtered_df = df[mask]
    excluded_count = initial_count - len(filtered_df)
    
    if excluded_count > 0:
        exclusion_logger.info(f"Excluded {excluded_count} records due to missing location")
        # Log excluded records
        excluded_df = df[~mask].copy()
        excluded_df['exclusion_reason'] = 'missing location'
        excluded_df.to_csv('results/logs/exclusion_log.csv', mode='a', header=False, index=False)
    
    return filtered_df, excluded_count

def filter_invalid_response_time(df: pd.DataFrame, exclusion_logger: logging.Logger) -> Tuple[pd.DataFrame, int]:
    """Filter out records with invalid response times."""
    initial_count = len(df)
    mask = (df['response_time'] >= RESPONSE_TIME_MIN_MS) & (df['response_time'] <= RESPONSE_TIME_MAX_MS)
    filtered_df = df[mask]
    excluded_count = initial_count - len(filtered_df)
    
    if excluded_count > 0:
        exclusion_logger.info(f"Excluded {excluded_count} records due to invalid response time")
        # Log excluded records
        excluded_df = df[~mask].copy()
        excluded_df['exclusion_reason'] = 'invalid response time'
        excluded_df.to_csv('results/logs/exclusion_log.csv', mode='a', header=False, index=False)
    
    return filtered_df, excluded_count

def filter_temperature_range(df: pd.DataFrame, exclusion_logger: logging.Logger) -> Tuple[pd.DataFrame, int]:
    """
    Filter out records with temperature_celsius values outside the configured range.
    This filter MUST be applied AFTER interpolation but BEFORE the final join.
    
    If the observed temperature range in the dataset exceeds the configured thresholds,
    the pipeline MUST ABORT.
    """
    initial_count = len(df)
    
    # Check if temperature column exists
    if 'temperature_celsius' not in df.columns:
        logging.getLogger("ingestion").warning("temperature_celsius column not found. Skipping temperature filter.")
        return df, 0
    
    # Check for extreme values that exceed thresholds (Abort Condition)
    min_observed = df['temperature_celsius'].min()
    max_observed = df['temperature_celsius'].max()
    
    logger = setup_logging_custom()
    
    if min_observed < TEMPERATURE_MIN or max_observed > TEMPERATURE_MAX:
        logger.error(f"ABORT: Observed temperature range [{min_observed}, {max_observed}] exceeds configured thresholds [{TEMPERATURE_MIN}, {TEMPERATURE_MAX}]")
        raise ValueError(
            f"Pipeline Aborted: Temperature range violation. "
            f"Observed: [{min_observed}, {max_observed}], Allowed: [{TEMPERATURE_MIN}, {TEMPERATURE_MAX}]"
        )
    
    # Apply filter
    mask = (df['temperature_celsius'] >= TEMPERATURE_MIN) & (df['temperature_celsius'] <= TEMPERATURE_MAX)
    filtered_df = df[mask]
    excluded_count = initial_count - len(filtered_df)
    
    if excluded_count > 0:
        exclusion_logger.info(f"Excluded {excluded_count} records due to temperature out of range")
        # Log excluded records
        excluded_df = df[~mask].copy()
        excluded_df['exclusion_reason'] = 'temperature out of range'
        excluded_df.to_csv('results/logs/exclusion_log.csv', mode='a', header=False, index=False)
    
    return filtered_df, excluded_count

def capture_pre_filter_count(df: pd.DataFrame, count_name: str, counts_log: Dict[str, Any]) -> Dict[str, Any]:
    """Capture the current record count."""
    counts_log[count_name] = len(df)
    return counts_log

def save_filtered_data(df: pd.DataFrame, output_path: str):
    """Save the filtered dataframe to parquet."""
    df.to_parquet(output_path, index=False)

def log_counts_to_file(counts: Dict[str, Any]):
    """Log counts to results/logs/counts.json."""
    log_path = Path("results/logs/counts.json")
    if log_path.exists():
        with open(log_path, 'r') as f:
            existing_counts = json.load(f)
        existing_counts.update(counts)
        counts = existing_counts
    
    with open(log_path, 'w') as f:
        json.dump(counts, f, indent=2)

def find_nearest_era5_grid(lat: float, lon: float, era5_grid_points: pd.DataFrame) -> Tuple[float, float, float]:
    """
    Find the nearest ERA5 grid point to a given lat/lon.
    Returns (grid_id, distance_km, temperature).
    Simplified for this implementation.
    """
    # This is a placeholder for the actual geospatial logic
    # In a real implementation, this would use geopy or haversine distance
    # to find the nearest grid point from the ERA5 dataset
    return (0.0, 0.0, 0.0)

def process_geospatial_matching(df: pd.DataFrame, era5_data: pd.DataFrame) -> pd.DataFrame:
    """Process geospatial matching between Moral Machine and ERA5 data."""
    # Placeholder for actual geospatial matching logic
    # This would involve finding the nearest grid point for each record
    return df

def main():
    """Main entry point for the ingestion script with temperature validation."""
    logger = setup_logging_custom()
    exclusion_logger = get_exclusion_logger()
    quality_logger = get_data_quality_logger()
    
    ensure_directories()
    ensure_exclusion_log_exists()
    
    # Parse arguments or use defaults
    input_path = "data/raw/moral_machine.csv.gz"
    temp_path = "data/raw/era5_data" # Placeholder for temp data path
    output_path = "data/processed/merged_dataset.parquet"
    
    # Check for command line arguments
    if len(sys.argv) > 1:
        input_path = sys.argv[1]
    if len(sys.argv) > 3:
        output_path = sys.argv[3]
    
    logger.info(f"Starting ingestion pipeline")
    logger.info(f"Input: {input_path}")
    logger.info(f"Output: {output_path}")
    
    counts = {}
    
    try:
        # 1. Load Data
        df = load_moral_machine_data(input_path)
        df = apply_column_mapping(df)
        
        # 2. Count Total Valid Location (Pre-filter)
        counts = capture_pre_filter_count(df, 'count_total_original_valid_location', counts)
        
        # 3. Filter Missing Location (Hard Filter 1)
        df, _ = filter_missing_location(df, exclusion_logger)
        
        # 4. Filter Invalid Response Time (Hard Filter 2)
        df, _ = filter_invalid_response_time(df, exclusion_logger)
        
        # 5. Geospatial Matching (T019)
        # Note: In a full pipeline, we would load ERA5 data here and match
        # For this task, we assume the data has been matched and contains 'temperature_celsius'
        # If the file is a merged dataset from previous steps, we load it
        
        # Check if we are processing a pre-merged file (from T019c-interpolate)
        # or if we need to perform the join here.
        # Based on T017b description: "Prerequisite: This filter MUST be applied AFTER T019c-interpolate"
        
        # If the input is the raw moral machine data, we cannot filter temperature yet.
        # We assume the input for this specific task execution is the intermediate
        # dataset that already has temperature joined (from T019c).
        # If the input file does not have temperature, we log a warning and skip.
        
        if 'temperature_celsius' in df.columns:
            logger.info("Temperature column found. Applying temperature range filter (T017b).")
            df, temp_excluded = filter_temperature_range(df, exclusion_logger)
            counts['temperature_excluded_count'] = temp_excluded
        else:
            logger.warning("No temperature_celsius column found in input. Skipping temperature filter.")
            logger.warning("Ensure T019c-interpolate has run and joined temperature data before this step.")
        
        # 6. Save Output
        save_filtered_data(df, output_path)
        
        # 7. Log Counts
        counts['count_filtered_for_analysis'] = len(df)
        log_counts_to_file(counts)
        
        quality_logger.info(f"Ingestion pipeline completed successfully. Final count: {len(df)}")
        logger.info(f"Pipeline completed. Output saved to {output_path}")
        
    except ValueError as e:
        if "Pipeline Aborted" in str(e):
            logger.critical(str(e))
            quality_logger.critical(str(e))
            sys.exit(1)
        raise
    except Exception as e:
        logger.error(f"Ingestion pipeline failed: {e}")
        quality_logger.error(f"Ingestion pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()