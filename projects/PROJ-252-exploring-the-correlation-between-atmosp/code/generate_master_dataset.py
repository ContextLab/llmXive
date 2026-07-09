"""
T017: Generate master dataset pairing earthquakes with pressure anomalies.

This script loads the preprocessed earthquake and pressure data, pairs every
earthquake with its corresponding pressure anomaly and control window label,
and outputs the master dataset to data/processed/master_dataset.csv.

Dependencies:
- code/preprocess.py: Provides load_raw_earthquake_data, load_raw_pressure_data,
  and the processed data structures.
- code/config.py: Provides configuration for paths and window parameters.
"""
import os
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Import from local modules
from config import get_processed_path, get_event_window_days, get_control_window_days
from preprocess import load_raw_earthquake_data, load_raw_pressure_data
from utils.logging import get_logger

logger = get_logger(__name__)

def load_processed_earthquakes() -> pd.DataFrame:
    """
    Load the deduplicated and filtered earthquake data from the processed directory.
    Expects the file 'earthquakes_processed.csv' to exist (output of T016).
    """
    processed_path = get_processed_path()
    earthquake_file = processed_path / "earthquakes_processed.csv"
    
    if not earthquake_file.exists():
        logger.error(f"Processed earthquake file not found: {earthquake_file}")
        logger.error("Please ensure T016 (deduplication) has been completed successfully.")
        raise FileNotFoundError(f"Processed earthquake file not found: {earthquake_file}")
    
    df = pd.read_csv(earthquake_file)
    logger.info(f"Loaded {len(df)} earthquakes from {earthquake_file}")
    return df

def load_processed_pressure_anomalies() -> pd.DataFrame:
    """
    Load the calculated daily pressure anomalies from the processed directory.
    Expects the file 'pressure_anomalies.csv' to exist (output of T014/T015).
    """
    processed_path = get_processed_path()
    anomaly_file = processed_path / "pressure_anomalies.csv"
    
    if not anomaly_file.exists():
        logger.error(f"Processed pressure anomaly file not found: {anomaly_file}")
        logger.error("Please ensure T014/T015 (anomaly calculation and filtering) has been completed.")
        raise FileNotFoundError(f"Processed pressure anomaly file not found: {anomaly_file}")
    
    df = pd.read_csv(anomaly_file)
    logger.info(f"Loaded {len(df)} pressure anomaly records from {anomaly_file}")
    return df

def assign_control_labels(
    earthquakes: pd.DataFrame, 
    anomalies: pd.DataFrame,
    event_window_days: int,
    control_window_days: int
) -> pd.DataFrame:
    """
    Merge earthquake data with pressure anomalies and assign control window labels.
    
    For each earthquake:
    1. Extract the pressure anomaly for the event window (t-N to t-0).
    2. Extract the pressure anomaly for the control window (t-M to t-N).
    3. Label the rows with 'event' or 'control' and the associated event ID.
    """
    if earthquakes.empty:
        logger.warning("No earthquakes to process.")
        return pd.DataFrame()
    
    if anomalies.empty:
        logger.warning("No pressure anomalies to process.")
        return pd.DataFrame()
    
    # Ensure timestamps are datetime objects
    earthquakes['timestamp'] = pd.to_datetime(earthquakes['timestamp'])
    anomalies['timestamp'] = pd.to_datetime(anomalies['timestamp'])
    
    results = []
    
    for _, eq_row in earthquakes.iterrows():
        eq_id = eq_row['id']
        eq_time = eq_row['timestamp']
        eq_lat = eq_row['lat']
        eq_lon = eq_row['lon']
        eq_mag = eq_row['magnitude']
        eq_depth = eq_row['depth']
        
        # Filter anomalies for this specific event location (nearest grid point was already extracted in T013)
        # We assume the 'event_id' column in anomalies links back to the earthquake
        # If the preprocess step didn't add an event_id, we match by lat/lon and time proximity.
        # Based on T013/T014 description, 'extract_nearest_points' should have linked them.
        
        # Strategy: Look for anomalies where event_id matches, or match by lat/lon if ID not present.
        # Assuming preprocess.py added an 'event_id' column to the anomaly dataframe during extraction.
        
        event_anomalies = anomalies[
            (anomalies['event_id'] == eq_id) | 
            ((anomalies['lat'] == eq_lat) & (anomalies['lon'] == eq_lon))
        ]
        
        if event_anomalies.empty:
            logger.warning(f"No pressure data found for earthquake {eq_id}. Skipping.")
            continue
        
        # Define time windows
        # Event window: [eq_time - event_window_days, eq_time]
        event_start = eq_time - pd.Timedelta(days=event_window_days)
        event_end = eq_time
        
        # Control window: [eq_time - event_window_days - control_window_days, eq_time - event_window_days]
        # This is the period immediately preceding the event window
        control_start = event_start - pd.Timedelta(days=control_window_days)
        control_end = event_start
        
        # Extract event window data
        event_data = event_anomalies[
            (event_anomalies['timestamp'] >= event_start) & 
            (event_anomalies['timestamp'] <= event_end)
        ]
        
        # Extract control window data
        control_data = event_anomalies[
            (event_anomalies['timestamp'] >= control_start) & 
            (event_anomalies['timestamp'] <= control_end)
        ]
        
        if event_data.empty and control_data.empty:
            logger.warning(f"No data in event or control windows for earthquake {eq_id}. Skipping.")
            continue
        
        # Create records for event window
        if not event_data.empty:
            for _, row in event_data.iterrows():
                results.append({
                    'event_id': eq_id,
                    'magnitude': eq_mag,
                    'depth': eq_depth,
                    'lat': eq_lat,
                    'lon': eq_lon,
                    'timestamp': row['timestamp'],
                    'pressure_anomaly': row['anomaly_value'], # Adjust column name if different
                    'window_type': 'event',
                    'event_time': eq_time
                })
        
        # Create records for control window
        if not control_data.empty:
            for _, row in control_data.iterrows():
                results.append({
                    'event_id': eq_id,
                    'magnitude': eq_mag,
                    'depth': eq_depth,
                    'lat': eq_lat,
                    'lon': eq_lon,
                    'timestamp': row['timestamp'],
                    'pressure_anomaly': row['anomaly_value'],
                    'window_type': 'control',
                    'event_time': eq_time
                })
    
    if not results:
        logger.error("No paired data could be generated. Check time windows and data alignment.")
        return pd.DataFrame()
        
    master_df = pd.DataFrame(results)
    logger.info(f"Generated master dataset with {len(master_df)} rows.")
    return master_df

def generate_master_dataset():
    """
    Main function to orchestrate the generation of the master dataset.
    """
    logger.info("Starting master dataset generation (T017)...")
    
    # Load data
    earthquakes = load_processed_earthquakes()
    anomalies = load_processed_pressure_anomalies()
    
    if earthquakes.empty or anomalies.empty:
        logger.error("Failed to load necessary data. Aborting.")
        return
    
    # Get configuration
    event_window_days = get_event_window_days()
    control_window_days = get_control_window_days()
    
    logger.info(f"Using event window: {event_window_days} days, control window: {control_window_days} days")
    
    # Generate master dataset
    master_df = assign_control_labels(
        earthquakes, 
        anomalies, 
        event_window_days, 
        control_window_days
    )
    
    if master_df.empty:
        logger.error("Master dataset is empty. Aborting.")
        return
    
    # Save to CSV
    output_path = get_processed_path() / "master_dataset.csv"
    master_df.to_csv(output_path, index=False)
    
    logger.info(f"Master dataset saved to {output_path}")
    logger.info(f"Row count: {len(master_df)}")
    logger.info(f"Columns: {list(master_df.columns)}")
    
    # Basic validation report
    event_count = len(master_df[master_df['window_type'] == 'event'])
    control_count = len(master_df[master_df['window_type'] == 'control'])
    logger.info(f"Event window records: {event_count}")
    logger.info(f"Control window records: {control_count}")
    
    return master_df

def main():
    """Entry point for the script."""
    generate_master_dataset()

if __name__ == "__main__":
    main()