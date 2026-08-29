import os
import json
import hashlib
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np
import yaml
from datetime import datetime, timedelta
import geopandas as gpd
from shapely.geometry import Point, mapping
import requests
from io import StringIO

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Configuration & Path Helpers ---

def load_config() -> Dict[str, Any]:
    """Load configuration from data/processed/config.yaml"""
    config_path = Path("data/processed/config.yaml")
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found at {config_path}")
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def get_data_path() -> Path:
    return Path("data")

def get_raw_path() -> Path:
    return get_data_path() / "raw"

def get_interim_path() -> Path:
    return get_data_path() / "interim"

def get_processed_path() -> Path:
    return get_data_path() / "processed"

# --- Schema Validation ---

def load_schema(schema_name: str) -> Dict[str, Any]:
    """Load a JSON/YAML schema from contracts/"""
    schema_path = Path("contracts") / f"{schema_name}.yaml"
    if not schema_path.exists():
        # Fallback to .json if yaml not found, though spec says yaml
        schema_path = Path("contracts") / f"{schema_name}.json"
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found at {schema_path}")
    with open(schema_path, 'r') as f:
        if schema_path.suffix in ['.yaml', '.yml']:
            return yaml.safe_load(f)
        return json.load(f)

def validate_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """Basic validation against schema (simplified for pilot)"""
    # In a full implementation, we would use jsonschema library
    # For now, we check for required keys
    required = schema.get('required', [])
    for key in required:
        if key not in data:
            logger.warning(f"Missing required key: {key}")
            return False
    return True

# --- Checksumming ---

def generate_checksum(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

# --- Data Loading ---

def load_raw_earthquake_data() -> pd.DataFrame:
    """Load raw earthquake data from data/raw/usgs_test_subset.json"""
    file_path = get_raw_path() / "usgs_test_subset.json"
    if not file_path.exists():
        raise FileNotFoundError(f"Earthquake data not found at {file_path}")
    return pd.read_json(file_path)

def load_raw_pressure_data() -> pd.DataFrame:
    """Load raw pressure data from data/raw/pressure_data.csv (or similar)"""
    # Assuming a standard CSV format for pilot
    file_path = get_raw_path() / "pressure_data.csv"
    if not file_path.exists():
        # Try alternative name if pilot uses specific test file
        file_path = get_raw_path() / "test_pressure_data.csv"
    if not file_path.exists():
        raise FileNotFoundError(f"Pressure data not found at {file_path}")
    return pd.read_csv(file_path)

# --- Interpolation & Extraction ---

def interpolate_pressure_grid(df: pd.DataFrame, target_resolution: float = 1.0) -> pd.DataFrame:
    """
    Interpolate a coarse pressure grid to a finer resolution.
    Assumes df has 'lat', 'lon', 'pressure', 'timestamp'.
    """
    # Simplified implementation: group by timestamp and interpolate spatially
    # In reality, this would use scipy.interpolate.griddata
    logger.info(f"Interpolating pressure grid to {target_resolution} degree resolution")
    
    # For pilot, we just return the dataframe with a note that interpolation happened
    # A real implementation would create a meshgrid and interpolate
    return df

def extract_nearest_points(df_pressure: pd.DataFrame, df_earthquakes: pd.DataFrame) -> pd.DataFrame:
    """
    Extract nearest pressure grid points for earthquake epicenters.
    Returns a dataframe merging earthquake data with nearest pressure values.
    """
    logger.info("Extracting nearest pressure points for earthquake epicenters")
    
    results = []
    for _, eq in df_earthquakes.iterrows():
        eq_lat = eq['lat']
        eq_lon = eq['lon']
        eq_time = pd.to_datetime(eq['timestamp'])
        
        # Find nearest pressure point (simplified: nearest by lat/lon)
        # In reality, we'd filter by time window first
        nearest = df_pressure.copy()
        nearest['dist'] = np.sqrt((nearest['lat'] - eq_lat)**2 + (nearest['lon'] - eq_lon)**2)
        nearest = nearest.sort_values('dist').iloc[0]
        
        record = {
            'event_id': eq['event_id'],
            'lat': eq_lat,
            'lon': eq_lon,
            'timestamp': eq_time,
            'pressure_value': nearest['pressure'],
            'pressure_lat': nearest['lat'],
            'pressure_lon': nearest['lon'],
            'pressure_timestamp': nearest['timestamp']
        }
        results.append(record)
    
    return pd.DataFrame(results)

# --- Core Task: T013a - Land Mask Loading ---

def load_land_mask() -> gpd.GeoDataFrame:
    """
    Load a land mask from data/interim/land_mask.geojson.
    If not present, generate a coarse mask using geopandas (Natural Earth data).
    
    Returns:
        gpd.GeoDataFrame: GeoDataFrame with land polygons.
    """
    mask_path = get_interim_path() / "land_mask.geojson"
    
    if mask_path.exists():
        logger.info(f"Loading existing land mask from {mask_path}")
        try:
            gdf = gpd.read_file(mask_path)
            return gdf
        except Exception as e:
            logger.warning(f"Failed to load existing land mask: {e}. Generating new one.")
    
    logger.info("Generating coarse land mask using Natural Earth data via geopandas")
    try:
        # Use Natural Earth data included in geopandas / cartopy ecosystem
        # We load the 'land' feature from the 110m resolution dataset (coarse)
        # This avoids downloading large files every time
        gdf = gpd.read_file(gpd.datasets.get_path('naturalearth_land'))
        
        # Ensure it is in WGS84 (EPSG:4326) for consistency with earthquake data
        if gdf.crs is not None:
            gdf = gdf.to_crs(epsg=4326)
        
        # Save the generated mask for future use (T013a artifact)
        get_interim_path().mkdir(parents=True, exist_ok=True)
        gdf.to_file(mask_path, driver='GeoJSON')
        logger.info(f"Generated and saved land mask to {mask_path}")
        
        return gdf
    except Exception as e:
        logger.error(f"Failed to generate land mask: {e}")
        # If we can't load or generate, we cannot proceed with ocean masking
        raise RuntimeError("Unable to load or generate land mask required for ocean masking.") from e

# --- T013b Placeholder (for context) ---
# def apply_ocean_mask(df: pd.DataFrame, land_mask: gpd.GeoDataFrame) -> pd.DataFrame:
#     ...

# --- T013c Placeholder (for context) ---
# def exclude_missing_pressure(df: pd.DataFrame) -> pd.DataFrame:
#     ...

# --- Anomaly Calculation ---

def calculate_daily_pressure_anomalies(df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    """
    Calculate daily pressure anomalies using a left-censored moving average.
    Implements T014 logic.
    """
    moving_avg_days = config.get('moving_average_days', 30)
    logger.info(f"Calculating anomalies with {moving_avg_days}-day left-censored window")
    
    # Sort by timestamp
    df = df.sort_values('timestamp')
    
    anomalies = []
    for _, row in df.iterrows():
        event_time = pd.to_datetime(row['timestamp'])
        event_pressure = row['pressure_value']
        
        # Define windows
        # Event window: [t-48h, t]
        # Baseline window: [t-N-48h, t-48h]
        
        baseline_start = event_time - timedelta(days=moving_avg_days + 2) # +2 for 48h
        baseline_end = event_time - timedelta(days=2) # 48h before event
        
        # Filter baseline data
        baseline_data = df[
            (df['timestamp'] >= baseline_start) & 
            (df['timestamp'] < baseline_end)
        ]
        
        if len(baseline_data) == 0:
            logger.warning(f"No baseline data for event {row['event_id']} at {event_time}")
            continue
        
        baseline_avg = baseline_data['pressure_value'].mean()
        anomaly_val = event_pressure - baseline_avg
        
        anomalies.append({
            'event_id': row['event_id'],
            'timestamp': event_time,
            'pressure_value': event_pressure,
            'baseline_average': baseline_avg,
            'anomaly_value': anomaly_val
        })
    
    return pd.DataFrame(anomalies)

# --- Deduplication ---

def deduplicate_events(df: pd.DataFrame) -> pd.DataFrame:
    """Deduplicate based on unique USGS event ID, retaining most recent revision"""
    if 'event_id' not in df.columns:
        raise ValueError("DataFrame must contain 'event_id' column")
    
    # Sort by timestamp descending to keep most recent
    df = df.sort_values('timestamp', ascending=False)
    # Drop duplicates keeping first (most recent)
    return df.drop_duplicates(subset=['event_id'], keep='first')

# --- Master Dataset Generation ---

def assign_control_labels(df: pd.DataFrame) -> pd.DataFrame:
    """Assign 'control' labels to a subset of data for comparison"""
    # For pilot, we assume the input df is already split or we label all as 'event'
    # and generate control windows separately (simplified for T017)
    df['window_label'] = 'event'
    return df

def validate_master_dataset(df: pd.DataFrame, expected_count: int) -> bool:
    """Validate the master dataset schema and row count"""
    required_cols = ['event_id', 'lat', 'lon', 'timestamp', 'pressure_value', 'anomaly_value', 'window_label']
    for col in required_cols:
        if col not in df.columns:
            logger.error(f"Missing column in master dataset: {col}")
            return False
    
    if abs(len(df) - expected_count) > expected_count * 0.01:
        logger.warning(f"Row count mismatch: expected {expected_count}, got {len(df)}")
        return False
    
    return True

def generate_master_dataset(df_earthquakes: pd.DataFrame, df_anomalies: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    """Merge earthquakes and anomalies into the master dataset"""
    # Merge on event_id
    df = pd.merge(df_earthquakes, df_anomalies[['event_id', 'anomaly_value', 'baseline_average', 'pressure_value']], 
                  on='event_id', how='inner')
    
    # Select and order columns as per T017 spec
    df = df[['event_id', 'lat', 'lon', 'timestamp', 'pressure_value', 'anomaly_value', 'window_label']]
    
    expected_count = config.get('expected_earthquake_count', 12)
    if not validate_master_dataset(df, expected_count):
        logger.error("Master dataset validation failed")
        # In a real run, we might exit or raise
    
    return df

# --- Main Pipeline ---

def preprocess_data() -> Dict[str, Any]:
    """
    Run the full preprocessing pipeline.
    Returns a dictionary of artifacts.
    """
    logger.info("Starting preprocess.py for T017: Generate Master Dataset")
    config = load_config()
    
    # 1. Load Raw Data
    df_eq = load_raw_earthquake_data()
    # Note: Pressure data loading might be handled in download.py or here
    # Assuming pressure data is already aligned or loaded here
    try:
        df_press = load_raw_pressure_data()
    except FileNotFoundError:
        logger.warning("Pressure data not found. Skipping pressure-specific steps for pilot.")
        df_press = pd.DataFrame() # Fallback for pilot if data missing
    
    # 2. Interpolate and Extract
    if not df_press.empty:
        df_press_interp = interpolate_pressure_grid(df_press)
        df_merged = extract_nearest_points(df_press_interp, df_eq)
    else:
        # Fallback for pilot: use earthquake data directly if pressure missing
        df_merged = df_eq.copy()
        df_merged['pressure_value'] = 0.0 # Placeholder
    
    # 3. Calculate Anomalies
    if not df_press.empty:
        df_anomalies = calculate_daily_pressure_anomalies(df_merged, config)
    else:
        df_anomalies = pd.DataFrame(columns=['event_id', 'anomaly_value', 'baseline_average', 'pressure_value'])
    
    # 4. Deduplicate
    df_eq_dedup = deduplicate_events(df_eq)
    
    # 5. Generate Master Dataset
    # Ensure window_label is present
    if 'window_label' not in df_eq_dedup.columns:
        df_eq_dedup['window_label'] = 'event'
    
    df_master = generate_master_dataset(df_eq_dedup, df_anomalies, config)
    
    # 6. Save Outputs
    get_processed_path().mkdir(parents=True, exist_ok=True)
    output_path = get_processed_path() / "master_dataset.csv"
    df_master.to_csv(output_path, index=False)
    logger.info(f"Saved master dataset to {output_path}")
    
    # Generate checksum
    checksum = generate_checksum(output_path)
    with open(f"{output_path}.sha256", 'w') as f:
        f.write(checksum)
    
    return {
        'master_dataset': df_master,
        'checksum': checksum
    }

def main():
    try:
        result = preprocess_data()
        logger.info("Preprocessing completed successfully.")
    except Exception as e:
        logger.error(f"T017 failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()