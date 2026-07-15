import os
import csv
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd

# Constants for data paths relative to project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
DATA_RAW_DIR = os.path.join(PROJECT_ROOT, "data", "raw")
ALIGNMENT_WINDOW_DAYS = 3

def load_dst_indices() -> pd.DataFrame:
    """Load Dst indices from the raw data directory."""
    path = os.path.join(DATA_RAW_DIR, "dst_indices.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Dst indices file not found at {path}. Run ingest.py first.")
    df = pd.read_csv(path, parse_dates=['timestamp'])
    return df

def load_flare_data() -> pd.DataFrame:
    """Load flare data from the raw data directory."""
    path = os.path.join(DATA_RAW_DIR, "goes_flares.csv")
    if not os.path.exists(path):
        # Fallback for testing if specific file name differs, but per spec we expect this
        raise FileNotFoundError(f"Flare data file not found at {path}. Run ingest.py first.")
    df = pd.read_csv(path, parse_dates=['timestamp'])
    return df

def load_cme_data() -> pd.DataFrame:
    """Load CME data from the raw data directory."""
    path = os.path.join(DATA_RAW_DIR, "cme_catalog.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(f"CME data file not found at {path}. Run ingest.py first.")
    df = pd.read_csv(path, parse_dates=['timestamp'])
    return df

def find_dst_minima(dst_df: pd.DataFrame, window_hours: int = 6) -> pd.DataFrame:
    """
    Identify local minima in the Dst index representing storm onset.
    A minimum is defined as a point lower than its neighbors within a window.
    """
    # Sort by timestamp
    dst_df = dst_df.sort_values('timestamp').reset_index(drop=True)
    
    minima_indices = []
    values = dst_df['dst'].values
    times = dst_df['timestamp'].values
    
    # Simple local minimum detection
    for i in range(1, len(values) - 1):
        # Check if current is lower than neighbors
        if values[i] < values[i-1] and values[i] < values[i+1]:
            # Further check if it's a significant drop (optional, but good for storms)
            # For now, simple local min
            minima_indices.append(i)
    
    minima_df = dst_df.iloc[minima_indices].copy()
    return minima_df

def match_solar_events(storm_minima: pd.DataFrame, flares_df: pd.DataFrame, cmes_df: pd.DataFrame) -> pd.DataFrame:
    """
    Match solar events (flares and CMEs) to storm minima within a 3-day window.
    """
    matched_records = []
    
    for _, storm in storm_minima.iterrows():
        storm_time = storm['timestamp']
        start_window = storm_time - timedelta(days=ALIGNMENT_WINDOW_DAYS)
        
        # Find matching flares
        matching_flares = flares_df[
            (flares_df['timestamp'] >= start_window) & 
            (flares_df['timestamp'] <= storm_time)
        ]
        
        # Find matching CMEs
        matching_cmes = cmes_df[
            (cmes_df['timestamp'] >= start_window) & 
            (cmes_df['timestamp'] <= storm_time)
        ]
        
        # Select best flare (strongest X-ray flux)
        best_flare = None
        if not matching_flares.empty:
            best_flare = matching_flares.loc[matching_flares['peak_flux'].idxmax()]
        
        # Select best CME (fastest speed)
        best_cme = None
        if not matching_cmes.empty:
            best_cme = matching_cmes.loc[matching_cmes['speed'].idxmax()]
        
        record = {
            'storm_timestamp': storm_time,
            'dst_min': storm['dst'],
            'flare_timestamp': best_flare['timestamp'] if best_flare is not None else None,
            'flare_class': best_flare['class'] if best_flare is not None else None,
            'flare_peak_flux': best_flare['peak_flux'] if best_flare is not None else None,
            'cme_timestamp': best_cme['timestamp'] if best_cme is not None else None,
            'cme_speed': best_cme['speed'] if best_cme is not None else None,
            'cme_width': best_cme['width'] if best_cme is not None else None,
            'cme_direction': best_cme['direction'] if best_cme is not None else None,
            'has_flare': best_flare is not None,
            'has_cme': best_cme is not None
        }
        matched_records.append(record)
        
    return pd.DataFrame(matched_records)

def flag_recurrent_activity(df: pd.DataFrame, recovery_hours: int = 24) -> pd.DataFrame:
    """
    Flag recurrent activity periods.
    Recurrent activity is defined as distinct storm minima separated by < 24 hours of recovery.
    A 'recovery' here implies the time between the end of one storm's active phase and the start of the next.
    Simplified logic: If two storm minima occur within (recovery_hours + some storm duration), they are recurrent.
    Given the data granularity, we treat any two minima separated by less than `recovery_hours` as recurrent.
    """
    df = df.sort_values('storm_timestamp').reset_index(drop=True)
    df['is_recurrent'] = False
    
    if len(df) < 2:
        return df
        
    for i in range(1, len(df)):
        prev_time = df.loc[i-1, 'storm_timestamp']
        curr_time = df.loc[i, 'storm_timestamp']
        
        time_diff = curr_time - prev_time
        
        # If the time difference is less than the recovery threshold
        if time_diff < timedelta(hours=recovery_hours):
            df.loc[i-1, 'is_recurrent'] = True
            df.loc[i, 'is_recurrent'] = True
            
    return df

def align_events() -> pd.DataFrame:
    """
    Main orchestration function to load data, align events, and flag recurrent activity.
    Returns the full aligned dataset with recurrent flags.
    """
    # Load data
    dst_df = load_dst_indices()
    flares_df = load_flare_data()
    cmes_df = load_cme_data()
    
    # Find storm minima
    storm_minima = find_dst_minima(dst_df)
    
    # Match solar events
    aligned_df = match_solar_events(storm_minima, flares_df, cmes_df)
    
    # Flag recurrent activity
    aligned_df = flag_recurrent_activity(aligned_df)
    
    # Ensure timestamps are datetime objects for consistency
    aligned_df['storm_timestamp'] = pd.to_datetime(aligned_df['storm_timestamp'])
    if aligned_df['flare_timestamp'].notna().any():
        aligned_df['flare_timestamp'] = pd.to_datetime(aligned_df['flare_timestamp'])
    if aligned_df['cme_timestamp'].notna().any():
        aligned_df['cme_timestamp'] = pd.to_datetime(aligned_df['cme_timestamp'])
        
    return aligned_df

def main():
    """Entry point for running the alignment process."""
    print("Starting event alignment...")
    try:
        aligned_data = align_events()
        
        # Ensure output directory exists
        os.makedirs(DATA_PROCESSED_DIR, exist_ok=True)
        
        output_path = os.path.join(DATA_PROCESSED_DIR, "aligned_events.csv")
        aligned_data.to_csv(output_path, index=False)
        print(f"Successfully wrote aligned events to {output_path}")
        print(f"Total events: {len(aligned_data)}")
        print(f"Recurrent events flagged: {aligned_data['is_recurrent'].sum()}")
        
    except Exception as e:
        print(f"Error during alignment: {e}")
        raise

if __name__ == "__main__":
    main()