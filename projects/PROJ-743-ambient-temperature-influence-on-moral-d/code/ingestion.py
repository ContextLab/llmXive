"""
Ingestion module for Ambient Temperature Influence on Moral Decision Speed.

This module implements the core data ingestion pipeline:
1. Load and filter Moral Machine dataset
2. Geospatial matching with ERA5 temperature data
3. Temporal interpolation for temperature gaps
4. Data quality logging and exclusion tracking
"""

import os
import sys
import logging
import json
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.geometry import Point

from config import get_path_env_override
from loaders import load_chunked_parquet, load_parquet_as_df
from setup_logging import setup_logging, get_data_quality_logger

# Constants
DISTANCE_THRESHOLD_KM = 100  # From config.py, but kept here for clarity
TEMPORAL_GAP_HOURS = 2  # Maximum gap for interpolation

def ensure_exclusion_log_exists(log_path: Path) -> None:
    """Ensure the exclusion log file exists with proper headers."""
    if not log_path.parent.exists():
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    if not log_path.exists():
        df = pd.DataFrame(columns=['participant_id', 'reason', 'timestamp'])
        df.to_csv(log_path, index=False)

def log_excluded_records(df: pd.DataFrame, reason: str, log_path: Path) -> None:
    """Log excluded records to the exclusion log."""
    if df.empty:
        return
    
    excluded = df[['participant_id']].copy()
    excluded['reason'] = reason
    excluded['timestamp'] = pd.Timestamp.now()
    
    existing = pd.read_csv(log_path)
    updated = pd.concat([existing, excluded], ignore_index=True)
    updated.to_csv(log_path, index=False)

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points on Earth.
    
    Args:
        lat1, lon1: Coordinates of point 1 in degrees
        lat2, lon2: Coordinates of point 2 in degrees
    
    Returns:
        Distance in kilometers
    """
    R = 6371  # Earth's radius in km
    
    lat1_rad = np.radians(lat1)
    lat2_rad = np.radians(lat2)
    delta_lat = np.radians(lat2 - lat1)
    delta_lon = np.radians(lon2 - lon1)
    
    a = np.sin(delta_lat/2)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(delta_lon/2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
    
    return R * c

def match_geospatial_records(moral_df: pd.DataFrame, 
                             era5_df: pd.DataFrame,
                             distance_threshold_km: float = DISTANCE_THRESHOLD_KM) -> Tuple[pd.DataFrame, int]:
    """
    Match each Moral Machine record to the nearest ERA5 grid point.
    
    Args:
        moral_df: Filtered Moral Machine dataset
        era5_df: ERA5 temperature dataset with grid_id, latitude, longitude, timestamp
        distance_threshold_km: Maximum distance for a valid match
    
    Returns:
        Tuple of (matched dataframe with distance and match_quality, count_matched_pre_exclusion)
    """
    if moral_df.empty or era5_df.empty:
        return moral_df, 0
    
    # Convert to GeoDataFrames for spatial operations
    moral_gdf = gpd.GeoDataFrame(
        moral_df,
        geometry=gpd.points_from_xy(moral_df['longitude'], moral_df['latitude']),
        crs="EPSG:4326"
    )
    
    era5_gdf = gpd.GeoDataFrame(
        era5_df,
        geometry=gpd.points_from_xy(era5_df['longitude'], era5_df['latitude']),
        crs="EPSG:4326"
    )
    
    # For each moral record, find nearest ERA5 point
    matched_records = []
    count_matched_pre_exclusion = 0
    
    for idx, moral_row in moral_gdf.iterrows():
        # Calculate distances to all ERA5 points (this is expensive, optimize if needed)
        distances = []
        for era5_idx, era5_row in era5_gdf.iterrows():
            dist = haversine_distance(
                moral_row['latitude'], moral_row['longitude'],
                era5_row['latitude'], era5_row['longitude']
            )
            distances.append((era5_idx, dist))
        
        if distances:
            # Find nearest point
            nearest_idx, min_dist = min(distances, key=lambda x: x[1])
            count_matched_pre_exclusion += 1
            
            # Determine match quality
            match_quality = 'high' if min_dist <= distance_threshold_km else 'low'
            
            # Create matched record
            matched_record = moral_row.to_dict()
            matched_record['nearest_era5_grid_id'] = era5_gdf.loc[nearest_idx, 'grid_id']
            matched_record['nearest_era5_distance_km'] = min_dist
            matched_record['match_quality'] = match_quality
            matched_records.append(matched_record)
    
    matched_df = pd.DataFrame(matched_records)
    return matched_df, count_matched_pre_exclusion

def interpolate_temporal_gaps(matched_df: pd.DataFrame,
                              era5_df: pd.DataFrame,
                              temporal_gap_hours: float = TEMPORAL_GAP_HOURS) -> pd.DataFrame:
    """
    Interpolate temperature values for Moral Machine records.
    
    Args:
        matched_df: Moral Machine records with nearest ERA5 grid ID
        era5_df: ERA5 temperature dataset
        temporal_gap_hours: Maximum gap for interpolation
    
    Returns:
        DataFrame with interpolated temperature values and gap flags
    """
    if matched_df.empty or era5_df.empty:
        return matched_df
    
    result_df = matched_df.copy()
    result_df['temperature_celsius'] = np.nan
    result_df['gap_status'] = 'ok'
    
    # Group ERA5 data by grid_id for efficient lookup
    era5_grouped = era5_df.groupby('grid_id')
    
    for idx, row in result_df.iterrows():
        grid_id = row.get('nearest_era5_grid_id')
        moral_timestamp = row.get('timestamp')
        
        if pd.isna(grid_id) or pd.isna(moral_timestamp):
            continue
        
        # Get ERA5 data for this grid
        try:
            era5_grid_data = era5_grouped.get_group(grid_id)
            era5_grid_data = era5_grid_data.sort_values('timestamp')
            
            # Find surrounding ERA5 timestamps
            before_mask = era5_grid_data['timestamp'] <= moral_timestamp
            after_mask = era5_grid_data['timestamp'] >= moral_timestamp
            
            before_data = era5_grid_data[before_mask]
            after_data = era5_grid_data[after_mask]
            
            if before_data.empty and after_data.empty:
                result_df.loc[idx, 'gap_status'] = 'no_data'
                continue
            
            # Get closest timestamps
            if before_data.empty:
                nearest_before = after_data.iloc[0]
                gap_hours = 0  # No gap before
            elif after_data.empty:
                nearest_after = before_data.iloc[-1]
                gap_hours = 0  # No gap after
            else:
                nearest_before = before_data.iloc[-1]
                nearest_after = after_data.iloc[0]
                gap_hours = (nearest_after['timestamp'] - nearest_before['timestamp']).total_seconds() / 3600
            
            if gap_hours > temporal_gap_hours:
                result_df.loc[idx, 'gap_status'] = 'gap_too_large'
                continue
            
            # Linear interpolation
            if pd.isna(nearest_before['temperature_celsius']) or pd.isna(nearest_after['temperature_celsius']):
                # Use whatever is available
                if not pd.isna(nearest_before['temperature_celsius']):
                    temp = nearest_before['temperature_celsius']
                elif not pd.isna(nearest_after['temperature_celsius']):
                    temp = nearest_after['temperature_celsius']
                else:
                    result_df.loc[idx, 'gap_status'] = 'no_temp_data'
                    continue
            else:
                # Linear interpolation
                t0 = nearest_before['timestamp']
                t1 = nearest_after['timestamp']
                t = moral_timestamp
                
                if t1 == t0:
                    temp = nearest_before['temperature_celsius']
                else:
                    weight = (t - t0).total_seconds() / (t1 - t0).total_seconds()
                    temp = nearest_before['temperature_celsius'] + weight * (
                        nearest_after['temperature_celsius'] - nearest_before['temperature_celsius']
                    )
            
            result_df.loc[idx, 'temperature_celsius'] = temp
            
        except Exception as e:
            logging.warning(f"Error interpolating for record {idx}: {e}")
            result_df.loc[idx, 'gap_status'] = 'interpolation_error'
    
    return result_df

def capture_pre_filter_count(df: pd.DataFrame, log_path: Path) -> int:
    """
    Count records with valid latitude/longitude before filtering.
    
    Args:
        df: Raw Moral Machine dataset
        log_path: Path to counts.json log file
    
    Returns:
        Count of records with valid location data
    """
    valid_location = df[df['latitude'].notna() & df['longitude'].notna()].shape[0]
    
    # Update counts log
    counts_log = {}
    if log_path.exists():
        with open(log_path, 'r') as f:
            counts_log = json.load(f)
    
    counts_log['count_total_original_valid_location'] = valid_location
    
    with open(log_path, 'w') as f:
        json.dump(counts_log, f, indent=2)
    
    return valid_location

def main():
    """Main ingestion pipeline."""
    logger = setup_logging()
    data_logger = get_data_quality_logger()
    
    # Paths
    input_path = Path(get_path_env_override('MORAL_MACHINE_PATH', 'data/raw/moral_machine.csv.gz'))
    era5_path = Path(get_path_env_override('ERA5_PATH', 'data/raw/era5_full.parquet'))
    output_path = Path(get_path_env_override('MERGED_OUTPUT_PATH', 'data/processed/merged_dataset.parquet'))
    exclusion_log_path = Path('results/logs/exclusion_log.csv')
    counts_log_path = Path('results/logs/counts.json')
    quality_log_path = Path('results/logs/data_quality_log.json')
    
    # Ensure directories exist
    output_path.parent.mkdir(parents=True, exist_ok=True)
    exclusion_log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Ensure exclusion log exists
    ensure_exclusion_log_exists(exclusion_log_path)
    
    # Load data
    logger.info(f"Loading Moral Machine data from {input_path}")
    moral_df = load_parquet_as_df(input_path) if input_path.suffix == '.parquet' else pd.read_csv(input_path)
    
    logger.info(f"Loading ERA5 data from {era5_path}")
    era5_df = load_parquet_as_df(era5_path)
    
    # Capture pre-filter count (T017a)
    pre_filter_count = capture_pre_filter_count(moral_df, counts_log_path)
    data_logger.info(f"Pre-filter count: {pre_filter_count}")
    
    # T017: Load, Filter & Count
    # Filter 1: Missing location
    location_mask = moral_df['latitude'].notna() & moral_df['longitude'].notna()
    missing_location = moral_df[~location_mask]
    log_excluded_records(missing_location, "missing location", exclusion_log_path)
    moral_df = moral_df[location_mask]
    
    # Filter 2: Invalid response time
    response_time_mask = (moral_df['response_time'] >= 100) & (moral_df['response_time'] <= 10000)
    invalid_response_time = moral_df[~response_time_mask]
    log_excluded_records(invalid_response_time, "invalid response time", exclusion_log_path)
    moral_df = moral_df[response_time_mask]
    
    count_filtered_for_analysis = moral_df.shape[0]
    data_logger.info(f"Post-filter count: {count_filtered_for_analysis}")
    
    # T019: Geospatial Matching & Flagging
    logger.info("Performing geospatial matching...")
    matched_df, count_matched_pre_exclusion = match_geospatial_records(moral_df, era5_df)
    
    # Log pre-exclusion match count (T019a)
    counts_log = {}
    if counts_log_path.exists():
        with open(counts_log_path, 'r') as f:
            counts_log = json.load(f)
    counts_log['count_matched_pre_exclusion'] = count_matched_pre_exclusion
    with open(counts_log_path, 'w') as f:
        json.dump(counts_log, f, indent=2)
    
    data_logger.info(f"Matched pre-exclusion: {count_matched_pre_exclusion}")
    
    # Flag low quality matches
    low_quality_matches = matched_df[matched_df['match_quality'] == 'low']
    for _, row in low_quality_matches.iterrows():
        log_entry = {
            'participant_id': row['participant_id'],
            'reason': 'distance > 100km',
            'distance_km': row['nearest_era5_distance_km']
        }
        # Append to quality log
        quality_log = []
        if quality_log_path.exists():
            with open(quality_log_path, 'r') as f:
                quality_log = json.load(f)
        quality_log.append(log_entry)
        with open(quality_log_path, 'w') as f:
            json.dump(quality_log, f, indent=2)
    
    # T019c: Interpolate & Flag Gaps
    logger.info("Performing temporal interpolation...")
    interpolated_df = interpolate_temporal_gaps(matched_df, era5_df)
    
    # Flag records with unresolvable gaps
    gap_failures = interpolated_df[interpolated_df['gap_status'].isin(['gap_too_large', 'no_data', 'no_temp_data', 'interpolation_error'])]
    for _, row in gap_failures.iterrows():
        log_entry = {
            'participant_id': row['participant_id'],
            'reason': f"temperature gap issue: {row['gap_status']}"
        }
        quality_log = []
        if quality_log_path.exists():
            with open(quality_log_path, 'r') as f:
                quality_log = json.load(f)
        quality_log.append(log_entry)
        with open(quality_log_path, 'w') as f:
            json.dump(quality_log, f, indent=2)
    
    # Save intermediate results
    logger.info(f"Saving merged dataset to {output_path}")
    interpolated_df.to_parquet(output_path, index=False)
    
    logger.info("Ingestion pipeline completed successfully")
    return output_path

if __name__ == '__main__':
    main()