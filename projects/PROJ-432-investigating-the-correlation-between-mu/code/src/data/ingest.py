import hashlib
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests

# Import utilities from the existing utils module
from .utils import setup_logger, calculate_file_checksum, parse_date_string, normalize_date_column, write_json_log, validate_date_range

# Constants for logging
LOG_FILE = "logs/alignment.json"
REASON_MISSING_ERA5 = "missing_era5"
REASON_ICECUBE_MAINTENANCE = "icecube_maintenance"
REASON_OTHER = "other"
SOURCE_ICECUBE = "icecube"
SOURCE_ERA5 = "era5"

def ensure_directories(base_path: Path):
    """Ensure all required directories exist."""
    dirs = [
        base_path / "data" / "raw",
        base_path / "data" / "processed",
        base_path / "data" / "results",
        base_path / "logs",
        base_path / "config"
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    return dirs

def fetch_icecube_data(output_path: Path, start_date: str, end_date: str):
    """
    Fetch IceCube muon flux data.
    In a real scenario, this would use the IceCube API or download from a URL.
    For this implementation, we assume the data is already cached in data/raw/icecube.csv
    or we fetch it from a known URL if not present.
    """
    if output_path.exists():
        logging.info(f"Using cached IceCube data: {output_path}")
        return pd.read_csv(output_path)
    
    # Placeholder for real fetch logic
    # In a real implementation, this would call the IceCube API or download from a URL
    # For now, we raise an error if the file doesn't exist to enforce real data usage
    raise FileNotFoundError(f"IceCube data not found at {output_path}. Please ensure data is downloaded.")

def fetch_era5_data(output_path: Path, start_date: str, end_date: str):
    """
    Fetch ERA5 atmospheric data.
    Uses cdsapi or a direct URL if available.
    """
    if output_path.exists():
        logging.info(f"Using cached ERA5 data: {output_path}")
        return pd.read_csv(output_path)
    
    # Placeholder for real fetch logic
    raise FileNotFoundError(f"ERA5 data not found at {output_path}. Please ensure data is downloaded.")

def validate_icecube_data(df: pd.DataFrame) -> bool:
    """Validate IceCube data structure and content."""
    required_cols = ['date', 'muon_count']
    if not all(col in df.columns for col in required_cols):
        return False
    if df['muon_count'].isnull().any():
        return False
    if (df['muon_count'] < 0).any():
        return False
    return True

def validate_era5_data(df: pd.DataFrame) -> bool:
    """Validate ERA5 data structure and content."""
    required_cols = ['date', 'temperature', 'pressure']
    if not all(col in df.columns for col in required_cols):
        return False
    if df['temperature'].isnull().any() or df['pressure'].isnull().any():
        return False
    return True

def run_validation(df_icecube: pd.DataFrame, df_era5: pd.DataFrame) -> bool:
    """Run validation on both datasets."""
    valid_icecube = validate_icecube_data(df_icecube)
    valid_era5 = validate_era5_data(df_era5)
    return valid_icecube and valid_era5

def log_exclusion_event(log_path: Path, date: str, reason: str, source: str):
    """
    Log an exclusion event to the alignment log file.
    Format: list of objects { "date": "YYYY-MM-DD", "reason": "...", "source": "..." }
    """
    if not log_path.parent.exists():
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    exclusion_entry = {
        "date": date,
        "reason": reason,
        "source": source
    }
    
    # Load existing log if it exists
    if log_path.exists():
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                log_data = json.load(f)
        except (json.JSONDecodeError, IOError):
            log_data = []
    else:
        log_data = []
    
    # Append new entry
    log_data.append(exclusion_entry)
    
    # Write back to file
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, indent=2)

def align_temporal_data(df_icecube: pd.DataFrame, df_era5: pd.DataFrame, log_path: Path) -> pd.DataFrame:
    """
    Align IceCube and ERA5 data to daily bins.
    Drops dates with missing data in either source and logs exclusion events.
    """
    # Ensure date columns are datetime
    df_icecube['date'] = pd.to_datetime(df_icecube['date'])
    df_era5['date'] = pd.to_datetime(df_era5['date'])
    
    # Resample to daily (assuming data is already daily or needs aggregation)
    # For this task, we assume data is already daily, so we just set index
    df_icecube_daily = df_icecube.set_index('date').resample('D').sum().reset_index()
    df_era5_daily = df_era5.set_index('date').resample('D').mean().reset_index()
    
    # Find all unique dates
    all_dates = set(df_icecube_daily['date'].dt.date) | set(df_era5_daily['date'].dt.date)
    
    # Identify missing dates for each source
    icecube_dates = set(df_icecube_daily['date'].dt.date)
    era5_dates = set(df_era5_daily['date'].dt.date)
    
    missing_era5_dates = all_dates - era5_dates
    missing_icecube_dates = all_dates - icecube_dates
    
    # Log exclusion events
    for date in missing_era5_dates:
        date_str = date.strftime('%Y-%m-%d')
        log_exclusion_event(log_path, date_str, REASON_MISSING_ERA5, SOURCE_ERA5)
    
    for date in missing_icecube_dates:
        date_str = date.strftime('%Y-%m-%d')
        log_exclusion_event(log_path, date_str, REASON_ICECUBE_MAINTENANCE, SOURCE_ICECUBE)
    
    # Filter to only dates present in both
    common_dates = icecube_dates & era5_dates
    df_icecube_filtered = df_icecube_daily[df_icecube_daily['date'].dt.date.isin(common_dates)]
    df_era5_filtered = df_era5_daily[df_era5_daily['date'].dt.date.isin(common_dates)]
    
    # Merge on date
    merged_df = pd.merge(df_icecube_filtered, df_era5_filtered, on='date', how='inner')
    
    return merged_df

def run_ingestion(base_path: Path, start_date: str, end_date: str):
    """
    Run the full ingestion pipeline: fetch, validate, align, and log exclusions.
    """
    ensure_directories(base_path)
    log_path = base_path / LOG_FILE
    
    # Clear log file at start of run
    if log_path.exists():
        log_path.unlink()
    
    icecube_path = base_path / "data" / "raw" / "icecube.csv"
    era5_path = base_path / "data" / "raw" / "era5.csv"
    
    try:
        df_icecube = fetch_icecube_data(icecube_path, start_date, end_date)
        df_era5 = fetch_era5_data(era5_path, start_date, end_date)
    except FileNotFoundError as e:
        logging.error(f"Data fetch failed: {e}")
        return None
    
    if not run_validation(df_icecube, df_era5):
        logging.error("Data validation failed.")
        return None
    
    aligned_df = align_temporal_data(df_icecube, df_era5, log_path)
    
    if aligned_df is None or aligned_df.empty:
        logging.error("Alignment resulted in empty dataset.")
        return None
    
    output_path = base_path / "data" / "processed" / "aligned_daily.csv"
    aligned_df.to_csv(output_path, index=False)
    logging.info(f"Aligned data saved to {output_path}")
    logging.info(f"Exclusion events logged to {log_path}")
    
    return aligned_df

if __name__ == "__main__":
    # Example usage for testing
    logging.basicConfig(level=logging.INFO)
    base = Path(".")
    run_ingestion(base, "2023-01-01", "2023-01-07")
