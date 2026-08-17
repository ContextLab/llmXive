import os
import sys
import logging
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
import pandas as pd
import numpy as np

# Import logging setup from existing project module
from setup_logging import get_data_quality_logger

# Constants
TEMP_GAP_THRESHOLD_HOURS = 2.0
EXCLUSION_LOG_PATH = Path("results/logs/exclusion_log.csv")
MERGED_DATASET_PATH = Path("data/processed/merged_dataset.parquet")

# Initialize logger
logger = get_data_quality_logger()

def ensure_exclusion_log_exists():
    """Ensure the exclusion log file and directory exist."""
    EXCLUSION_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not EXCLUSION_LOG_PATH.exists():
        # Create empty CSV with headers
        pd.DataFrame(columns=['record_id', 'reason', 'details']).to_csv(
            EXCLUSION_LOG_PATH, index=False
        )

def log_excluded_records(records_to_exclude: list):
    """
    Append exclusion records to the CSV log.
    
    Args:
        records_to_exclude: List of dicts with keys: record_id, reason, details
    """
    if not records_to_exclude:
        return

    df_exclusion = pd.DataFrame(records_to_exclude)
    
    # Append to existing CSV without headers if file exists
    if EXCLUSION_LOG_PATH.exists() and EXCLUSION_LOG_PATH.stat().st_size > 0:
        df_exclusion.to_csv(EXCLUSION_LOG_PATH, mode='a', header=False, index=False)
    else:
        df_exclusion.to_csv(EXCLUSION_LOG_PATH, index=False)
    
    logger.info(f"Logged {len(records_to_exclude)} excluded records to {EXCLUSION_LOG_PATH}")

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points on the Earth (km).
    
    Args:
        lat1, lon1: Coordinates of point 1 (degrees)
        lat2, lon2: Coordinates of point 2 (degrees)
        
    Returns:
        Distance in kilometers
    """
    R = 6371.0  # Earth radius in km
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlambda = np.radians(lon2 - lon1)

    a = np.sin(dphi/2.0)**2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlambda/2.0)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))

    return R * c

def match_geospatial_records(moral_df: pd.DataFrame, era5_df: pd.DataFrame, threshold_km: float = 100.0) -> Tuple[pd.DataFrame, list]:
    """
    Match Moral Machine records to nearest ERA5 grid point within threshold.
    
    Args:
        moral_df: Moral Machine dataset with 'latitude', 'longitude'
        era5_df: ERA5 dataset with 'latitude', 'longitude'
        threshold_km: Maximum distance threshold in km
        
    Returns:
        Tuple of (matched_df, exclusion_log_entries)
    """
    exclusion_log_entries = []
    matched_records = []

    # Ensure ERA5 is indexed by lat/lon for efficient lookup (simplified for this task)
    # In production, use spatial index (e.g., k-d tree) for large datasets
    era5_coords = era5_df[['latitude', 'longitude']].drop_duplicates()

    for idx, moral_row in moral_df.iterrows():
        m_lat = moral_row['latitude']
        m_lon = moral_row['longitude']
        
        # Calculate distances to all ERA5 grid points
        # Optimized: vectorized calculation
        distances = era5_coords.apply(
            lambda row: haversine_distance(m_lat, m_lon, row['latitude'], row['longitude']),
            axis=1
        )
        
        min_dist = distances.min()
        nearest_idx = distances.idxmin()
        
        if min_dist > threshold_km:
            exclusion_log_entries.append({
                'record_id': moral_row.get('id', idx),
                'reason': 'distance > 100km',
                'details': f"Nearest ERA5 grid point is {min_dist:.2f}km away"
            })
            continue
        
        # Get nearest ERA5 record
        nearest_era5 = era5_df.loc[era5_coords.loc[nearest_idx].name] # Simplified lookup
        
        matched_records.append({
            **moral_row,
            'era5_lat': nearest_era5['latitude'],
            'era5_lon': nearest_era5['longitude'],
            'distance_km': min_dist,
            'match_quality': 'high' if min_dist < 50 else 'low'
        })

    matched_df = pd.DataFrame(matched_records)
    return matched_df, exclusion_log_entries

def interpolate_temporal_gaps(merged_df: pd.DataFrame) -> Tuple[pd.DataFrame, list]:
    """
    Apply linear interpolation for missing ERA5 hourly values.
    Exclude records if gap > 2 hours.
    
    Args:
        merged_df: DataFrame with 'timestamp' (datetime) and 'temperature_celsius'
        
    Returns:
        Tuple of (cleaned_df, exclusion_log_entries)
    """
    exclusion_log_entries = []
    cleaned_records = []
    
    # Sort by timestamp to ensure correct interpolation order
    # Ensure timestamp is datetime
    if not pd.api.types.is_datetime64_any_dtype(merged_df['timestamp']):
        merged_df['timestamp'] = pd.to_datetime(merged_df['timestamp'])
    
    merged_df = merged_df.sort_values('timestamp')
    
    # Group by location to interpolate independently per grid point
    # Assuming 'era5_lat' and 'era5_lon' identify the grid point
    grouped = merged_df.groupby(['era5_lat', 'era5_lon'])
    
    for (lat, lon), group in grouped:
        group = group.set_index('timestamp').sort_index()
        
        # Reindex to hourly frequency to identify gaps
        full_range = pd.date_range(start=group.index.min(), end=group.index.max(), freq='H')
        group_reindexed = group.reindex(full_range)
        
        # Identify gaps
        # A gap is defined as a period where temperature is NaN
        # We need to check the size of the gap in hours
        temp_series = group_reindexed['temperature_celsius']
        
        # Create a mask for valid data
        valid_mask = temp_series.notna()
        
        # Find indices where data transitions from valid to invalid or vice versa
        # This helps identify gap boundaries
        diff = valid_mask.astype(int).diff()
        gap_start = diff == -1
        gap_end = diff == 1
        
        # Handle edge cases
        if valid_mask.iloc[0] == False:
            # Start with a gap
            pass 
        
        # Process gaps
        # Simple approach: iterate through rows and check consecutive NaNs
        current_gap_start = None
        gap_indices = []
        
        for i, (ts, val) in enumerate(temp_series.items()):
            if pd.isna(val):
                if current_gap_start is None:
                    current_gap_start = ts
                gap_indices.append(ts)
            else:
                if current_gap_start is not None:
                    # Gap ended
                    gap_duration = (ts - current_gap_start).total_seconds() / 3600.0
                    if gap_duration > TEMP_GAP_THRESHOLD_HOURS:
                        # Exclude records in this gap
                        for gap_ts in gap_indices:
                            # Find original record corresponding to gap_ts
                            original_row = group.loc[gap_ts] if gap_ts in group.index else None
                            if original_row is not None:
                                exclusion_log_entries.append({
                                    'record_id': original_row.get('id', 'unknown'),
                                    'reason': 'temporal_gap > 2h',
                                    'details': f"Gap of {gap_duration:.2f}h at {gap_ts}"
                                })
                    else:
                        # Interpolate
                        # We will interpolate after processing all gaps
                        pass
                    current_gap_start = None
                    gap_indices = []
        
        # Final gap check if ends with NaN
        if current_gap_start is not None:
            gap_duration = (temp_series.index[-1] - current_gap_start).total_seconds() / 3600.0
            if gap_duration > TEMP_GAP_THRESHOLD_HOURS:
                for gap_ts in gap_indices:
                    original_row = group.loc[gap_ts] if gap_ts in group.index else None
                    if original_row is not None:
                        exclusion_log_entries.append({
                            'record_id': original_row.get('id', 'unknown'),
                            'reason': 'temporal_gap > 2h',
                            'details': f"Gap of {gap_duration:.2f}h at {gap_ts}"
                        })
        
        # Perform interpolation for gaps <= 2h
        # Use linear interpolation
        interpolated_series = temp_series.interpolate(method='linear', limit_direction='both')
        
        # For rows that were originally NaN but not interpolated (gap > 2h), mark as excluded
        # Actually, we already excluded them above. Now we just keep the interpolated values.
        # But we need to be careful: if a gap was > 2h, we excluded those records.
        # The interpolation should only happen for gaps <= 2h.
        # The `interpolate` method will fill all NaNs. We need to revert the ones that were > 2h.
        # However, we already removed those from consideration in the exclusion logic above?
        # No, we just logged them. We need to drop them from the final dataframe.
        
        # Let's refine: 
        # 1. Identify which indices correspond to gaps > 2h.
        # 2. Drop those indices from the group before interpolation.
        # 3. Interpolate the rest.
        
        # Re-doing the gap logic more cleanly
        valid_data = group[['temperature_celsius']].copy()
        valid_data = valid_data.dropna() # Drop existing NaNs temporarily to find gaps? No.
        
        # Better approach: 
        # 1. Reindex to hourly.
        # 2. Identify gaps > 2h.
        # 3. Drop those specific rows from the reindexed dataframe.
        # 4. Interpolate remaining NaNs.
        # 5. Merge back with original non-NaN rows? 
        
        # Actually, the task says: "EXCLUDE the record if the gap > 2 hours".
        # This implies if a specific timestamp in the Moral Machine data falls into a gap > 2h, exclude it.
        # But ERA5 is hourly. If there is a missing hour in ERA5, and the gap to the next available hour is > 2h,
        # then any Moral Machine record mapped to that missing hour should be excluded.
        
        # Let's assume the merged_df already has ERA5 temp for the nearest hour.
        # If ERA5 has a gap (missing hour), and the gap is > 2h, we exclude.
        
        # Simplified logic for this task:
        # 1. Reindex to hourly.
        # 2. Find gaps > 2h.
        # 3. For any Moral Machine record that falls into a gap > 2h, exclude it.
        # 4. For gaps <= 2h, interpolate the missing value and assign it to the record.
        
        # Since we are working with the reindexed series, we can mark which indices are "bad".
        bad_indices = set()
        
        # Re-scan for bad gaps
        current_gap_start = None
        gap_indices = []
        
        for i, (ts, val) in enumerate(temp_series.items()):
            if pd.isna(val):
                if current_gap_start is None:
                    current_gap_start = ts
                gap_indices.append(ts)
            else:
                if current_gap_start is not None:
                    gap_duration = (ts - current_gap_start).total_seconds() / 3600.0
                    if gap_duration > TEMP_GAP_THRESHOLD_HOURS:
                        bad_indices.update(gap_indices)
                    current_gap_start = None
                    gap_indices = []
        
        if current_gap_start is not None:
            gap_duration = (temp_series.index[-1] - current_gap_start).total_seconds() / 3600.0
            if gap_duration > TEMP_GAP_THRESHOLD_HOURS:
                bad_indices.update(gap_indices)
        
        # Mark bad indices in the original group if they exist
        # We need to map back to the original Moral Machine records.
        # The reindexed dataframe has indices that might not be in the original group.
        # The original group has indices from the Moral Machine dataset.
        # We need to check if a Moral Machine record's timestamp falls into a bad gap.
        
        # Let's assume the merged_df has a 'timestamp' column that aligns with the Moral Machine record time.
        # We need to check if that timestamp is within a bad gap.
        
        # For simplicity in this task, we will assume the 'timestamp' in merged_df is the hour we are trying to fill.
        # If that hour is in a bad gap, exclude.
        
        # We'll create a mask for the current group
        group_mask = group.index.isin(bad_indices)
        if group_mask.any():
            # Log excluded records
            for bad_ts in group.index[group_mask]:
                original_row = group.loc[bad_ts]
                exclusion_log_entries.append({
                    'record_id': original_row.get('id', 'unknown'),
                    'reason': 'ERA5 coverage gap',
                    'details': f"Timestamp {bad_ts} falls in a gap > 2h"
                })
            # Drop these rows from the group
            group = group.drop(group.index[group_mask])
        
        # Now interpolate remaining NaNs
        if not group.empty:
            group['temperature_celsius'] = group['temperature_celsius'].interpolate(method='linear')
            
            # Check for any remaining NaNs (should not happen if all gaps <= 2h were interpolated)
            remaining_nans = group['temperature_celsius'].isna()
            if remaining_nans.any():
                for nan_ts in group.index[remaining_nans]:
                    original_row = group.loc[nan_ts]
                    exclusion_log_entries.append({
                        'record_id': original_row.get('id', 'unknown'),
                        'reason': 'Low confidence match',
                        'details': f"Could not interpolate value at {nan_ts}"
                    })
                group = group.drop(group.index[remaining_nans])
            
            cleaned_records.append(group.reset_index())
    
    if cleaned_records:
        cleaned_df = pd.concat(cleaned_records, ignore_index=True)
    else:
        cleaned_df = pd.DataFrame()
        
    return cleaned_df, exclusion_log_entries

def main():
    """Main execution function for T020."""
    logger.info("Starting T020: Time-based interpolation for missing ERA5 values")
    
    ensure_exclusion_log_exists()
    
    # Load the merged dataset from previous step (T019)
    # Assuming it exists at MERGED_DATASET_PATH
    if not MERGED_DATASET_PATH.exists():
        logger.error(f"Merged dataset not found at {MERGED_DATASET_PATH}. Cannot proceed.")
        sys.exit(1)
    
    try:
        merged_df = pd.read_parquet(MERGED_DATASET_PATH)
        logger.info(f"Loaded {len(merged_df)} records from {MERGED_DATASET_PATH}")
    except Exception as e:
        logger.error(f"Failed to load merged dataset: {e}")
        sys.exit(1)
    
    # Ensure required columns exist
    required_cols = ['timestamp', 'temperature_celsius', 'era5_lat', 'era5_lon']
    missing_cols = [col for col in required_cols if col not in merged_df.columns]
    if missing_cols:
        logger.error(f"Missing required columns in merged dataset: {missing_cols}")
        sys.exit(1)
    
    # Apply temporal interpolation
    cleaned_df, exclusion_entries = interpolate_temporal_gaps(merged_df)
    
    # Log excluded records
    if exclusion_entries:
        log_excluded_records(exclusion_entries)
        logger.info(f"Excluded {len(exclusion_entries)} records due to temporal gaps.")
    
    # Save cleaned dataset
    cleaned_df.to_parquet(MERGED_DATASET_PATH, index=False)
    logger.info(f"Saved cleaned dataset to {MERGED_DATASET_PATH} with {len(cleaned_df)} records")
    
    logger.info("T020 completed successfully.")

if __name__ == "__main__":
    main()