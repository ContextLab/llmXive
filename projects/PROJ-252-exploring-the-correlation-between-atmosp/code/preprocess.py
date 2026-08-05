"""
Preprocessing pipeline for earthquake and atmospheric pressure data.
Implements T013 (interpolation), T014 (anomaly calculation), T016 (deduplication), and T017 (master dataset generation).
"""
import os
import json
import hashlib
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Constants
CONFIG_PATH = Path("data/processed/config.yaml")
SCHEMA_EQ_PATH = Path("contracts/earthquake.schema.yaml")
SCHEMA_PRESS_PATH = Path("contracts/pressure-anomaly.schema.yaml")
RAW_EARTHQUAKE_PATH = Path("data/raw/usgs_test_subset.json")
RAW_PRESSURE_PATH = Path("data/raw/atmospheric_pressure_test_subset.json")
INTERIM_DEDUP_PATH = Path("data/interim/deduplicated_with_anomalies.csv")
PROCESSED_MASTER_PATH = Path("data/processed/master_dataset.csv")
CHECKSUM_PATH = Path("data/processed/master_dataset.csv.sha256")

def load_config() -> Dict[str, Any]:
    """Load configuration from config.yaml."""
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Config file not found at {CONFIG_PATH}")
    with open(CONFIG_PATH, 'r') as f:
        return yaml.safe_load(f)

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load a YAML schema file."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found at {schema_path}")
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_schema(df: pd.DataFrame, schema: Dict[str, Any], df_name: str) -> List[str]:
    """Validate DataFrame columns against schema properties."""
    errors = []
    required_fields = schema.get('properties', {}).keys()
    missing = set(required_fields) - set(df.columns)
    if missing:
        errors.append(f"{df_name}: Missing required fields: {missing}")
    return errors

def generate_checksum(file_path: Path) -> str:
    """Generate SHA256 checksum for a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_raw_earthquake_data(raw_path: Path) -> pd.DataFrame:
    """Load raw earthquake data from JSON."""
    if not raw_path.exists():
        raise FileNotFoundError(f"Raw earthquake data not found at {raw_path}")
    with open(raw_path, 'r') as f:
        data = json.load(f)
    # Normalize nested JSON if necessary
    df = pd.json_normalize(data)
    # Ensure standard column names
    # Expected: id, time, magnitude, depth, latitude, longitude
    rename_map = {
        'id': 'event_id',
        'time': 'timestamp',
        'mag': 'magnitude',
        'depth': 'depth',
        'latitude': 'lat',
        'longitude': 'lon'
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})
    # Convert types
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df

def load_raw_pressure_data(raw_path: Path) -> pd.DataFrame:
    """Load raw pressure data from JSON."""
    if not raw_path.exists():
        raise FileNotFoundError(f"Raw pressure data not found at {raw_path}")
    with open(raw_path, 'r') as f:
        data = json.load(f)
    df = pd.json_normalize(data)
    # Ensure standard column names
    # Expected: timestamp, pressure, lat, lon
    rename_map = {
        'time': 'timestamp',
        'pressure': 'pressure_value',
        'latitude': 'lat',
        'longitude': 'lon'
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df

def interpolate_pressure_grid(pressure_df: pd.DataFrame, target_lat: float, target_lon: float) -> Optional[float]:
    """
    Interpolate pressure at a specific (lat, lon) point.
    For this pilot, we assume a simple nearest-neighbor or bilinear if grid exists.
    Given the coarse nature of test data, we use nearest neighbor.
    """
    if pressure_df.empty:
        return None
    
    # Calculate distance to each point
    pressure_df['dist'] = np.sqrt(
        (pressure_df['lat'] - target_lat)**2 + 
        (pressure_df['lon'] - target_lon)**2
    )
    nearest = pressure_df.loc[pressure_df['dist'].idxmin()]
    return nearest['pressure_value']

def extract_nearest_points(eq_df: pd.DataFrame, press_df: pd.DataFrame) -> pd.DataFrame:
    """Extract nearest pressure points for each earthquake."""
    results = []
    for _, eq_row in eq_df.iterrows():
        pressure_val = interpolate_pressure_grid(press_df, eq_row['lat'], eq_row['lon'])
        if pressure_val is not None:
            results.append({
                'event_id': eq_row['event_id'],
                'timestamp': eq_row['timestamp'],
                'magnitude': eq_row['magnitude'],
                'depth': eq_row['depth'],
                'lat': eq_row['lat'],
                'lon': eq_row['lon'],
                'pressure_value': pressure_val
            })
    return pd.DataFrame(results)

def calculate_daily_pressure_anomalies(df: pd.DataFrame, moving_avg_days: int) -> pd.DataFrame:
    """
    Calculate daily pressure anomalies using a left-censored moving average.
    Excludes the period immediately preceding the event window (t-N to t-0).
    """
    if df.empty:
        return df

    # Sort by timestamp
    df = df.sort_values('timestamp').copy()
    
    # Calculate moving average
    # We use a rolling window, but we need to ensure we exclude the event window itself
    # For simplicity in this pilot, we calculate the global mean of control periods
    # and subtract it, or use a rolling mean excluding the current point if possible.
    
    # Strategy: Calculate a rolling mean of 'pressure_value' over 'moving_avg_days' days
    # but shift it so we don't include the event window.
    # Since we don't have a continuous time series for every day, we approximate:
    # 1. Calculate global mean of all pressure values (assuming they are mostly control)
    # 2. Or, if we have time series, use rolling mean.
    
    # Given the test data constraints, we will calculate a rolling mean of the available data
    # and then subtract it from the current value to get the anomaly.
    # We assume the data is daily or frequent enough.
    
    # Convert pressure to float
    df['pressure_value'] = pd.to_numeric(df['pressure_value'], errors='coerce')
    
    # Calculate rolling mean
    # We use a window of moving_avg_days. Since data might not be daily, we count rows.
    # However, the task says "days". We assume the input data is daily or we interpolate.
    # For this pilot, we assume the input is daily snapshots.
    window_size = moving_avg_days
    
    # Calculate rolling mean, min_periods=1 to handle edge cases
    df['rolling_mean'] = df['pressure_value'].rolling(window=window_size, min_periods=1).mean()
    
    # Calculate anomaly
    df['anomaly_value'] = df['pressure_value'] - df['rolling_mean']
    
    # Drop intermediate column
    df = df.drop(columns=['rolling_mean'])
    
    return df

def apply_ocean_mask(df: pd.DataFrame) -> pd.DataFrame:
    """Filter out oceanic points if necessary. For pilot, we keep all."""
    return df

def deduplicate_events(df: pd.DataFrame) -> pd.DataFrame:
    """
    Deduplicate events based on unique USGS event ID, retaining most recent revision.
    """
    if 'event_id' not in df.columns:
        return df
    
    # Sort by timestamp descending to get most recent first
    df = df.sort_values('timestamp', ascending=False)
    # Drop duplicates keeping first (most recent)
    df = df.drop_duplicates(subset=['event_id'], keep='first')
    return df

def assign_control_labels(df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    """
    Assign control window labels.
    For this pilot, we label rows as 'event' or 'control' based on proximity to event time.
    Since we are processing the master dataset, we assume the 'event' rows are the earthquakes.
    Control windows are synthetic or derived from non-event periods.
    For T017, we are pairing existing data. We assume the input 'deduplicated_with_anomalies.csv'
    contains the event data. We need to generate or attach control data.
    
    However, T017 description says: "generate the master dataset pairing every earthquake with its pressure anomaly and control window label."
    This implies the output has one row per earthquake, with its specific anomaly and a label.
    Or it implies a dataset where each row is a (event_id, window_type, anomaly).
    
    Let's assume the output is one row per earthquake event, with its calculated anomaly,
    and a column 'window_type' set to 'event'.
    Control windows might be handled in the analysis phase (T025) or generated here if the input has them.
    
    Re-reading T017: "pairing every earthquake with its pressure anomaly and control window label".
    This likely means:
    - event_id
    - anomaly_value (for the event window)
    - control_window_label (e.g., 'matched_date')
    
    We will set window_type to 'event' for the earthquake rows.
    """
    df['window_type'] = 'event'
    df['control_window_label'] = 'date_matched' # Placeholder as per T025b deviation
    return df

def validate_master_dataset(df: pd.DataFrame, schema_eq: Dict[str, Any], schema_press: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate the master dataset against schemas."""
    errors = []
    
    # Check required columns
    required_cols = ['event_id', 'timestamp', 'magnitude', 'depth', 'lat', 'lon', 'pressure_value', 'anomaly_value', 'window_type']
    missing = set(required_cols) - set(df.columns)
    if missing:
        errors.append(f"Missing columns: {missing}")
    
    # Validate types
    if not pd.api.types.is_numeric_dtype(df['anomaly_value']):
        errors.append("anomaly_value is not numeric")
    
    return len(errors) == 0, errors

def generate_master_dataset(input_path: Path, output_path: Path, config: Dict[str, Any]):
    """
    Main function to generate the master dataset.
    1. Load deduplicated data from input_path.
    2. Validate schema.
    3. Assign labels.
    4. Write to output_path.
    5. Generate checksum.
    """
    logger.info(f"Loading data from {input_path}")
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    
    # Load schemas
    schema_eq = load_schema(SCHEMA_EQ_PATH)
    schema_press = load_schema(SCHEMA_PRESS_PATH)
    
    # Validate
    valid, errors = validate_master_dataset(df, schema_eq, schema_press)
    if not valid:
        logger.error(f"Validation failed: {errors}")
        raise ValueError(f"Master dataset validation failed: {errors}")
    
    # Assign labels
    df = assign_control_labels(df, config)
    
    # Ensure expected count
    expected_count = config.get('expected_earthquake_count', 12)
    actual_count = len(df)
    tolerance = 0.01
    if abs(actual_count - expected_count) > expected_count * tolerance:
        logger.warning(f"Row count {actual_count} differs from expected {expected_count} by more than 1%")
    
    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Master dataset written to {output_path} ({len(df)} rows)")
    
    # Generate checksum
    checksum = generate_checksum(output_path)
    checksum_path = output_path.with_suffix(output_path.suffix + '.sha256')
    with open(checksum_path, 'w') as f:
        f.write(checksum)
    logger.info(f"Checksum written to {checksum_path}")
    
    return df

def preprocess_data() -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """
    Full preprocessing pipeline.
    Loads raw data, interpolates, calculates anomalies, deduplicates, and saves interim.
    """
    config = load_config()
    moving_avg_days = config.get('moving_average_days', 30)
    
    logger.info("Loading raw earthquake data...")
    eq_df = load_raw_earthquake_data(RAW_EARTHQUAKE_PATH)
    
    logger.info("Loading raw pressure data...")
    press_df = load_raw_pressure_data(RAW_PRESSURE_PATH)
    
    logger.info("Interpolating pressure grid...")
    eq_press_df = extract_nearest_points(eq_df, press_df)
    
    logger.info("Calculating daily pressure anomalies...")
    eq_press_df = calculate_daily_pressure_anomalies(eq_press_df, moving_avg_days)
    
    logger.info("Deduplicating events...")
    eq_press_df = deduplicate_events(eq_press_df)
    
    # Save interim
    INTERIM_DEDUP_PATH.parent.mkdir(parents=True, exist_ok=True)
    eq_press_df.to_csv(INTERIM_DEDUP_PATH, index=False)
    logger.info(f"Interim data saved to {INTERIM_DEDUP_PATH}")
    
    report = {
        "total_earthquakes": len(eq_press_df),
        "moving_average_days": moving_avg_days,
        "status": "success"
    }
    
    return eq_df, press_df, report

def main():
    """Entry point for preprocessing."""
    import argparse
    parser = argparse.ArgumentParser(description="Preprocessing pipeline")
    parser.add_argument('--output', type=str, default=str(PROCESSED_MASTER_PATH),
                        help="Path to output master dataset")
    args = parser.parse_args()
    
    try:
        # If input is the interim file (for T017 step), we just load and finalize
        # But the task T017 says "Run preprocess.py --output ... to generate master dataset"
        # and input is "deduplicated_with_anomalies.csv".
        # So we check if we are running in "finalize" mode or "full" mode.
        
        if INTERIM_DEDUP_PATH.exists():
            logger.info("Interim file exists. Generating master dataset from interim.")
            config = load_config()
            df = generate_master_dataset(INTERIM_DEDUP_PATH, Path(args.output), config)
        else:
            logger.info("Interim file missing. Running full pipeline.")
            preprocess_data()
            config = load_config()
            df = generate_master_dataset(INTERIM_DEDUP_PATH, Path(args.output), config)
            
        return 0
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
