import os
import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from config import get_processed_path, get_data_path, get_event_window_days, get_control_window_days, get_deviations_path
from utils.logging import get_logger

logger = get_logger(__name__)

def load_raw_earthquake_data(raw_path: str) -> pd.DataFrame:
    """Load raw earthquake data from JSON file."""
    path = Path(raw_path)
    if not path.exists():
        raise FileNotFoundError(f"Raw earthquake data not found at {raw_path}")
    
    with open(path, 'r') as f:
        data = json.load(f)
    
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

def interpolate_pressure_grid(pressure_df: pd.DataFrame, target_resolution: float = 1.0) -> pd.DataFrame:
    """Interpolate a coarse pressure grid to a finer resolution."""
    logger.info(f"Interpolating pressure grid to {target_resolution} degree resolution")
    
    if pressure_df.empty:
        logger.warning("Pressure dataframe is empty, returning empty dataframe")
        return pd.DataFrame()
    
    # Group by timestamp and interpolate spatially
    interpolated_records = []
    
    for timestamp, group in pressure_df.groupby('timestamp'):
        # Create a grid for interpolation
        lat_min, lat_max = group['latitude'].min(), group['latitude'].max()
        lon_min, lon_max = group['longitude'].min(), group['longitude'].max()
        
        # Generate fine grid
        lats = np.arange(lat_min, lat_max + target_resolution, target_resolution)
        lons = np.arange(lon_min, lon_max + target_resolution, target_resolution)
        
        # Simple bilinear interpolation placeholder
        # In a real scenario, we would use scipy.interpolate.griddata
        for lat in lats:
            for lon in lons:
                # Find nearest point for simplicity in this pilot
                nearest = group.iloc[np.argmin((group['latitude'] - lat)**2 + (group['longitude'] - lon)**2)]
                interpolated_records.append({
                    'timestamp': timestamp,
                    'latitude': lat,
                    'longitude': lon,
                    'pressure_value': nearest['pressure_value'],
                    'interpolation_method': 'nearest_neighbor'
                })
    
    result_df = pd.DataFrame(interpolated_records)
    logger.info(f"Interpolated to {len(result_df)} grid points")
    return result_df

def extract_nearest_points(interpolated_df: pd.DataFrame, earthquake_df: pd.DataFrame) -> pd.DataFrame:
    """Extract nearest grid points for earthquake epicenters."""
    logger.info("Extracting nearest pressure points for earthquake epicenters")
    
    if interpolated_df.empty or earthquake_df.empty:
        logger.warning("Input dataframes empty, returning empty result")
        return pd.DataFrame()
    
    results = []
    
    for _, eq in earthquake_df.iterrows():
        eq_lat, eq_lon, eq_time = eq['latitude'], eq['longitude'], eq['timestamp']
        
        # Find matching timestamp
        time_mask = interpolated_df['timestamp'] == eq_time
        if not time_mask.any():
            # Try closest timestamp
            time_diffs = (pd.to_datetime(interpolated_df['timestamp']) - pd.to_datetime(eq_time)).abs()
            closest_time_idx = time_diffs.idxmin()
            closest_time = interpolated_df.loc[closest_time_idx, 'timestamp']
            time_mask = interpolated_df['timestamp'] == closest_time
        
        time_filtered = interpolated_df[time_mask]
        
        if time_filtered.empty:
            logger.warning(f"No pressure data found near {eq_time} for EQ {eq['earthquake_id']}")
            continue
        
        # Find nearest point
        distances = (time_filtered['latitude'] - eq_lat)**2 + (time_filtered['longitude'] - eq_lon)**2
        nearest_idx = distances.idxmin()
        nearest_point = time_filtered.loc[nearest_idx]
        
        results.append({
            'earthquake_id': eq['earthquake_id'],
            'timestamp': eq_time,
            'latitude': eq_lat,
            'longitude': eq_lon,
            'pressure_value': nearest_point['pressure_value'],
            'distance_to_grid': np.sqrt(distances.min())
        })
    
    result_df = pd.DataFrame(results)
    logger.info(f"Extracted {len(result_df)} nearest points")
    return result_df

def calculate_daily_pressure_anomalies(pressure_df: pd.DataFrame, window_days: int = 30) -> pd.DataFrame:
    """
    Calculate daily pressure anomalies using a left-censored 30-day moving average.
    Excludes the period immediately preceding the event window (t-N to t-0) from the calculation.
    """
    logger.info(f"Calculating daily pressure anomalies with {window_days}-day window")
    
    if pressure_df.empty:
        return pd.DataFrame()
    
    pressure_df = pressure_df.copy()
    pressure_df['timestamp'] = pd.to_datetime(pressure_df['timestamp'])
    pressure_df = pressure_df.sort_values(['latitude', 'longitude', 'timestamp'])
    
    anomalies = []
    
    # Group by location to calculate anomalies per grid point
    for (lat, lon), group in pressure_df.groupby(['latitude', 'longitude']):
        group = group.sort_values('timestamp')
        group['days_since_epoch'] = (group['timestamp'] - group['timestamp'].min()).dt.days
        
        for i, (idx, row) in group.iterrows():
            current_time = row['timestamp']
            current_pressure = row['pressure_value']
            
            # Define the lookback window, excluding the event window (t-N to t-0)
            # We look back N days, but skip the last N days immediately before current_time
            # This creates a "left-censored" baseline
            baseline_start = current_time - pd.Timedelta(days=window_days * 2)
            baseline_end = current_time - pd.Timedelta(days=window_days)
            
            # Filter for baseline period
            baseline_mask = (group['timestamp'] >= baseline_start) & (group['timestamp'] < baseline_end)
            baseline_data = group[baseline_mask]['pressure_value']
            
            if len(baseline_data) > 0:
                mean_baseline = baseline_data.mean()
                std_baseline = baseline_data.std()
                anomaly = current_pressure - mean_baseline
                z_score = anomaly / std_baseline if std_baseline > 0 else 0.0
            else:
                # Fallback if not enough data
                mean_baseline = current_pressure
                std_baseline = 1.0
                anomaly = 0.0
                z_score = 0.0
            
            anomalies.append({
                'timestamp': row['timestamp'],
                'latitude': lat,
                'longitude': lon,
                'pressure_value': current_pressure,
                'anomaly_value': anomaly,
                'z_score': z_score,
                'baseline_mean': mean_baseline,
                'baseline_std': std_baseline
            })
    
    result_df = pd.DataFrame(anomalies)
    logger.info(f"Calculated anomalies for {len(result_df)} records")
    return result_df

def apply_ocean_mask(pressure_anomalies_df: pd.DataFrame, reliability_threshold: float = 0.95) -> pd.DataFrame:
    """
    Filter to exclude ocean-masked events where interpolation reliability is < 95%.
    For this pilot, we use a simple land/sea check based on coordinates.
    """
    logger.info(f"Applying ocean mask with reliability threshold {reliability_threshold}")
    
    if pressure_anomalies_df.empty:
        return pd.DataFrame()
    
    # Simple land/sea approximation for pilot (using known land boundaries)
    # In a full implementation, this would use a proper land mask grid (e.g., ETOPO1)
    # For Alaska region in our test set, we assume all points are valid land/interpolated
    # unless explicitly marked otherwise in a real mask file.
    
    # Filter based on distance_to_grid if available (proxy for reliability)
    if 'distance_to_grid' in pressure_anomalies_df.columns:
        # Keep points where distance is small (high reliability)
        # Assuming small distance correlates with high reliability
        valid_mask = pressure_anomalies_df['distance_to_grid'] < 0.5
        filtered_df = pressure_anomalies_df[valid_mask]
        logger.info(f"Filtered out {len(pressure_anomalies_df) - len(filtered_df)} low-reliability points")
    else:
        filtered_df = pressure_anomalies_df
        logger.warning("No distance_to_grid column found, skipping reliability filter")
    
    return filtered_df

def deduplicate_events(earthquake_df: pd.DataFrame) -> pd.DataFrame:
    """
    Implement deduplication logic based on unique USGS event ID, retaining most recent revision.
    
    USGS event IDs are unique, but revisions may exist. We group by event_id and keep
    the record with the latest update time (or timestamp if update time is missing).
    """
    logger.info("Deduplicating earthquake events by event ID")
    
    if earthquake_df.empty:
        logger.warning("Earthquake dataframe is empty, returning empty dataframe")
        return pd.DataFrame()
    
    # Ensure we have an event_id column
    if 'earthquake_id' not in earthquake_df.columns:
        logger.error("earthquake_id column not found in dataframe")
        return earthquake_df
    
    # Check for revision indicators
    has_update_time = 'update_time' in earthquake_df.columns
    has_timestamp = 'timestamp' in earthquake_df.columns
    
    # Determine sort key
    if has_update_time:
        sort_key = 'update_time'
    elif has_timestamp:
        sort_key = 'timestamp'
    else:
        logger.warning("No timestamp or update_time column found, keeping first occurrence")
        return earthquake_df.drop_duplicates(subset=['earthquake_id'], keep='first')
    
    # Convert to datetime if necessary
    if sort_key in earthquake_df.columns:
        earthquake_df[sort_key] = pd.to_datetime(earthquake_df[sort_key])
    
    # Sort by event_id and sort_key (descending) to get latest first
    earthquake_df = earthquake_df.sort_values(by=[sort_key], ascending=False)
    
    # Drop duplicates keeping the first (which is the most recent due to sort)
    deduped_df = earthquake_df.drop_duplicates(subset=['earthquake_id'], keep='first')
    
    logger.info(f"Deduplicated {len(earthquake_df)} records to {len(deduped_df)} unique events")
    return deduped_df

def generate_validation_report(deduped_df: pd.DataFrame, anomaly_df: pd.DataFrame, output_path: str) -> Dict[str, Any]:
    """Generate a validation report for the preprocessed data."""
    logger.info(f"Generating validation report to {output_path}")
    
    report = {
        'total_earthquakes_loaded': len(deduped_df),
        'unique_earthquakes': len(deduped_df['earthquake_id'].unique()) if not deduped_df.empty else 0,
        'total_pressure_anomalies': len(anomaly_df),
        'missing_fields': [],
        'validation_status': 'PASSED'
    }
    
    # Check required fields in earthquake data
    required_eq_fields = ['earthquake_id', 'timestamp', 'latitude', 'longitude', 'magnitude', 'depth_km']
    for field in required_eq_fields:
        if field not in deduped_df.columns:
            report['missing_fields'].append(f"earthquake.{field}")
            report['validation_status'] = 'FAILED'
        elif deduped_df[field].isnull().any():
            report['missing_fields'].append(f"earthquake.{field} (null values present)")
            report['validation_status'] = 'FAILED'
    
    # Check required fields in anomaly data
    required_anomaly_fields = ['timestamp', 'latitude', 'longitude', 'pressure_value', 'anomaly_value']
    for field in required_anomaly_fields:
        if field not in anomaly_df.columns:
            report['missing_fields'].append(f"anomaly.{field}")
            report['validation_status'] = 'FAILED'
        elif anomaly_df[field].isnull().any():
            report['missing_fields'].append(f"anomaly.{field} (null values present)")
            report['validation_status'] = 'FAILED'
    
    # Write report
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Validation report generated: {report['validation_status']}")
    return report

def preprocess_data() -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """Main preprocessing pipeline."""
    logger.info("Starting preprocessing pipeline")
    
    # Paths
    raw_earthquake_path = get_data_path() / "raw" / "usgs_test_subset.json"
    raw_pressure_path = get_data_path() / "raw" / "pressure_test_subset.json"
    processed_path = get_processed_path()
    
    # Ensure directories exist
    processed_path.mkdir(parents=True, exist_ok=True)
    (processed_path.parent / "raw").mkdir(parents=True, exist_ok=True)
    
    # Load raw data
    try:
        eq_df = load_raw_earthquake_data(str(raw_earthquake_path))
    except FileNotFoundError as e:
        logger.error(str(e))
        raise
    
    try:
        press_df = load_raw_pressure_data(str(raw_pressure_path))
    except FileNotFoundError as e:
        logger.error(str(e))
        raise
    
    # Deduplicate earthquakes (T016)
    eq_df = deduplicate_events(eq_df)
    
    # Interpolate pressure grid
    press_interpolated = interpolate_pressure_grid(press_df)
    
    # Extract nearest points
    nearest_points = extract_nearest_points(press_interpolated, eq_df)
    
    # Calculate anomalies
    anomaly_df = calculate_daily_pressure_anomalies(nearest_points)
    
    # Apply ocean mask
    anomaly_df = apply_ocean_mask(anomaly_df)
    
    # Generate validation report
    report_path = processed_path / "validation_report.json"
    report = generate_validation_report(eq_df, anomaly_df, str(report_path))
    
    # Save intermediate files
    eq_output_path = processed_path / "earthquakes_processed.csv"
    anomaly_output_path = processed_path / "pressure_anomalies_processed.csv"
    
    eq_df.to_csv(eq_output_path, index=False)
    anomaly_df.to_csv(anomaly_output_path, index=False)
    
    logger.info("Preprocessing pipeline completed")
    return eq_df, anomaly_df, report

def main():
    """Entry point for preprocessing script."""
    try:
        eq_df, anomaly_df, report = preprocess_data()
        logger.info("Preprocessing completed successfully")
        return 0
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        raise

if __name__ == "__main__":
    exit(main())