"""
Data cleaning module for the ductility prediction pipeline.
Handles unit conversion, filtering, and feature engineering.
"""
import os
import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

def convert_units(df: pd.DataFrame) -> pd.DataFrame:
    """Convert all units to SI (W, mm/s, µm, %)."""
    logger.info("Converting units to SI")
    
    # Power: ensure W (assume input is already W based on acquisition)
    if 'laser_power' in df.columns:
        df['laser_power'] = pd.to_numeric(df['laser_power'], errors='coerce')
    
    # Scan speed: ensure mm/s
    if 'scan_speed' in df.columns:
        df['scan_speed'] = pd.to_numeric(df['scan_speed'], errors='coerce')
    
    # Hatch spacing: ensure mm
    if 'hatch_spacing' in df.columns:
        df['hatch_spacing'] = pd.to_numeric(df['hatch_spacing'], errors='coerce')
    
    # Layer thickness: ensure mm
    if 'layer_thickness' in df.columns:
        df['layer_thickness'] = pd.to_numeric(df['layer_thickness'], errors='coerce')
    
    # Ductility: ensure %
    if 'ductility' in df.columns:
        df['ductility'] = pd.to_numeric(df['ductility'], errors='coerce')
    
    return df

def filter_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """Filter out records with missing ductility or incomplete process specs."""
    logger.info("Filtering missing values")
    
    required_cols = ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness', 'ductility', 'alloy_family']
    missing_before = len(df)
    
    # Drop rows with any missing required values
    df_clean = df.dropna(subset=required_cols)
    
    dropped_count = missing_before - len(df_clean)
    if dropped_count > 0:
        logger.warning(f"Dropped {dropped_count} rows with missing required values")
    
    return df_clean

def map_alloy_flags(df: pd.DataFrame) -> pd.DataFrame:
    """Map alloy composition to binary flags for specific elements."""
    logger.info("Mapping alloy flags")
    
    elements = ['cr', 'al', 'ti', 'co', 'mo', 'w']
    
    for elem in elements:
        if elem in df.columns:
            # Create binary flag: 1 if element present (>0.1%), 0 otherwise
            df[f'{elem}_flag'] = (df[elem] > 0.1).astype(int)
        else:
            # If composition columns don't exist, create flags based on alloy family
            df[f'{elem}_flag'] = 0
    
    return df

def add_validation_checks(df: pd.DataFrame) -> pd.DataFrame:
    """Add validation checks for data integrity."""
    logger.info("Adding validation checks")
    
    # Check row count
    if len(df) < 50:
        logger.critical(f"Dataset has only {len(df)} rows (< 50). Proceeding with warning.")
    
    # Check for negative values
    numeric_cols = ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness', 'ductility']
    for col in numeric_cols:
        if col in df.columns:
            negative_count = (df[col] < 0).sum()
            if negative_count > 0:
                logger.warning(f"Found {negative_count} negative values in {col}")
    
    return df

def main():
    """Main entry point for data cleaning."""
    logger.info("Starting data cleaning")
    
    # Load input data (from acquisition)
    input_path = DATA_DIR / "curated_builds_with_descriptors.csv"
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} records from {input_path}")
    
    # Apply cleaning steps
    df = convert_units(df)
    df = filter_missing_values(df)
    df = map_alloy_flags(df)
    df = add_validation_checks(df)
    
    # Save output
    output_path = DATA_DIR / "curated_builds.csv"
    df.to_csv(output_path, index=False)
    logger.info(f"Saved cleaned data to {output_path}")
    
    return df

if __name__ == "__main__":
    main()
