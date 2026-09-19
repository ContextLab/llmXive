"""
Ingestion module for T017: Load, Filter & Count.

This module implements the core data ingestion pipeline for User Story 1.
It loads the Moral Machine dataset, applies hard filters for location and
response time validity, and logs exclusion reasons.

Dependencies:
- T006: Pre-ingestion validation gate (ensures raw data exists)
- T010: Configuration (thresholds)
"""
import os
import sys
import logging
import json
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
import pandas as pd
import numpy as np

# Import configuration
from config import get_path_env_override

# Setup logging infrastructure
def setup_logging_custom(log_file: Optional[str] = None) -> logging.Logger:
    """Setup custom logger for ingestion tasks."""
    logger = logging.getLogger('ingestion')
    logger.setLevel(logging.DEBUG)
    
    if not logger.handlers:
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # File handler
        if log_file:
            fh = logging.FileHandler(log_file)
            fh.setLevel(logging.INFO)
            fh.setFormatter(formatter)
            logger.addHandler(fh)
        
        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    
    return logger

def ensure_directories(base_path: Path) -> None:
    """Ensure all required directories exist."""
    dirs = [
        base_path / 'data' / 'raw',
        base_path / 'data' / 'processed',
        base_path / 'results' / 'logs',
        base_path / 'results' / 'figures',
        base_path / 'results' / 'stats',
        base_path / 'state' / 'projects'
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def ensure_exclusion_log_exists(log_path: Path) -> None:
    """Ensure the exclusion log file exists and is initialized."""
    if not log_path.exists():
        log_path.parent.mkdir(parents=True, exist_ok=True)
        # Initialize with header
        with open(log_path, 'w') as f:
            f.write('record_id,exclusion_reason,original_data\n')

def load_moral_machine_data(csv_path: Path) -> pd.DataFrame:
    """
    Load the Moral Machine dataset from CSV.
    
    Args:
        csv_path: Path to the CSV file (can be gzipped)
        
    Returns:
        DataFrame with raw Moral Machine data
    """
    logger = logging.getLogger('ingestion')
    logger.info(f"Loading Moral Machine data from {csv_path}")
    
    if not csv_path.exists():
        raise FileNotFoundError(f"Moral Machine dataset not found at {csv_path}")
    
    try:
        # Handle gzipped files
        if str(csv_path).endswith('.gz'):
            df = pd.read_csv(csv_path, compression='gzip')
        else:
            df = pd.read_csv(csv_path)
        
        logger.info(f"Loaded {len(df)} records from {csv_path}")
        return df
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        raise

def apply_column_mapping(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply standard column name mappings.
    
    Maps:
    - lat -> latitude
    - lon -> longitude
    - response_time_ms -> response_time
    """
    logger = logging.getLogger('ingestion')
    mapping = {
        'lat': 'latitude',
        'lon': 'longitude',
        'response_time_ms': 'response_time'
    }
    
    # Only map columns that exist
    existing_cols = {k: v for k, v in mapping.items() if k in df.columns}
    if existing_cols:
        df = df.rename(columns=existing_cols)
        logger.info(f"Mapped columns: {existing_cols}")
    
    return df

def filter_missing_location(df: pd.DataFrame, exclusion_log: Path) -> Tuple[pd.DataFrame, int]:
    """
    Filter out records with missing latitude or longitude.
    
    Args:
        df: Input DataFrame
        exclusion_log: Path to exclusion log file
        
    Returns:
        Tuple of (filtered DataFrame, count of excluded records)
    """
    logger = logging.getLogger('ingestion')
    
    # Identify records with missing location
    missing_mask = df['latitude'].isna() | df['longitude'].isna()
    excluded_count = missing_mask.sum()
    
    if excluded_count > 0:
        logger.warning(f"Excluding {excluded_count} records with missing location data")
        
        # Log excluded records
        ensure_exclusion_log_exists(exclusion_log)
        excluded_records = df[missing_mask].copy()
        excluded_records['exclusion_reason'] = 'missing location'
        
        # Append to log
        with open(exclusion_log, 'a') as f:
            for _, row in excluded_records.iterrows():
                # Create a simple string representation
                record_data = ','.join(str(v) for v in row.values)
                f.write(f"{row.name},missing location,{record_data}\n")
        
        # Filter
        df = df[~missing_mask].copy()
    
    logger.info(f"Location filtering complete: {len(df)} records remain")
    return df, excluded_count

def filter_invalid_response_time(
    df: pd.DataFrame, 
    exclusion_log: Path,
    min_ms: int = 100,
    max_ms: int = 10000
) -> Tuple[pd.DataFrame, int]:
    """
    Filter out records with response times outside valid range.
    
    Args:
        df: Input DataFrame
        exclusion_log: Path to exclusion log file
        min_ms: Minimum valid response time in ms
        max_ms: Maximum valid response time in ms
        
    Returns:
        Tuple of (filtered DataFrame, count of excluded records)
    """
    logger = logging.getLogger('ingestion')
    
    # Check if response_time column exists
    if 'response_time' not in df.columns:
        logger.warning("response_time column not found, skipping response time filter")
        return df, 0
    
    # Identify invalid response times
    invalid_mask = (df['response_time'] < min_ms) | (df['response_time'] > max_ms)
    excluded_count = invalid_mask.sum()
    
    if excluded_count > 0:
        logger.warning(f"Excluding {excluded_count} records with invalid response times")
        
        # Log excluded records
        ensure_exclusion_log_exists(exclusion_log)
        excluded_records = df[invalid_mask].copy()
        excluded_records['exclusion_reason'] = 'invalid response time'
        
        # Append to log
        with open(exclusion_log, 'a') as f:
            for _, row in excluded_records.iterrows():
                record_data = ','.join(str(v) for v in row.values)
                f.write(f"{row.name},invalid response time,{record_data}\n")
        
        # Filter
        df = df[~invalid_mask].copy()
    
    logger.info(f"Response time filtering complete: {len(df)} records remain")
    return df, excluded_count

def capture_pre_filter_count(df: pd.DataFrame, counts_log: Path) -> None:
    """
    Capture the count of records with valid latitude/longitude BEFORE filtering.
    
    Args:
        df: DataFrame before location filtering
        counts_log: Path to counts JSON log file
    """
    logger = logging.getLogger('ingestion')
    
    # Count records with valid location
    valid_location_count = df['latitude'].notna() & df['longitude'].notna()
    count_valid_location = valid_location_count.sum()
    
    # Ensure log directory exists
    counts_log.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing counts or initialize
    if counts_log.exists():
        with open(counts_log, 'r') as f:
            counts = json.load(f)
    else:
        counts = {}
    
    # Update counts
    counts['count_total_original_valid_location'] = int(count_valid_location)
    
    # Save
    with open(counts_log, 'w') as f:
        json.dump(counts, f, indent=2)
    
    logger.info(f"Captured pre-filter count: {count_valid_location}")

def save_filtered_data(df: pd.DataFrame, output_path: Path) -> None:
    """
    Save filtered DataFrame to Parquet format.
    
    Args:
        df: Filtered DataFrame
        output_path: Output path for Parquet file
    """
    logger = logging.getLogger('ingestion')
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)
    
    logger.info(f"Saved filtered data to {output_path} ({len(df)} records)")

def log_counts_to_file(
    counts_log: Path,
    count_filtered: int,
    count_missing_location: int,
    count_invalid_response_time: int
) -> None:
    """
    Log all counts to the counts JSON file.
    
    Args:
        counts_log: Path to counts JSON log file
        count_filtered: Final count after all filters
        count_missing_location: Count excluded for missing location
        count_invalid_response_time: Count excluded for invalid response time
    """
    logger = logging.getLogger('ingestion')
    
    # Ensure log directory exists
    counts_log.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing counts or initialize
    if counts_log.exists():
        with open(counts_log, 'r') as f:
            counts = json.load(f)
    else:
        counts = {}
    
    # Update counts
    counts['count_filtered_for_analysis'] = count_filtered
    counts['count_excluded_missing_location'] = count_missing_location
    counts['count_excluded_invalid_response_time'] = count_invalid_response_time
    
    # Save
    with open(counts_log, 'w') as f:
        json.dump(counts, f, indent=2)
    
    logger.info(f"Logged counts: filtered={count_filtered}, missing_loc={count_missing_location}, invalid_rt={count_invalid_response_time}")

def main(
    input_path: Optional[str] = None,
    output_path: Optional[str] = None,
    exclusion_log_path: Optional[str] = None,
    counts_log_path: Optional[str] = None
) -> None:
    """
    Main ingestion pipeline for T017.
    
    Args:
        input_path: Path to input Moral Machine CSV
        output_path: Path to output Parquet file
        exclusion_log_path: Path to exclusion log CSV
        counts_log_path: Path to counts JSON log
    """
    # Setup paths
    base_path = Path(get_path_env_override('PROJECT_ROOT', '.'))
    
    if input_path is None:
        input_path = base_path / 'data' / 'raw' / 'moral_machine.csv.gz'
    else:
        input_path = Path(input_path)
    
    if output_path is None:
        output_path = base_path / 'data' / 'processed' / 'merged_dataset.parquet'
    else:
        output_path = Path(output_path)
    
    if exclusion_log_path is None:
        exclusion_log_path = base_path / 'results' / 'logs' / 'exclusion_log.csv'
    else:
        exclusion_log_path = Path(exclusion_log_path)
    
    if counts_log_path is None:
        counts_log_path = base_path / 'results' / 'logs' / 'counts.json'
    else:
        counts_log_path = Path(counts_log_path)
    
    # Setup logging
    log_file = base_path / 'results' / 'logs' / 'ingestion.log'
    logger = setup_logging_custom(str(log_file))
    
    logger.info("Starting T017: Load, Filter & Count")
    logger.info(f"Input: {input_path}")
    logger.info(f"Output: {output_path}")
    
    try:
        # Ensure directories
        ensure_directories(base_path)
        
        # Load data
        df = load_moral_machine_data(input_path)
        
        # Apply column mapping
        df = apply_column_mapping(df)
        
        # Capture pre-filter count (before location filtering)
        capture_pre_filter_count(df, counts_log_path)
        
        # Filter 1: Missing location
        df, count_missing_location = filter_missing_location(df, exclusion_log_path)
        
        # Filter 2: Invalid response time
        df, count_invalid_response_time = filter_invalid_response_time(
            df, 
            exclusion_log_path,
            min_ms=100,
            max_ms=10000
        )
        
        # Log final counts
        log_counts_to_file(
            counts_log_path,
            count_filtered=len(df),
            count_missing_location=count_missing_location,
            count_invalid_response_time=count_invalid_response_time
        )
        
        # Save filtered data
        save_filtered_data(df, output_path)
        
        logger.info("T017 completed successfully")
        print(f"SUCCESS: Filtered dataset saved to {output_path}")
        print(f"Total records after filtering: {len(df)}")
        print(f"Excluded for missing location: {count_missing_location}")
        print(f"Excluded for invalid response time: {count_invalid_response_time}")
        
    except Exception as e:
        logger.error(f"T017 failed: {e}")
        raise

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='T017: Load, Filter & Count')
    parser.add_argument('--input', type=str, help='Input CSV path')
    parser.add_argument('--output', type=str, help='Output Parquet path')
    parser.add_argument('--exclusion-log', type=str, help='Exclusion log path')
    parser.add_argument('--counts-log', type=str, help='Counts log path')
    
    args = parser.parse_args()
    
    main(
        input_path=args.input,
        output_path=args.output,
        exclusion_log_path=args.exclusion_log,
        counts_log_path=args.counts_log
    )
