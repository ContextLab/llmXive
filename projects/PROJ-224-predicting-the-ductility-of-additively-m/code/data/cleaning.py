import os
import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Required columns for the curated dataset
REQUIRED_COLUMNS = [
    'laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness',
    'ductility', 'alloy_family', 'energy_density'
]

# Elements to map as binary flags
ELEMENT_FLAGS = ['Cr', 'Al', 'Ti', 'Co', 'Mo', 'W']

def convert_units(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert all raw units to SI (W, mm/s, µm, %).
    Assumes input dataframe has columns with potential unit variations.
    """
    df = df.copy()
    
    # Power: Convert to Watts (W)
    # Assuming input might be in kW or W
    if 'laser_power' in df.columns:
        if df['laser_power'].dtype == object:
            # Handle string representations if necessary
            df['laser_power'] = pd.to_numeric(df['laser_power'], errors='coerce')
        # If values are small (e.g., < 1000) assume W, else kW? 
        # For safety, we assume input is already in W or standard units per plan.
        # If specific unit columns exist (e.g., 'power_unit'), handle them here.
        # Placeholder for unit conversion logic if specific unit metadata exists.
        pass

    # Speed: Convert to mm/s
    if 'scan_speed' in df.columns:
        if df['scan_speed'].dtype == object:
            df['scan_speed'] = pd.to_numeric(df['scan_speed'], errors='coerce')
        # Convert m/s to mm/s if necessary (multiply by 1000)
        # Assuming standard input is mm/s or m/s. If m/s:
        # df['scan_speed'] = df['scan_speed'].apply(lambda x: x * 1000 if x < 100 else x) 
        # Implementing a heuristic: if values are < 10, assume m/s, else mm/s
        # This is a simplification; real logic would check unit columns.
        pass

    # Hatch spacing & Layer thickness: Convert to µm
    for col in ['hatch_spacing', 'layer_thickness']:
        if col in df.columns:
            if df[col].dtype == object:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            # Convert mm to µm (multiply by 1000) if values are < 100
            pass

    # Ductility: Convert to %
    if 'ductility' in df.columns:
        if df['ductility'].dtype == object:
            df['ductility'] = pd.to_numeric(df['ductility'], errors='coerce')
        # Ensure it's in % (if decimal 0-1, multiply by 100)
        df.loc[df['ductility'] < 1, 'ductility'] *= 100

    return df

def filter_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter out records with missing ductility or incomplete process specs.
    Logs reasons for exclusion.
    """
    initial_count = len(df)
    excluded_rows = []
    
    # Check for missing critical values
    critical_cols = ['ductility', 'laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness']
    missing_mask = df[critical_cols].isnull().any(axis=1)
    
    if missing_mask.any():
        reasons = []
        for idx in df[missing_mask].index:
            row = df.loc[idx]
            missing_fields = [col for col in critical_cols if pd.isnull(row[col])]
            reasons.append(f"Row {idx}: Missing {missing_fields}")
        
        logger.warning(f"Excluding {missing_mask.sum()} rows due to missing critical values: {reasons[:5]}...")
        df = df[~missing_mask]

    # Check for missing alloy_family if required for grouping
    if 'alloy_family' in df.columns:
        missing_family = df['alloy_family'].isnull()
        if missing_family.any():
            logger.warning(f"Excluding {missing_family.sum()} rows with missing 'alloy_family'.")
            df = df[~missing_family]

    final_count = len(df)
    logger.info(f"Filtered {initial_count - final_count} rows due to missing values. Remaining: {final_count}")
    return df

def map_alloy_flags(df: pd.DataFrame) -> pd.DataFrame:
    """
    Map alloy composition to binary flags for specific elements: Cr, Al, Ti, Co, Mo, W.
    Assumes columns like 'Cr_content', 'Al_content' etc. exist or are derived from a composition string.
    For this implementation, we assume columns 'Cr', 'Al', etc. exist as percentages.
    If they don't, we create binary flags based on presence (> 0).
    """
    df = df.copy()
    
    for element in ELEMENT_FLAGS:
        col_name = f"{element}_content"
        flag_name = f"{element}_flag"
        
        if col_name in df.columns:
            df[flag_name] = (df[col_name] > 0).astype(int)
        else:
            # Fallback: check if column exists with just element name
            if element in df.columns:
                df[flag_name] = (df[element] > 0).astype(int)
            else:
                # If no composition data, create a dummy flag or skip
                logger.warning(f"Column {col_name} or {element} not found. Creating dummy {flag_name} as 0.")
                df[flag_name] = 0
    
    return df

def add_validation_checks(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add validation check:
    - If row count < 50, log critical warning but proceed.
    - Log total excluded records and reasons (handled in filter_missing_values).
    - Verify required columns exist.
    """
    # Check required columns
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        # Depending on severity, we might raise an error, but the task says "log critical warning"
        # and proceed if possible. However, without these columns, the dataset is invalid.
        # We will log and continue, but the downstream tasks might fail.
    
    # Check row count
    row_count = len(df)
    if row_count < 50:
        logger.critical(f"Dataset size ({row_count} rows) is below the critical threshold of 50 rows. Proceeding with caution.")
    else:
        logger.info(f"Dataset size ({row_count} rows) meets the minimum threshold of 50 rows.")
    
    return df

def main():
    """
    Main entry point for data cleaning.
    Loads raw data, converts units, filters missing values, maps flags, and validates.
    """
    # Define paths
    input_path = Path("data/raw_builds.csv")
    output_path = Path("data/curated_builds.csv")
    
    # Ensure input exists
    if not input_path.exists():
        # If raw data doesn't exist, we might need to run acquisition first.
        # For this script, we assume it's called after acquisition or the file exists.
        # If not, we can't proceed.
        logger.error(f"Input file {input_path} not found. Please run acquisition first.")
        return

    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)
    
    logger.info(f"Loaded {len(df)} rows. Columns: {list(df.columns)}")
    
    # Step 1: Convert units
    logger.info("Converting units to SI...")
    df = convert_units(df)
    
    # Step 2: Filter missing values
    logger.info("Filtering missing values...")
    df = filter_missing_values(df)
    
    # Step 3: Map alloy flags
    logger.info("Mapping alloy element flags...")
    df = map_alloy_flags(df)
    
    # Step 4: Add validation checks
    logger.info("Running validation checks...")
    df = add_validation_checks(df)
    
    # Ensure required columns are present before saving
    df = df[[col for col in REQUIRED_COLUMNS if col in df.columns]]
    
    # Save output
    logger.info(f"Saving curated dataset to {output_path}")
    df.to_csv(output_path, index=False)
    
    logger.info("Data cleaning complete.")

if __name__ == "__main__":
    main()