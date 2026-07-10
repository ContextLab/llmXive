"""
align_data.py

Merges cosmic ray flux data (from fetch_ams02.py) and solar activity data (from fetch_noaa.py).
Handles time zones, date format normalization, and flags gaps > 30 days.
Outputs a unified CSV to data/processed/unified_timeseries.csv.
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import numpy as np

# Project root relative to this file
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

# Import logging utilities
from utils.logging import setup_logger, log_data_gap

# Configure logger
logger = setup_logger("align_data")

def load_flux_data() -> pd.DataFrame:
    """
    Loads the preprocessed AMS-02 flux data.
    Expects 'data/raw/ams02_flux.csv' to exist (output of T011).
    Returns a DataFrame with columns: date, rigidity, species, flux.
    """
    flux_path = DATA_RAW_DIR / "ams02_flux.csv"
    if not flux_path.exists():
        logger.error(f"Flux data file not found: {flux_path}")
        raise FileNotFoundError(f"Required flux data missing at {flux_path}")
    
    df = pd.read_csv(flux_path)
    # Ensure 'date' is datetime
    df['date'] = pd.to_datetime(df['date'])
    return df

def load_solar_data() -> pd.DataFrame:
    """
    Loads the preprocessed NOAA sunspot data.
    Expects 'data/raw/noaa_sunspots.csv' to exist (output of T012).
    Returns a DataFrame with columns: date, sunspot_number.
    """
    solar_path = DATA_RAW_DIR / "noaa_sunspots.csv"
    if not solar_path.exists():
        logger.error(f"Sunspot data file not found: {solar_path}")
        raise FileNotFoundError(f"Required sunspot data missing at {solar_path}")
    
    df = pd.read_csv(solar_path)
    # Ensure 'date' is datetime
    df['date'] = pd.to_datetime(df['date'])
    return df

def flag_gaps(df: pd.DataFrame, gap_threshold_days: int = 30) -> pd.DataFrame:
    """
    Flags rows where the gap from the previous date exceeds the threshold.
    Adds a boolean column 'is_data_gap'.
    """
    df = df.sort_values('date').reset_index(drop=True)
    df['date_diff'] = df['date'].diff().dt.days
    df['is_data_gap'] = df['date_diff'] > gap_threshold_days
    
    # Flag the first row after a gap as a gap start, or handle strictly?
    # The requirement says "flag gaps > 30 days". We mark the rows that follow a large gap.
    # We also need to ensure the first row isn't flagged as a gap unless it's the start of a known gap.
    # Standard approach: if diff > threshold, mark current as gap.
    
    # Reset the diff for the very first row to avoid NaN issues in boolean logic if needed,
    # though pd.to_datetime usually handles it.
    df['is_data_gap'] = df['is_data_gap'].fillna(False)
    
    return df

def merge_datasets(flux_df: pd.DataFrame, solar_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merges flux and solar data on date.
    Handles potential multiple rigidity bins and species in flux_df.
    """
    # Pivot flux data to have species/rigidity as columns for easier merging?
    # The requirement says: "output a single CSV file containing columns for date, rigidity bin, 
    # proton flux, helium flux, heavy flux, and sunspot number."
    # This implies we need to pivot the long-format flux data (if it is long) into wide format
    # per rigidity bin, or iterate per rigidity bin.
    
    # Let's assume the input flux_df has: date, rigidity, species, flux
    # We need to pivot to: date, rigidity, proton_flux, helium_flux, heavy_flux
    
    if 'species' not in flux_df.columns:
        raise ValueError("Flux data must contain 'species' column to pivot.")
    
    # Normalize species names to ensure consistency
    flux_df['species'] = flux_df['species'].str.lower().str.strip()
    
    # Map species to target columns
    species_map = {
        'proton': 'proton_flux',
        'helium': 'helium_flux',
        'he': 'helium_flux',
        'cno': 'heavy_flux',
        'fe': 'heavy_flux',
        'heavy': 'heavy_flux'
    }
    
    # Create a unified species column for pivoting
    flux_df['target_species'] = flux_df['species'].map(species_map)
    flux_df = flux_df[flux_df['target_species'].notna()]
    
    # Pivot
    # We want one row per (date, rigidity)
    pivot_df = flux_df.pivot_table(
        index=['date', 'rigidity'],
        columns='target_species',
        values='flux',
        aggfunc='mean' # In case of duplicates, take mean
    ).reset_index()
    
    # Ensure columns exist (fill NaN with NaN for now, will be handled in gap logic)
    for col in ['proton_flux', 'helium_flux', 'heavy_flux']:
        if col not in pivot_df.columns:
            pivot_df[col] = np.nan
    
    # Merge with solar data
    # Solar data has one row per date
    merged = pd.merge(
        pivot_df,
        solar_df[['date', 'sunspot_number']],
        on='date',
        how='left'
    )
    
    # Sort by date
    merged = merged.sort_values('date').reset_index(drop=True)
    
    return merged

def main():
    """
    Main entry point for T013.
    1. Load flux and solar data.
    2. Merge on date.
    3. Flag gaps > 30 days.
    4. Save to data/processed/unified_timeseries.csv.
    """
    logger.info("Starting data alignment process (T013)...")
    
    try:
        # Load data
        logger.info("Loading AMS-02 flux data...")
        flux_df = load_flux_data()
        
        logger.info("Loading NOAA sunspot data...")
        solar_df = load_solar_data()
        
        # Merge
        logger.info("Merging datasets...")
        unified_df = merge_datasets(flux_df, solar_df)
        
        # Flag gaps
        logger.info("Flagging data gaps (> 30 days)...")
        unified_df = flag_gaps(unified_df, gap_threshold_days=30)
        
        # Count gaps
        gap_count = unified_df['is_data_gap'].sum()
        logger.info(f"Detected {gap_count} rows following a data gap > 30 days.")
        
        # Ensure output directory exists
        DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        output_path = DATA_PROCESSED_DIR / "unified_timeseries.csv"
        
        # Save
        unified_df.to_csv(output_path, index=False)
        logger.info(f"Successfully saved unified timeseries to {output_path}")
        
        # Verification
        if not output_path.exists():
            logger.error("Output file was not created.")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Alignment process failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
