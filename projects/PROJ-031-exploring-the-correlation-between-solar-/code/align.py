import os
import csv
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import logging

# Configure logging for this module
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_aligned_events(flare_path: str, cme_path: str, dst_path: str) -> pd.DataFrame:
    """
    Load flare, CME, and Dst data into a unified DataFrame.
    Handles missing files gracefully by returning empty DataFrames with expected columns.
    """
    logger.info(f"Loading flare data from {flare_path}")
    if os.path.exists(flare_path):
        flares = pd.read_csv(flare_path)
        if 'time' not in flares.columns:
            flares['time'] = pd.to_datetime(flares['time'])
    else:
        logger.warning(f"Flare file not found: {flare_path}. Creating empty DataFrame.")
        flares = pd.DataFrame(columns=['time', 'flux', 'class', 'region'])

    logger.info(f"Loading CME data from {cme_path}")
    if os.path.exists(cme_path):
        cmes = pd.read_csv(cme_path)
        if 'time' not in cmes.columns:
            cmes['time'] = pd.to_datetime(cmes['time'])
    else:
        logger.warning(f"CME file not found: {cme_path}. Creating empty DataFrame.")
        cmes = pd.DataFrame(columns=['time', 'speed', 'width', 'halo'])

    logger.info(f"Loading Dst data from {dst_path}")
    if os.path.exists(dst_path):
        dst = pd.read_csv(dst_path)
        if 'time' not in dst.columns:
            dst['time'] = pd.to_datetime(dst['time'])
    else:
        logger.warning(f"Dst file not found: {dst_path}. Creating empty DataFrame.")
        dst = pd.DataFrame(columns=['time', 'value'])

    return flares, cmes, dst

def align_events(flares: pd.DataFrame, cmes: pd.DataFrame, dst: pd.DataFrame, window_days: int = 3) -> pd.DataFrame:
    """
    Align solar events (flares/CMEs) with geomagnetic storms (Dst minima).
    
    For each Dst minimum (storm), find the preceding solar event within the window.
    If no match is found, the storm is retained with NULL solar predictors.
    If multiple events exist, the closest one is chosen.
    
    Returns a DataFrame with columns:
    - storm_time, storm_dst (the event)
    - flare_time, flare_flux, flare_class, flare_region (or NaN if missing)
    - cme_time, cme_speed, cme_width, cme_halo (or NaN if missing)
    - match_found (bool): True if a solar event was found within window
    - time_diff_days (float): Days between solar event and storm (NaN if no match)
    """
    if dst.empty:
        logger.warning("Dst DataFrame is empty. Cannot align events.")
        return pd.DataFrame()

    # Identify storms as local minima in Dst
    # A storm is a significant drop; we'll mark local minima below a threshold or just all local minima
    # For simplicity, we treat every local minimum as a potential storm candidate
    # Then we filter or flag them later if needed.
    # We sort by time first
    dst = dst.sort_values('time').reset_index(drop=True)
    
    # Find local minima: value is lower than both neighbors
    # We'll use a simple approach: iterate and compare
    storm_candidates = []
    for i in range(1, len(dst) - 1):
        if dst.loc[i, 'value'] < dst.loc[i-1, 'value'] and dst.loc[i, 'value'] < dst.loc[i+1, 'value']:
            storm_candidates.append(dst.loc[i])
    
    # If no local minima found (e.g., flat data), just take the global minimum if it exists
    if not storm_candidates and not dst.empty:
        idx = dst['value'].idxmin()
        storm_candidates.append(dst.loc[idx])
    
    if not storm_candidates:
        logger.warning("No storm candidates found in Dst data.")
        return pd.DataFrame()

    results = []
    window_delta = timedelta(days=window_days)

    for storm in storm_candidates:
        storm_time = storm['time']
        storm_val = storm['value']
        
        # Define search window: [storm_time - window_days, storm_time]
        # We look for solar events that happened BEFORE the storm
        search_start = storm_time - window_delta
        search_end = storm_time

        # Find matching flares
        matched_flare = None
        if not flares.empty:
            mask = (flares['time'] >= search_start) & (flares['time'] <= search_end)
            candidates = flares[mask]
            if not candidates.empty:
                # Pick the one closest to storm_time (latest before storm)
                closest = candidates.loc[candidates['time'].idxmax()]
                matched_flare = closest

        # Find matching CMEs
        matched_cme = None
        if not cmes.empty:
            mask = (cmes['time'] >= search_start) & (cmes['time'] <= search_end)
            candidates = cmes[mask]
            if not candidates.empty:
                closest = candidates.loc[candidates['time'].idxmax()]
                matched_cme = closest

        # Determine match status
        match_found = (matched_flare is not None) or (matched_cme is not None)
        
        # Calculate time difference if matched
        time_diff = None
        if match_found:
            # Prefer CME time if available, else flare time
            ref_time = matched_cme['time'] if matched_cme is not None else matched_flare['time']
            time_diff = (storm_time - ref_time).total_seconds() / 86400.0

        # Build row with NULLs for missing predictors (T015 requirement)
        row = {
            'storm_time': storm_time,
            'storm_dst': storm_val,
            'flare_time': matched_flare['time'] if matched_flare is not None else None,
            'flare_flux': matched_flare['flux'] if matched_flare is not None else None,
            'flare_class': matched_flare['class'] if matched_flare is not None else None,
            'flare_region': matched_flare['region'] if matched_flare is not None else None,
            'cme_time': matched_cme['time'] if matched_cme is not None else None,
            'cme_speed': matched_cme['speed'] if matched_cme is not None else None,
            'cme_width': matched_cme['width'] if matched_cme is not None else None,
            'cme_halo': matched_cme['halo'] if matched_cme is not None else None,
            'match_found': match_found,
            'time_diff_days': time_diff
        }
        results.append(row)

    if not results:
        logger.warning("No aligned events could be formed.")
        return pd.DataFrame()

    df = pd.DataFrame(results)
    logger.info(f"Aligned {len(df)} storm events. {df['match_found'].sum()} had solar matches.")
    return df

def flag_recurrent_activity(df: pd.DataFrame) -> pd.DataFrame:
    """
    Flag periods of recurrent solar activity.
    If a storm has a match, and another storm occurs within 24 hours of the previous storm's solar trigger,
    it might be part of a recurrent period.
    For this task, we simply add a placeholder column 'is_recurrent' set to False for now.
    Detailed logic is handled in T016.
    """
    df['is_recurrent'] = False
    return df

def write_aligned_events(df: pd.DataFrame, output_path: str):
    """
    Write the aligned events DataFrame to a CSV file.
    Ensures directories exist.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Wrote {len(df)} aligned events to {output_path}")

def main():
    """
    Main entry point for the alignment process.
    Reads raw data, aligns events, flags missing data, and writes output.
    """
    # Configuration paths (relative to project root)
    flare_path = "data/raw/goes_flares.csv"
    cme_path = "data/raw/lasco_cmes.csv"
    dst_path = "data/raw/dst_indices.csv"
    output_path = "data/processed/aligned_events.csv"

    logger.info("Starting alignment process...")
    
    # Load data
    flares, cmes, dst = load_aligned_events(flare_path, cme_path, dst_path)
    
    # Align events
    aligned_df = align_events(flares, cmes, dst, window_days=3)
    
    # Flag recurrent activity (T016 logic placeholder, just adds column)
    aligned_df = flag_recurrent_activity(aligned_df)
    
    # Write output
    write_aligned_events(aligned_df, output_path)
    
    logger.info("Alignment process completed successfully.")
    return aligned_df

if __name__ == "__main__":
    main()