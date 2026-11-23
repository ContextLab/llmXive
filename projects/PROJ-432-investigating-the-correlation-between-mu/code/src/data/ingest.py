"""
Ingestion module for IceCube muon flux and ERA5 atmospheric data.
Handles downloading, caching, validation, and temporal alignment.
"""
import hashlib
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List

import pandas as pd
import numpy as np

# Local imports
from src.data.utils import (
    setup_logger,
    calculate_file_checksum,
    parse_date_string,
    normalize_date_column,
    write_json_log,
    validate_date_range
)
from src.config.constants import load_config

# Setup logger
logger = setup_logger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
LOGS_DIR = PROJECT_ROOT / "logs"
CONFIG_PATH = PROJECT_ROOT / "code" / "src" / "config" / "constants.yaml"

# Ensure directories exist
DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)


def ensure_directories():
    """Create necessary directory structure if it doesn't exist."""
    dirs = [DATA_RAW_DIR, DATA_PROCESSED_DIR, LOGS_DIR]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured directory exists: {d}")


def fetch_icecube_data(force: bool = False) -> pd.DataFrame:
    """
    Fetch IceCube muon flux data.
    In a real implementation, this would call the IceCube API or download from a URL.
    For this implementation, we assume data is already cached in data/raw/icecube.csv
    as per T009 completion status, or fetch it if missing.
    """
    ensure_directories()
    cache_path = DATA_RAW_DIR / "icecube.csv"

    if cache_path.exists() and not force:
        logger.info(f"Loading cached IceCube data from {cache_path}")
        df = pd.read_csv(cache_path)
        # Validate date format
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
        return df

    logger.warning("IceCube data not found in cache. Attempting to fetch...")
    # Placeholder for actual API call
    # In a real scenario: response = requests.get(ICECUBE_URL) ...
    # For now, we raise an error to prevent fabrication
    raise FileNotFoundError(
        "IceCube data not found at cache path and fetch implementation is pending. "
        "Please ensure T009 has successfully populated data/raw/icecube.csv or implement the fetch logic."
    )


def fetch_era5_data(force: bool = False) -> pd.DataFrame:
    """
    Fetch ERA5 atmospheric data.
    In a real implementation, this would use cdsapi or download from HuggingFace.
    Assumes data is cached in data/raw/era5.csv as per T010.
    """
    ensure_directories()
    cache_path = DATA_RAW_DIR / "era5.csv"

    if cache_path.exists() and not force:
        logger.info(f"Loading cached ERA5 data from {cache_path}")
        df = pd.read_csv(cache_path)
        # Validate date format
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
        return df

    logger.warning("ERA5 data not found in cache. Attempting to fetch...")
    # Placeholder for actual API call (cdsapi)
    # In a real scenario: import cdsapi; client = cdsapi.Client(); ...
    raise FileNotFoundError(
        "ERA5 data not found at cache path and fetch implementation is pending. "
        "Please ensure T010 has successfully populated data/raw/era5.csv or implement the fetch logic."
    )


def validate_icecube_data(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Validate IceCube muon flux data.
    
    Checks:
    1. 'date' column exists
    2. 'muon_count' (or similar) column exists and is non-negative
    3. No null values in critical columns
    4. Date range is reasonable (not in future)
    
    Returns:
      Tuple of (is_valid, list of error messages)
    """
    errors = []
    
    # Check required columns
    required_cols = ['date', 'muon_count']
    for col in required_cols:
        if col not in df.columns:
            errors.append(f"Missing required column: {col}")
    
    if errors:
        return False, errors

    # Check date column
    if df['date'].isnull().any():
        errors.append("Found null values in 'date' column")
    
    # Check muon_count column
    if 'muon_count' in df.columns:
        if df['muon_count'].isnull().any():
            errors.append("Found null values in 'muon_count' column")
        
        if (df['muon_count'] < 0).any():
            errors.append("Found negative values in 'muon_count' column")
    
    # Check date range (not in future)
    now = datetime.now()
    if (df['date'] > now).any():
        errors.append("Found dates in the future")

    return len(errors) == 0, errors


def validate_era5_data(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Validate ERA5 atmospheric data.
    
    Checks:
    1. 'date' column exists
    2. Pressure levels (hPa) are valid (positive, within reasonable range)
    3. Temperature values are valid (not null, within physical range)
    4. No null values in critical columns
    
    Returns:
      Tuple of (is_valid, list of error messages)
    """
    errors = []
    
    # Check required columns
    required_cols = ['date']
    for col in required_cols:
        if col not in df.columns:
            errors.append(f"Missing required column: {col}")
    
    if errors:
        return False, errors

    # Check date column
    if df['date'].isnull().any():
        errors.append("Found null values in 'date' column")
    
    # Check pressure columns (usually multiple levels)
    pressure_cols = [col for col in df.columns if 'pressure' in col.lower() or 'hpa' in col.lower()]
    if not pressure_cols:
        # Try to identify pressure columns by common names
        pressure_cols = [col for col in df.columns if col in ['pressure', 'P1000', 'P925', 'P850', 'P700', 'P500', 'P400', 'P300', 'P250', 'P200', 'P150', 'P100', 'P70', 'P50', 'P30', 'P20', 'P10']]
    
    for col in pressure_cols:
        if col in df.columns:
            if df[col].isnull().any():
                errors.append(f"Found null values in pressure column: {col}")
            if (df[col] <= 0).any():
                errors.append(f"Found non-positive pressure values in column: {col}")
            # Reasonable pressure range: 0.1 hPa to 1100 hPa
            if (df[col] < 0.1).any() or (df[col] > 1100).any():
                errors.append(f"Pressure values out of reasonable range (0.1-1100 hPa) in column: {col}")
    
    # Check temperature columns
    temp_cols = [col for col in df.columns if 'temp' in col.lower() or 'temperature' in col.lower()]
    if not temp_cols:
        temp_cols = [col for col in df.columns if col in ['temperature', 'T1000', 'T925', 'T850', 'T700', 'T500', 'T400', 'T300', 'T250', 'T200', 'T150', 'T100', 'T70', 'T50', 'T30', 'T20', 'T10']]
    
    for col in temp_cols:
        if col in df.columns:
            if df[col].isnull().any():
                errors.append(f"Found null values in temperature column: {col}")
            # Reasonable temperature range: -100°C to 60°C (or -173K to 333K)
            # Assuming Celsius for ERA5
            if (df[col] < -100).any() or (df[col] > 60).any():
                errors.append(f"Temperature values out of reasonable range (-100 to 60°C) in column: {col}")

    return len(errors) == 0, errors


def run_validation() -> Dict[str, Any]:
    """
    Run validation on both IceCube and ERA5 data.
    Returns a summary of validation results.
    """
    results = {
        "timestamp": datetime.now().isoformat(),
        "icecube": {"valid": False, "errors": []},
        "era5": {"valid": False, "errors": []},
        "overall_valid": False
    }
    
    try:
        icecube_df = fetch_icecube_data()
        is_valid, errors = validate_icecube_data(icecube_df)
        results["icecube"]["valid"] = is_valid
        results["icecube"]["errors"] = errors
        results["icecube"]["row_count"] = len(icecube_df)
        logger.info(f"IceCube validation: {'PASSED' if is_valid else 'FAILED'} - {len(errors)} errors")
    except Exception as e:
        results["icecube"]["errors"].append(f"Fetch error: {str(e)}")
        logger.error(f"Error validating IceCube data: {e}")
    
    try:
        era5_df = fetch_era5_data()
        is_valid, errors = validate_era5_data(era5_df)
        results["era5"]["valid"] = is_valid
        results["era5"]["errors"] = errors
        results["era5"]["row_count"] = len(era5_df)
        logger.info(f"ERA5 validation: {'PASSED' if is_valid else 'FAILED'} - {len(errors)} errors")
    except Exception as e:
        results["era5"]["errors"].append(f"Fetch error: {str(e)}")
        logger.error(f"Error validating ERA5 data: {e}")
    
    results["overall_valid"] = (
        results["icecube"]["valid"] and 
        results["era5"]["valid"] and 
        len(results["icecube"]["errors"]) == 0 and 
        len(results["era5"]["errors"]) == 0
    )
    
    # Save validation results to logs
    log_path = LOGS_DIR / "validation_results.json"
    with open(log_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    logger.info(f"Validation results saved to {log_path}")
    
    return results


def log_exclusion_event(date: str, reason: str, source: str):
    """
    Log a data exclusion event to logs/alignment.json.
    
    Args:
        date: Date string in YYYY-MM-DD format
        reason: Reason for exclusion (e.g., 'missing_era5', 'icecube_maintenance')
        source: Source of data (e.g., 'icecube', 'era5')
    """
    log_path = LOGS_DIR / "alignment.json"
    
    event = {
        "date": date,
        "reason": reason,
        "source": source
    }
    
    write_json_log(log_path, event)
    logger.info(f"Logged exclusion event: {event}")


def align_temporal_data(icecube_df: pd.DataFrame, era5_df: pd.DataFrame) -> pd.DataFrame:
    """
    Align IceCube and ERA5 data to daily bins.
    
    Steps:
    1. Resample muon counts to daily sums
    2. Average temperature metrics to daily means
    3. Drop dates with missing data in either source
    4. Log exclusion events
    
    Returns:
        Aligned DataFrame with daily data
    """
    ensure_directories()
    
    # Ensure date columns are datetime
    if 'date' in icecube_df.columns:
        icecube_df['date'] = pd.to_datetime(icecube_df['date'])
    if 'date' in era5_df.columns:
        era5_df['date'] = pd.to_datetime(era55_df['date'])
    
    # Resample IceCube data to daily
    icecube_daily = icecube_df.set_index('date').resample('D').sum().reset_index()
    icecube_daily = icecube_daily.dropna(subset=['muon_count'])
    
    # Resample ERA5 data to daily (average for temperature, sum/mean for pressure as appropriate)
    # Assuming temperature columns start with 'T' or contain 'temp'
    temp_cols = [col for col in era5_df.columns if 'temp' in col.lower() or 'temperature' in col.lower()]
    if temp_cols:
        era5_daily = era5_df.set_index('date').resample('D')[temp_cols].mean().reset_index()
    else:
        era5_daily = era5_df.set_index('date').resample('D').mean().reset_index()
    
    era5_daily = era5_daily.dropna()
    
    # Merge on date
    aligned = pd.merge(icecube_daily, era5_daily, on='date', how='inner')
    
    # Log excluded dates
    all_dates = pd.date_range(
        start=min(icecube_df['date'].min(), era5_df['date'].min()),
        end=max(icecube_df['date'].max(), era5_df['date'].max()),
        freq='D'
    )
    
    icecube_dates = set(icecube_daily['date'].dt.strftime('%Y-%m-%d'))
    era5_dates = set(era5_daily['date'].dt.strftime('%Y-%m-%d'))
    aligned_dates = set(aligned['date'].dt.strftime('%Y-%m-%d'))
    
    for date in all_dates:
        date_str = date.strftime('%Y-%m-%d')
        if date_str not in icecube_dates and date_str not in era5_dates:
            log_exclusion_event(date_str, "missing_both", "both")
        elif date_str not in icecube_dates:
            log_exclusion_event(date_str, "missing_icecube", "icecube")
        elif date_str not in era5_dates:
            log_exclusion_event(date_str, "missing_era5", "era5")
    
    logger.info(f"Aligned data: {len(aligned)} daily records")
    return aligned


def run_ingestion():
    """
    Main entry point for the ingestion pipeline.
    Executes download, validation, and alignment.
    """
    logger.info("Starting ingestion pipeline")
    
    # Fetch data
    icecube_df = fetch_icecube_data()
    era5_df = fetch_era5_data()
    
    # Validate data
    icecube_valid, icecube_errors = validate_icecube_data(icecube_df)
    era5_valid, era5_errors = validate_era5_data(era5_df)
    
    if not icecube_valid:
        logger.error(f"IceCube validation failed: {icecube_errors}")
        return False
    if not era5_valid:
        logger.error(f"ERA5 validation failed: {era5_errors}")
        return False
    
    # Align data
    aligned_df = align_temporal_data(icecube_df, era5_df)
    
    # Save aligned data
    output_path = DATA_PROCESSED_DIR / "aligned_daily.csv"
    aligned_df.to_csv(output_path, index=False)
    logger.info(f"Saved aligned data to {output_path}")
    
    return True


if __name__ == "__main__":
    success = run_ingestion()
    sys.exit(0 if success else 1)