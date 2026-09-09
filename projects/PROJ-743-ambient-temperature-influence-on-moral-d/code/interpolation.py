"""
Interpolation module for ERA5 temporal gaps.

Implements T019c: Interpolate & Flag Gaps.
Processes ERA5 data to find nearest temporal neighbors for Moral Machine records,
interpolates if gap <= 2 hours, and flags/excludes records with larger gaps.
"""
import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import pandas as pd
import numpy as np

from config import get_path_env_override
from setup_logging import setup_logging, get_data_quality_logger
from loaders import load_parquet_as_df

# Constants
GAP_THRESHOLD_HOURS = 2.0
DATA_QUALITY_LOG_PATH = "results/logs/data_quality_log.json"
ERAS5_FULL_PATH = "data/raw/era5_full.parquet"
MERGED_DATASET_PATH = "data/processed/merged_dataset.parquet"
OUTPUT_PATH = "data/processed/interpolated_dataset.parquet"

def ensure_directories():
    """Ensure output directories exist."""
    Path("results/logs").mkdir(parents=True, exist_ok=True)
    Path("data/processed").mkdir(parents=True, exist_ok=True)

def setup_custom_logger(name):
    """Setup custom logger for this module."""
    return get_data_quality_logger(name)

def load_merged_data() -> pd.DataFrame:
    """Load the merged dataset from T019/T019a."""
    path = Path(get_path_env_override("MERGED_DATASET_PATH", MERGED_DATASET_PATH))
    if not path.exists():
        raise FileNotFoundError(f"Missing merged dataset at {path}")
    return load_parquet_as_df(path)

def load_era5_data() -> pd.DataFrame:
    """Load the full ERA5 dataset."""
    path = Path(get_path_env_override("ERA5_FULL_PATH", ERAS5_FULL_PATH))
    if not path.exists():
        raise FileNotFoundError(f"Missing ERA5 full dataset at {path}")
    return load_parquet_as_df(path)

def calculate_temporal_gap(timestamp: pd.Timestamp, prev_ts: pd.Timestamp, next_ts: pd.Timestamp) -> float:
    """
    Calculate the total temporal gap in hours between the surrounding ERA5 points.
    Returns the sum of the gap before and after the target timestamp.
    """
    if pd.isna(prev_ts) or pd.isna(next_ts):
        return float('inf')
    
    gap_before = (timestamp - prev_ts).total_seconds() / 3600.0
    gap_after = (next_ts - timestamp).total_seconds() / 3600.0
    return gap_before + gap_after

def interpolate_temperature(row: pd.Series, era5_subset: pd.DataFrame) -> Optional[float]:
    """
    Perform linear interpolation for a single record.
    
    Args:
        row: The Moral Machine record with 'grid_id' and 'timestamp'.
        era5_subset: Filtered ERA5 data for the specific grid_id, sorted by timestamp.
        
    Returns:
        Interpolated temperature or None if gap is too large.
    """
    target_ts = row['timestamp']
    grid_id = row['grid_id']
    
    # Filter for this grid
    grid_data = era5_subset[era5_subset['grid_id'] == grid_id].sort_values('timestamp')
    
    if grid_data.empty:
        return None
    
    # Find surrounding points
    # We need the point immediately before and immediately after the target timestamp
    before = grid_data[grid_data['timestamp'] <= target_ts]
    after = grid_data[grid_data['timestamp'] >= target_ts]
    
    prev_ts = before['timestamp'].max() if not before.empty else None
    next_ts = after['timestamp'].min() if not after.empty else None
    
    # If we have an exact match, use it directly
    if not after.empty and next_ts == target_ts:
        return after[after['timestamp'] == next_ts]['temperature_celsius'].iloc[0]
    
    # Calculate total gap
    gap = calculate_temporal_gap(target_ts, prev_ts, next_ts)
    
    if gap > GAP_THRESHOLD_HOURS:
        return None  # Gap too large
    
    # Linear interpolation
    if prev_ts is None or next_ts is None:
        return None  # Cannot interpolate without both sides
    
    prev_temp = before[before['timestamp'] == prev_ts]['temperature_celsius'].iloc[0]
    next_temp = after[after['timestamp'] == next_ts]['temperature_celsius'].iloc[0]
    
    # Interpolation factor (0.0 to 1.0)
    total_span = (next_ts - prev_ts).total_seconds() / 3600.0
    if total_span == 0:
        return prev_temp
        
    fraction = (target_ts - prev_ts).total_seconds() / (total_span * 3600.0)
    interpolated_temp = prev_temp + (next_temp - prev_temp) * fraction
    
    return interpolated_temp

def process_interpolation():
    """
    Main processing function for T019c.
    1. Load merged dataset and ERA5 data.
    2. Filter ERA5 to relevant grid_ids and timestamps.
    3. Interpolate temperatures.
    4. Flag/exclude records with gaps > 2 hours.
    5. Save results.
    """
    logger = setup_custom_logger("interpolation")
    logger.info("Starting interpolation process (T019c)")
    
    ensure_directories()
    
    # Load data
    try:
        merged_df = load_merged_data()
        era5_df = load_era5_data()
    except FileNotFoundError as e:
        logger.error(str(e))
        raise
    
    logger.info(f"Loaded {len(merged_df)} merged records and {len(era5_df)} ERA5 records")
    
    # Ensure timestamps are datetime
    merged_df['timestamp'] = pd.to_datetime(merged_df['timestamp'])
    era5_df['timestamp'] = pd.to_datetime(era5_df['timestamp'])
    
    # Initialize results list
    results = []
    excluded_records = []
    
    # Process each record
    logger.info("Processing interpolation for each record...")
    for idx, row in merged_df.iterrows():
        grid_id = row['grid_id']
        timestamp = row['timestamp']
        
        # Check if grid_id exists in ERA5
        if grid_id not in era5_df['grid_id'].values:
            excluded_records.append({
                'record_idx': idx,
                'reason': 'grid_id_not_in_era5',
                'grid_id': grid_id,
                'timestamp': str(timestamp)
            })
            continue
        
        # Perform interpolation
        interp_temp = interpolate_temperature(row, era5_df)
        
        if interp_temp is None:
            # Determine specific reason
            era5_grid = era5_df[era5_df['grid_id'] == grid_id].sort_values('timestamp')
            if era5_grid.empty:
                reason = 'no_data_for_grid'
            else:
                # Check gap size
                before = era5_grid[era5_grid['timestamp'] <= timestamp]
                after = era5_grid[era5_grid['timestamp'] >= timestamp]
                if before.empty or after.empty:
                    reason = 'missing_surrounding_points'
                else:
                    gap = calculate_temporal_gap(timestamp, before['timestamp'].max(), after['timestamp'].min())
                    reason = f'temperature_gap_{gap:.2f}_hours'
            
            excluded_records.append({
                'record_idx': idx,
                'reason': reason,
                'grid_id': grid_id,
                'timestamp': str(timestamp)
            })
        else:
            # Add interpolated temperature to row
            new_row = row.to_dict()
            new_row['interpolated_temperature'] = interp_temp
            new_row['interpolation_gap_status'] = 'valid'
            results.append(new_row)
    
    logger.info(f"Processed {len(results)} valid records, excluded {len(excluded_records)} records")
    
    # Log excluded records
    if excluded_records:
        log_path = Path(DATA_QUALITY_LOG_PATH)
        existing_logs = []
        if log_path.exists():
            with open(log_path, 'r') as f:
                try:
                    existing_logs = json.load(f)
                except json.JSONDecodeError:
                    existing_logs = []
        
        existing_logs.extend(excluded_records)
        with open(log_path, 'w') as f:
            json.dump(existing_logs, f, indent=2)
        logger.info(f"Logged {len(excluded_records)} exclusions to {DATA_QUALITY_LOG_PATH}")
    
    # Create output DataFrame
    output_df = pd.DataFrame(results)
    
    # Save output
    output_path = Path(get_path_env_override("OUTPUT_PATH", OUTPUT_PATH))
    output_df.to_parquet(output_path, index=False)
    logger.info(f"Saved interpolated dataset to {output_path}")
    
    # Log summary
    summary = {
        'total_records': len(merged_df),
        'valid_records': len(results),
        'excluded_records': len(excluded_records),
        'exclusion_reasons': {}
    }
    
    for rec in excluded_records:
        reason = rec['reason']
        summary['exclusion_reasons'][reason] = summary['exclusion_reasons'].get(reason, 0) + 1
    
    summary_path = Path("results/logs/interpolation_summary.json")
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    return summary

def main():
    """Entry point for the script."""
    try:
        summary = process_interpolation()
        print(json.dumps(summary, indent=2))
        sys.exit(0)
    except Exception as e:
        logging.error(f"Interpolation failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
