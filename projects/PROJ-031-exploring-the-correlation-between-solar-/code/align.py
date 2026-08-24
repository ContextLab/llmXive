"""
Solar Flare and Geomagnetic Storm Alignment Module.

This module handles the alignment of solar eruption events (flares, CMEs)
with geomagnetic storm events (Dst minima) within a specified time window.
It implements logic to flag missing solar predictors and handle cases where
no matching solar event is found for a storm, without excluding the storm
from the dataset.
"""

import os
import csv
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd

# Constants
ALIGNMENT_WINDOW_DAYS = 3
Dst_THRESHOLD_STORM = -50  # nT, typical storm threshold
Dst_THRESHOLD_SEVERE = -100  # nT, severe storm threshold
MISSING_FLAG = None  # Use None for missing values to be handled by pandas

def load_aligned_events(filepath: str) -> pd.DataFrame:
    """
    Load aligned events from a CSV file.

    Args:
        filepath: Path to the CSV file.

    Returns:
        DataFrame containing the aligned events.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    return pd.read_csv(filepath)

def align_events(
    flare_df: pd.DataFrame,
    cme_df: pd.DataFrame,
    dst_df: pd.DataFrame,
    kp_df: pd.DataFrame,
    window_days: int = ALIGNMENT_WINDOW_DAYS
) -> pd.DataFrame:
    """
    Align solar events (flares, CMEs) with geomagnetic storms (Dst minima).

    This function identifies Dst minima (storms) and matches them with
    preceding solar events within a specified time window. It handles
    cases where no match is found or data is missing by flagging them
    appropriately rather than excluding the event.

    Args:
        flare_df: DataFrame containing flare data.
        cme_df: DataFrame containing CME data.
        dst_df: DataFrame containing Dst index data.
        kp_df: DataFrame containing Kp index data.
        window_days: Time window in days to search for matching solar events.

    Returns:
        DataFrame containing aligned events with flags for missing data.
    """
    # Ensure date columns are datetime
    if 'time' in flare_df.columns:
        flare_df['time'] = pd.to_datetime(flare_df['time'])
    if 'time' in cme_df.columns:
        cme_df['time'] = pd.to_datetime(cme_df['time'])
    if 'time' in dst_df.columns:
        dst_df['time'] = pd.to_datetime(dst_df['time'])
    if 'time' in kp_df.columns:
        kp_df['time'] = pd.to_datetime(kp_df['time'])

    # Identify storms (Dst minima below threshold)
    # We look for local minima in Dst that are below the threshold
    storm_mask = dst_df['value'] < Dst_THRESHOLD_STORM
    storms = dst_df[storm_mask].copy()

    if storms.empty:
        # If no storms found, return an empty aligned dataframe with correct schema
        aligned_df = pd.DataFrame(columns=[
            'storm_time', 'dst_min', 'kp_max', 'flare_time', 'flare_flux',
            'cme_time', 'cme_speed', 'cme_width', 'has_match',
            'missing_flare', 'missing_cme', 'is_recurrent'
        ])
        return aligned_df

    # Find the actual minima within storm periods
    # For simplicity, we take the minimum Dst value for each storm event
    # In a more complex implementation, we might group consecutive storm days
    storms = storms.sort_values('time')
    storm_events = []
    current_storm_start = None
    current_storm_min = None
    current_storm_min_time = None

    for _, row in storms.iterrows():
        if current_storm_start is None:
            current_storm_start = row['time']
            current_storm_min = row['value']
            current_storm_min_time = row['time']
        elif (row['time'] - current_storm_min_time) <= timedelta(days=1):
            # Continue storm event
            if row['value'] < current_storm_min:
                current_storm_min = row['value']
                current_storm_min_time = row['time']
        else:
            # New storm event
            storm_events.append({
                'time': current_storm_min_time,
                'dst_min': current_storm_min
            })
            current_storm_start = row['time']
            current_storm_min = row['value']
            current_storm_min_time = row['time']

    # Don't forget the last storm
    if current_storm_start is not None:
        storm_events.append({
            'time': current_storm_min_time,
            'dst_min': current_storm_min
        })

    aligned_records = []

    for storm in storm_events:
        storm_time = storm['time']
        dst_min = storm['dst_min']

        # Find Kp max within the storm period (simplified: use max in a window)
        kp_window_start = storm_time - timedelta(days=1)
        kp_window_end = storm_time + timedelta(days=1)
        kp_window = kp_df[
            (kp_df['time'] >= kp_window_start) &
            (kp_df['time'] <= kp_window_end)
        ]

        kp_max = kp_window['value'].max() if not kp_window.empty else MISSING_FLAG

        # Search for matching flare
        flare_window_start = storm_time - timedelta(days=window_days)
        flare_window_end = storm_time
        flare_candidates = flare_df[
            (flare_df['time'] >= flare_window_start) &
            (flare_df['time'] <= flare_window_end)
        ]

        flare_time = MISSING_FLAG
        flare_flux = MISSING_FLAG
        has_flare = False

        if not flare_candidates.empty:
            # Take the most intense flare (highest flux)
            best_flare = flare_candidates.loc[flare_candidates['flux'].idxmax()]
            flare_time = best_flare['time']
            flare_flux = best_flare['flux']
            has_flare = True

        # Search for matching CME
        cme_window_start = storm_time - timedelta(days=window_days)
        cme_window_end = storm_time
        cme_candidates = cme_df[
            (cme_df['time'] >= cme_window_start) &
            (cme_df['time'] <= cme_window_end)
        ]

        cme_time = MISSING_FLAG
        cme_speed = MISSING_FLAG
        cme_width = MISSING_FLAG
        has_cme = False

        if not cme_candidates.empty:
            # Take the fastest CME
            best_cme = cme_candidates.loc[cme_candidates['speed'].idxmax()]
            cme_time = best_cme['time']
            cme_speed = best_cme['speed']
            cme_width = best_cme['width']
            has_cme = True

        # Determine if we have a match (at least one solar event)
        has_match = has_flare or has_cme

        # Flag missing data
        missing_flare = not has_flare
        missing_cme = not has_cme

        aligned_records.append({
            'storm_time': storm_time,
            'dst_min': dst_min,
            'kp_max': kp_max,
            'flare_time': flare_time,
            'flare_flux': flare_flux,
            'cme_time': cme_time,
            'cme_speed': cme_speed,
            'cme_width': cme_width,
            'has_match': has_match,
            'missing_flare': missing_flare,
            'missing_cme': missing_cme,
            'is_recurrent': False  # Will be updated by flag_recurrent_activity
        })

    aligned_df = pd.DataFrame(aligned_records)

    # Ensure correct column order and types
    expected_columns = [
        'storm_time', 'dst_min', 'kp_max', 'flare_time', 'flare_flux',
        'cme_time', 'cme_speed', 'cme_width', 'has_match',
        'missing_flare', 'missing_cme', 'is_recurrent'
    ]

    # Reindex to ensure all columns exist
    for col in expected_columns:
        if col not in aligned_df.columns:
            aligned_df[col] = MISSING_FLAG

    aligned_df = aligned_df[expected_columns]

    # Convert datetime columns back to string for CSV compatibility if needed
    # or keep as datetime for further processing
    # For now, keep as datetime

    return aligned_df

def flag_recurrent_activity(df: pd.DataFrame) -> pd.DataFrame:
    """
    Flag periods of recurrent solar activity.

    This function identifies time periods where multiple solar events
    occur in close succession, indicating recurrent activity.

    Args:
        df: DataFrame containing aligned events.

    Returns:
        DataFrame with 'is_recurrent' flag updated.
    """
    if df.empty:
        return df

    df = df.copy()
    df['storm_time'] = pd.to_datetime(df['storm_time'])

    # Sort by storm time
    df = df.sort_values('storm_time')

    # Flag events that occur within 27 days of another event (solar rotation period)
    # This is a simplified approach
    recurrent_indices = []

    for i, row in df.iterrows():
        current_time = row['storm_time']
        # Check for other events within +/- 27 days
        time_diffs = (df['storm_time'] - current_time).abs()
        # Exclude the event itself (diff=0)
        nearby_events = time_diffs[(time_diffs > timedelta(days=0)) & (time_diffs <= timedelta(days=27))]

        if not nearby_events.empty:
            recurrent_indices.append(i)

    df.loc[recurrent_indices, 'is_recurrent'] = True

    return df

def write_aligned_events(df: pd.DataFrame, output_path: str) -> None:
    """
    Write aligned events to a CSV file.

    Args:
        df: DataFrame containing aligned events.
        output_path: Path to the output CSV file.
    """
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Convert datetime to string for CSV
    df_output = df.copy()
    for col in df_output.columns:
        if pd.api.types.is_datetime64_any_dtype(df_output[col]):
            df_output[col] = df_output[col].astype(str)

    df_output.to_csv(output_path, index=False)

def main():
    """
    Main function to run the alignment process.

    This function orchestrates the loading of raw data, alignment of events,
    flagging of missing data and recurrent activity, and writing the output.
    """
    # Define paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(base_dir)

    flare_path = os.path.join(project_root, 'data', 'raw', 'goes_flares.csv')
    cme_path = os.path.join(project_root, 'data', 'raw', 'cme_catalog.csv')
    dst_path = os.path.join(project_root, 'data', 'raw', 'dst_indices.csv')
    kp_path = os.path.join(project_root, 'data', 'raw', 'kp_indices.csv')
    output_path = os.path.join(project_root, 'data', 'processed', 'aligned_events.csv')

    # Check if input files exist
    missing_files = []
    for path in [flare_path, cme_path, dst_path, kp_path]:
        if not os.path.exists(path):
            missing_files.append(path)

    if missing_files:
        error_msg = f"Missing required input files: {', '.join(missing_files)}"
        raise FileNotFoundError(error_msg)

    # Load data
    print("Loading flare data...")
    flare_df = pd.read_csv(flare_path)
    print(f"Loaded {len(flare_df)} flare events.")

    print("Loading CME data...")
    cme_df = pd.read_csv(cme_path)
    print(f"Loaded {len(cme_df)} CME events.")

    print("Loading Dst data...")
    dst_df = pd.read_csv(dst_path)
    print(f"Loaded {len(dst_df)} Dst records.")

    print("Loading Kp data...")
    kp_df = pd.read_csv(kp_path)
    print(f"Loaded {len(kp_df)} Kp records.")

    # Align events
    print("Aligning events...")
    aligned_df = align_events(flare_df, cme_df, dst_df, kp_df)
    print(f"Aligned {len(aligned_df)} storm events.")

    # Flag recurrent activity
    print("Flagging recurrent activity...")
    aligned_df = flag_recurrent_activity(aligned_df)

    # Count missing data
    missing_flare_count = aligned_df['missing_flare'].sum()
    missing_cme_count = aligned_df['missing_cme'].sum()
    total_storms = len(aligned_df)

    print(f"Missing flare data: {missing_flare_count}/{total_storms}")
    print(f"Missing CME data: {missing_cme_count}/{total_storms}")

    # Write output
    print(f"Writing aligned events to {output_path}...")
    write_aligned_events(aligned_df, output_path)
    print("Done.")

    return aligned_df

if __name__ == "__main__":
    main()