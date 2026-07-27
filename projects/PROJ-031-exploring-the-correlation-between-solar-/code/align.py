import os
import csv
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd

def load_dst_indices(filepath: str = "data/raw/dst_indices.csv") -> pd.DataFrame:
    """Load Dst indices from CSV."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Dst indices file not found: {filepath}")
    df = pd.read_csv(filepath)
    df['time'] = pd.to_datetime(df['time'])
    return df

def load_flare_data(filepath: str = "data/raw/goes_flares.csv") -> pd.DataFrame:
    """Load GOES flare data from CSV."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Flare data file not found: {filepath}")
    df = pd.read_csv(filepath)
    df['time'] = pd.to_datetime(df['time'])
    return df

def load_cme_data(filepath: str = "data/raw/lasco_cmes.csv") -> pd.DataFrame:
    """Load LASCO CME data from CSV."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"CME data file not found: {filepath}")
    df = pd.read_csv(filepath)
    df['time'] = pd.to_datetime(df['time'])
    return df

def find_dst_minima(dst_df: pd.DataFrame, window_hours: int = 24) -> pd.DataFrame:
    """Identify local minima in Dst index (storm events)."""
    # Sort by time
    dst_df = dst_df.sort_values('time').reset_index(drop=True)
    
    # Find local minima
    minima_indices = []
    for i in range(1, len(dst_df) - 1):
        if dst_df.iloc[i]['dst'] < dst_df.iloc[i-1]['dst'] and \
           dst_df.iloc[i]['dst'] < dst_df.iloc[i+1]['dst']:
            minima_indices.append(i)
    
    # Create minima dataframe
    minima_df = dst_df.iloc[minima_indices].copy()
    minima_df = minima_df.rename(columns={'dst': 'dst_min'})
    
    return minima_df

def match_solar_events(
    storm_df: pd.DataFrame,
    flare_df: pd.DataFrame,
    cme_df: pd.DataFrame,
    max_days: int = 3
) -> List[Dict[str, Any]]:
    """Match solar events to storms within a time window."""
    aligned_events = []
    
    for _, storm in storm_df.iterrows():
        storm_time = storm['time']
        flare_time = None
        flare_class = None
        flare_flux = None
        cme_time = None
        cme_speed = None
        cme_width = None
        cme_direction = None
        has_missing = False
        
        # Find preceding flare within window
        flare_window_start = storm_time - timedelta(days=max_days)
        flare_candidates = flare_df[
            (flare_df['time'] >= flare_window_start) & 
            (flare_df['time'] <= storm_time)
        ]
        
        if not flare_candidates.empty:
            # Take the most recent flare before the storm
            latest_flare = flare_candidates.sort_values('time').iloc[-1]
            flare_time = latest_flare['time']
            flare_class = latest_flare.get('class', None)
            flare_flux = latest_flare.get('flux', None)
            if flare_flux is None:
                has_missing = True
        else:
            has_missing = True
        
        # Find preceding CME within window
        cme_window_start = storm_time - timedelta(days=max_days)
        cme_candidates = cme_df[
            (cme_df['time'] >= cme_window_start) & 
            (cme_df['time'] <= storm_time)
        ]
        
        if not cme_candidates.empty:
            # Take the most recent CME before the storm
            latest_cme = cme_candidates.sort_values('time').iloc[-1]
            cme_time = latest_cme['time']
            cme_speed = latest_cme.get('speed', None)
            cme_width = latest_cme.get('width', None)
            cme_direction = latest_cme.get('source', None)
            if cme_speed is None:
                has_missing = True
        else:
            has_missing = True
        
        # Calculate alignment window days
        if flare_time:
            alignment_days = (storm_time - flare_time).days
        else:
            alignment_days = max_days + 1  # Out of window
        
        event = {
            'storm_id': f"STORM_{int(storm_time.timestamp())}",
            'storm_time': storm_time,
            'dst_min': storm['dst_min'],
            'flare_time': flare_time,
            'flare_class': flare_class,
            'flare_flux': flare_flux,
            'cme_time': cme_time,
            'cme_speed': cme_speed,
            'cme_width': cme_width,
            'cme_direction': cme_direction,
            'alignment_window_days': alignment_days,
            'is_recurrent': False,  # Will be updated by flag_recurrent_activity
            'has_missing_predictors': has_missing
        }
        
        aligned_events.append(event)
    
    return aligned_events

def flag_recurrent_activity(events: List[Dict[str, Any]], recovery_hours: int = 24) -> List[Dict[str, Any]]:
    """Flag recurrent activity periods (storms < 24h apart)."""
    if not events:
        return events
    
    # Sort by storm time
    sorted_events = sorted(events, key=lambda x: x['storm_time'])
    
    for i in range(1, len(sorted_events)):
        prev_time = sorted_events[i-1]['storm_time']
        curr_time = sorted_events[i]['storm_time']
        time_diff = (curr_time - prev_time).total_seconds() / 3600  # hours
        
        # If less than recovery_hours and previous storm was significant
        if time_diff < recovery_hours:
            # Check if previous storm was significant (Dst <= -50 nT)
            if sorted_events[i-1]['dst_min'] <= -50:
                sorted_events[i-1]['is_recurrent'] = True
                sorted_events[i]['is_recurrent'] = True
    
    return sorted_events

def align_events(
    dst_path: str = "data/raw/dst_indices.csv",
    flare_path: str = "data/raw/goes_flares.csv",
    cme_path: str = "data/raw/lasco_cmes.csv",
    output_path: str = "data/processed/aligned_events.csv"
) -> pd.DataFrame:
    """Main function to align solar events with geomagnetic storms."""
    # Load data
    dst_df = load_dst_indices(dst_path)
    flare_df = load_flare_data(flare_path)
    cme_df = load_cme_data(cme_path)
    
    # Find storm minima
    storm_df = find_dst_minima(dst_df)
    print(f"Found {len(storm_df)} storm events")
    
    # Match solar events
    aligned_events = match_solar_events(storm_df, flare_df, cme_df)
    print(f"Matched {len(aligned_events)} events")
    
    # Flag recurrent activity
    aligned_events = flag_recurrent_activity(aligned_events)
    
    # Convert to DataFrame
    df = pd.DataFrame(aligned_events)
    
    # Format datetime columns for CSV
    for col in ['storm_time', 'flare_time', 'cme_time']:
        if col in df.columns:
            df[col] = df[col].dt.strftime('%Y-%m-%dT%H:%M:%S')
    
    # Save to CSV
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Saved aligned events to {output_path}")
    
    return df

def main():
    """Main entry point for alignment."""
    align_events()

if __name__ == "__main__":
    main()
