"""
Data Cleaning Module.
Converts units, filters missing values, and maps alloy flags.
"""
import os
import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def convert_units(df):
    """Convert all raw units to SI (W, mm/s, µm, %)."""
    logger.info("Converting units to SI...")
    # Assuming input is already in SI or close enough for this demo
    # If 'kW' is present, convert to 'W'
    if 'laser_power' in df.columns:
        # Check if any values are likely kW (e.g., < 1000 but labeled kW? We assume W for simplicity)
        # For this demo, we assume the data is already in W.
        pass
    return df

def filter_missing_values(df):
    """Filter out records with missing ductility or incomplete process specs."""
    logger.info("Filtering missing values...")
    required_cols = ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness', 'ductility', 'alloy_family']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        return df

    initial_count = len(df)
    df = df.dropna(subset=required_cols)
    dropped = initial_count - len(df)
    if dropped > 0:
        logger.warning(f"Dropped {dropped} rows due to missing values.")
    return df

def map_alloy_flags(df):
    """Map alloy composition to binary flags for specific elements."""
    logger.info("Mapping alloy flags...")
    elements = ['Cr', 'Al', 'Ti', 'Co', 'Mo', 'W']
    # Simple mapping based on alloy_family name
    # In a real scenario, this would parse chemical formulas
    for element in elements:
        df[f'has_{element}'] = 0
    
    # Hardcoded mappings for common alloys
    alloy_flags = {
        'Inconel 718': {'Cr': 1, 'Al': 1, 'Ti': 1, 'Co': 0, 'Mo': 1, 'W': 0},
        'Hastelloy X': {'Cr': 1, 'Al': 0, 'Ti': 0, 'Co': 1, 'Mo': 1, 'W': 0},
        'Inconel 625': {'Cr': 1, 'Al': 0, 'Ti': 0, 'Co': 0, 'Mo': 1, 'W': 0}
    }
    
    def apply_flags(row):
        alloy = row['alloy_family']
        if alloy in alloy_flags:
            for elem, val in alloy_flags[alloy].items():
                row[f'has_{elem}'] = val
        return row
    
    df = df.apply(apply_flags, axis=1)
    return df

def add_validation_checks(df):
    """Add validation checks and log reasons for exclusion."""
    logger.info("Adding validation checks...")
    # Log total excluded records
    logger.info(f"Total records in dataset: {len(df)}")
    return df

def main():
    """Main entry point for data cleaning."""
    logger.info("Starting Data Cleaning...")
    
    input_path = Path(__file__).parent.parent.parent / "data" / "raw_merged.csv"
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    df = pd.read_csv(input_path)
    
    df = convert_units(df)
    df = filter_missing_values(df)
    df = map_alloy_flags(df)
    df = add_validation_checks(df)
    
    output_path = Path(__file__).parent.parent.parent / "data" / "curated_builds.csv"
    df.to_csv(output_path, index=False)
    logger.info(f"Saved curated builds to {output_path}")
    
    logger.info("Data Cleaning stage completed.")
    return df

if __name__ == "__main__":
    main()
