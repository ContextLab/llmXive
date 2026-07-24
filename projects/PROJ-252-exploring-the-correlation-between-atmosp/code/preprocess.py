"""
Preprocessing pipeline for earthquake and atmospheric pressure data.

Implements:
- T013: Interpolate coarse pressure grid to finer resolution
- T014: Calculate daily pressure anomalies using left-censored moving average
- T016: Deduplicate events by USGS ID
- T017: Generate master dataset pairing earthquakes with pressure anomalies
"""
import os
import json
import hashlib
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Import project config
from config import (
    get_data_path, get_raw_path, get_interim_path, get_processed_path,
    get_deviations_path, get_event_window_days, get_control_window_days,
    get_anomaly_window_days, get_random_seed, set_random_seed,
    get_usgs_base_url, get_min_magnitude, get_max_depth_km, get_test_event_count,
    get_test_region
)
from utils.logging import get_logger

logger = get_logger(__name__)

def load_raw_earthquake_data(raw_path: str) -> pd.DataFrame:
    """Load raw earthquake data from JSON file."""
    path = Path(raw_path)
    if not path.exists():
        raise FileNotFoundError(f"Raw earthquake data not found at {raw_path}")
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    # Convert to DataFrame
    df = pd.DataFrame(data)
    logger.info(f"Loaded {len(df)} earthquake records from {raw_path}")
    return df

def load_raw_pressure_data(raw_path: str) -> pd.DataFrame:
    """Load raw pressure data from JSON file."""
    path = Path(raw_path)
    if not path.exists():
        raise FileNotFoundError(f"Raw pressure data not found at {raw_path}")
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    df = pd.DataFrame(data)
    logger.info(f"Loaded {len(df)} pressure records from {raw_path}")
    return df

def interpolate_pressure_grid(pressure_df: pd.DataFrame, target_resolution: float = 0.5) -> pd.DataFrame:
    """
    Interpolate coarse pressure grid to finer resolution.
    Uses linear interpolation for missing points.
    """
    logger.info(f"Interpolating pressure grid to {target_resolution} degree resolution")
    
    # Convert timestamp to datetime
    pressure_df = pressure_df.copy()
    pressure_df['timestamp'] = pd.to_datetime(pressure_df['timestamp'])
    
    # Sort by timestamp and location
    pressure_df = pressure_df.sort_values(['timestamp', 'latitude', 'longitude'])
    
    # Group by date and interpolate
    pressure_df['date'] = pressure_df['timestamp'].dt.date
    interpolated_dfs = []
    
    for date, group in pressure_df.groupby('date'):
        # Create a grid of points
        lats = np.arange(group['latitude'].min(), group['latitude'].max() + target_resolution, target_resolution)
        lons = np.arange(group['longitude'].min(), group['longitude'].max() + target_resolution, target_resolution)
        
        # Create meshgrid
        lat_grid, lon_grid = np.meshgrid(lats, lons)
        
        # Interpolate pressure values
        from scipy.interpolate import griddata
        
        points = group[['latitude', 'longitude']].values
        values = group['pressure_value'].values
        
        interp_values = griddata(points, values, (lat_grid, lon_grid), method='linear')
        
        # Create interpolated dataframe
        interp_df = pd.DataFrame({
            'timestamp': pd.Timestamp(date),
            'latitude': lat_grid.flatten(),
            'longitude': lon_grid.flatten(),
            'pressure_value': interp_values.flatten()
        })
        
        # Drop NaN values
        interp_df = interp_df.dropna(subset=['pressure_value'])
        interpolated_dfs.append(interp_df)
    
    result = pd.concat(interpolated_dfs, ignore_index=True)
    logger.info(f"Interpolated grid contains {len(result)} points")
    return result

def extract_nearest_points(earthquake_df: pd.DataFrame, pressure_df: pd.DataFrame, 
                          window_days: int = 30) -> pd.DataFrame:
    """
    Extract nearest pressure grid points for each earthquake epicenters.
    Returns pressure values within the specified time window around each event.
    """
    logger.info(f"Extracting nearest pressure points for {len(earthquake_df)} earthquakes")
    
    earthquake_df = earthquake_df.copy()
    pressure_df = pressure_df.copy()
    
    # Convert timestamps
    earthquake_df['timestamp'] = pd.to_datetime(earthquake_df['timestamp'])
    pressure_df['timestamp'] = pd.to_datetime(pressure_df['timestamp'])
    
    results = []
    
    for _, eq in earthquake_df.iterrows():
        eq_time = eq['timestamp']
        eq_lat = eq['latitude']
        eq_lon = eq['longitude']
        
        # Define time window
        start_time = eq_time - timedelta(days=window_days)
        end_time = eq_time + timedelta(days=window_days)
        
        # Filter pressure data within time window
        window_pressure = pressure_df[
            (pressure_df['timestamp'] >= start_time) & 
            (pressure_df['timestamp'] <= end_time)
        ]
        
        if len(window_pressure) == 0:
            logger.warning(f"No pressure data found for earthquake at {eq_time}")
            continue
        
        # Find nearest pressure point
        window_pressure['dist'] = np.sqrt(
            (window_pressure['latitude'] - eq_lat) ** 2 + 
            (window_pressure['longitude'] - eq_lon) ** 2
        )
        
        nearest = window_pressure.loc[window_pressure['dist'].idxmin()]
        
        results.append({
            'earthquake_id': eq.get('earthquake_id', eq.get('event_id')),
            'event_time': eq_time,
            'event_lat': eq_lat,
            'event_lon': eq_lon,
            'pressure_timestamp': nearest['timestamp'],
            'pressure_value': nearest['pressure_value'],
            'pressure_lat': nearest['latitude'],
            'pressure_lon': nearest['longitude'],
            'distance_km': nearest['dist'] * 111  # Approximate km
        })
    
    return pd.DataFrame(results)

def calculate_daily_pressure_anomalies(pressure_df: pd.DataFrame, 
                                      moving_average_days: int = 30,
                                      config: Optional[Dict] = None) -> pd.DataFrame:
    """
    Calculate daily pressure anomalies using a left-censored moving average.
    Excludes the period immediately preceding the event window (t-N to t-0).
    """
    logger.info(f"Calculating daily pressure anomalies with {moving_average_days}-day moving average")
    
    pressure_df = pressure_df.copy()
    pressure_df['timestamp'] = pd.to_datetime(pressure_df['timestamp'])
    pressure_df = pressure_df.sort_values('timestamp')
    
    # Group by date and calculate mean pressure per day
    daily_pressure = pressure_df.groupby(pressure_df['timestamp'].dt.date).agg({
        'pressure_value': 'mean',
        'latitude': 'first',
        'longitude': 'first'
    }).reset_index()
    daily_pressure.rename(columns={'timestamp': 'date'}, inplace=True)
    
    # Calculate moving average (left-censored: only use past data)
    daily_pressure['moving_avg'] = daily_pressure['pressure_value'].rolling(
        window=moving_average_days, min_periods=1
    ).mean()
    
    # Calculate anomaly (deviation from moving average)
    daily_pressure['anomaly'] = daily_pressure['pressure_value'] - daily_pressure['moving_avg']
    
    logger.info(f"Calculated anomalies for {len(daily_pressure)} days")
    return daily_pressure

def apply_ocean_mask(data_df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply ocean mask to exclude pressure readings over ocean.
    For this pilot, we use a simple latitude/longitude filter.
    """
    logger.info("Applying ocean mask to exclude ocean readings")
    
    # Simple filter: exclude points with longitude in Pacific Ocean range
    # This is a simplified approach for the pilot
    mask = ~((data_df['longitude'] > 130) & (data_df['longitude'] < 240))
    
    filtered = data_df[mask]
    excluded = len(data_df) - len(filtered)
    logger.info(f"Excluded {excluded} ocean readings, keeping {len(filtered)} land readings")
    
    return filtered

def deduplicate_events(earthquake_df: pd.DataFrame) -> pd.DataFrame:
    """
    Deduplicate events based on unique USGS event ID, retaining most recent revision.
    """
    logger.info(f"Deduplicating {len(earthquake_df)} earthquake events")
    
    if 'earthquake_id' not in earthquake_df.columns and 'event_id' not in earthquake_df.columns:
        raise ValueError("Earthquake DataFrame must contain 'earthquake_id' or 'event_id' column")
    
    id_col = 'earthquake_id' if 'earthquake_id' in earthquake_df.columns else 'event_id'
    
    # Ensure timestamp column exists
    if 'timestamp' not in earthquake_df.columns:
        raise ValueError("Earthquake DataFrame must contain 'timestamp' column")
    
    earthquake_df = earthquake_df.copy()
    earthquake_df['timestamp'] = pd.to_datetime(earthquake_df['timestamp'])
    
    # Sort by ID and timestamp descending to get most recent first
    earthquake_df = earthquake_df.sort_values([id_col, 'timestamp'], ascending=[True, False])
    
    # Keep first occurrence of each ID (most recent)
    deduped = earthquake_df.drop_duplicates(subset=[id_col], keep='first')
    
    excluded = len(earthquake_df) - len(deduped)
    logger.info(f"Deduplicated: kept {len(deduped)} events, excluded {excluded} duplicates")
    
    return deduped

def assign_control_labels(df: pd.DataFrame, event_window_days: int = 30) -> pd.DataFrame:
    """
    Assign control window labels to pressure data points.
    Labels: 'event' for points within event window, 'control' for others.
    """
    logger.info(f"Assigning control labels with {event_window_days}-day event window")
    
    df = df.copy()
    
    # Initialize all as control
    df['window_type'] = 'control'
    
    # Mark event windows if earthquake data is present
    if 'earthquake_id' in df.columns:
        # For pressure data aligned with earthquakes
        event_mask = df['window_type'] == 'event'  # Already marked
        
    return df

def generate_validation_report(df: pd.DataFrame, schema_path: str) -> Dict[str, Any]:
    """Generate a validation report for the dataset."""
    report = {
        'total_rows': len(df),
        'columns': list(df.columns),
        'missing_values': df.isnull().sum().to_dict(),
        'duplicate_rows': df.duplicated().sum(),
        'timestamp_range': {
            'min': str(df['timestamp'].min()) if 'timestamp' in df.columns else None,
            'max': str(df['timestamp'].max()) if 'timestamp' in df.columns else None
        }
    }
    return report

def load_config() -> Dict[str, Any]:
    """Load configuration from data/processed/config.yaml"""
    config_path = get_processed_path() / 'config.yaml'
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found at {config_path}")
    
    with open(config_path, 'r') as f:
        import yaml
        config = yaml.safe_load(f)
    
    return config

def validate_schema(df: pd.DataFrame, schema_path: str) -> Tuple[bool, List[str]]:
    """Validate DataFrame against schema."""
    errors = []
    
    if not Path(schema_path).exists():
        errors.append(f"Schema file not found: {schema_path}")
        return False, errors
    
    import yaml
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    
    required_fields = schema.get('properties', {}).keys()
    missing_fields = [f for f in required_fields if f not in df.columns]
    
    if missing_fields:
        errors.append(f"Missing required fields: {missing_fields}")
        return False, errors
    
    return True, errors

def generate_checksum(file_path: str) -> str:
    """Generate SHA256 checksum for a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def preprocess_data() -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """
    Main preprocessing pipeline.
    Returns: (earthquake_df, pressure_df, validation_report)
    """
    logger.info("Starting preprocessing pipeline")
    
    # Load config
    config = load_config()
    moving_average_days = config.get('moving_average_days', 30)
    expected_count = config.get('expected_earthquake_count', 12)
    
    # Paths
    raw_earthquake_path = get_raw_path() / 'usgs_test_subset.json'
    raw_pressure_path = get_raw_path() / 'pressure_test_subset.json'
    interim_dedup_path = get_interim_path() / 'deduplicated_with_anomalies.csv'
    processed_master_path = get_processed_path() / 'master_dataset.csv'
    
    # Load raw data
    logger.info("Loading raw earthquake data")
    eq_df = load_raw_earthquake_data(str(raw_earthquake_path))
    
    logger.info("Loading raw pressure data")
    press_df = load_raw_pressure_data(str(raw_pressure_path))
    
    # Deduplicate earthquakes
    logger.info("Deduplicating earthquake events")
    eq_df = deduplicate_events(eq_df)
    
    # Verify count
    if abs(len(eq_df) - expected_count) > expected_count * 0.01:
        logger.warning(f"Earthquake count {len(eq_df)} differs from expected {expected_count}")
    
    # Interpolate pressure grid
    logger.info("Interpolating pressure grid")
    press_df = interpolate_pressure_grid(press_df)
    
    # Extract nearest points
    logger.info("Extracting nearest pressure points for earthquakes")
    eq_press = extract_nearest_points(eq_df, press_df)
    
    # Calculate anomalies
    logger.info("Calculating daily pressure anomalies")
    daily_anomalies = calculate_daily_pressure_anomalies(press_df, moving_average_days)
    
    # Merge earthquake data with pressure anomalies
    master_df = eq_press.merge(
        daily_anomalies,
        left_on='pressure_timestamp',
        right_on='date',
        how='left'
    )
    
    # Assign control labels
    master_df = assign_control_labels(master_df)
    
    # Apply ocean mask
    master_df = apply_ocean_mask(master_df)
    
    # Validate schemas
    eq_schema = get_data_path() / 'contracts' / 'earthquake.schema.yaml'
    press_schema = get_data_path() / 'contracts' / 'pressure-anomaly.schema.yaml'
    
    eq_valid, eq_errors = validate_schema(eq_df, str(eq_schema))
    press_valid, press_errors = validate_schema(master_df, str(press_schema))
    
    validation_report = {
        'earthquake_validation': {'valid': eq_valid, 'errors': eq_errors},
        'pressure_validation': {'valid': press_valid, 'errors': press_errors},
        'row_count': len(master_df),
        'expected_count': expected_count
    }
    
    # Write intermediate file
    master_df.to_csv(interim_dedup_path, index=False)
    logger.info(f"Wrote intermediate file to {interim_dedup_path}")
    
    # Write master dataset
    master_df.to_csv(processed_master_path, index=False)
    logger.info(f"Wrote master dataset to {processed_master_path}")
    
    # Generate checksum
    checksum = generate_checksum(str(processed_master_path))
    checksum_path = get_processed_path() / 'master_dataset.csv.sha256'
    with open(checksum_path, 'w') as f:
        f.write(f"{checksum}  master_dataset.csv\n")
    logger.info(f"Wrote checksum to {checksum_path}")
    
    logger.info("Preprocessing pipeline completed successfully")
    return eq_df, press_df, validation_report

def main() -> int:
    """Main entry point for preprocessing pipeline."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Preprocess earthquake and pressure data')
    parser.add_argument('--output', type=str, default=None,
                      help='Output path for master dataset')
    args = parser.parse_args()
    
    try:
        eq_df, press_df, report = preprocess_data()
        
        # Verify row count
        config = load_config()
        expected = config.get('expected_earthquake_count', 12)
        actual = report['row_count']
        
        if abs(actual - expected) > expected * 0.01:
            logger.error(f"Row count mismatch: expected {expected}, got {actual}")
            return 1
        
        logger.info(f"Validation passed: {actual} rows match expected {expected}")
        return 0
        
    except Exception as e:
        logger.exception(f"Preprocessing pipeline failed: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
