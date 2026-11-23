"""
Generate the curated dataset for molecular interactions.

This script loads the cleaned data from data/raw/molnet_raw.csv,
validates the required fields, and outputs the final curated dataset
to data/curated/curated_dataset.csv with the schema:
- polymer_smiles (str)
- filler_smiles (str)
- adhesion_energy (float)

It enforces the hard abort logic (E-DATA-001) if adhesion_energy is missing
or row count < 100, as per the project plan.
"""
import os
import sys
import logging
import json
import math
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.exceptions import DataError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Paths
RAW_DATA_PATH = project_root / "data" / "raw" / "molnet_raw.csv"
CURATED_OUTPUT_PATH = project_root / "data" / "curated" / "curated_dataset.csv"
OUTPUT_DIR = CURATED_OUTPUT_PATH.parent

def load_cleaned_data() -> pd.DataFrame:
    """
    Load the cleaned data from the raw CSV file.
    """
    if not RAW_DATA_PATH.exists():
        raise DataError(f"Raw data file not found at {RAW_DATA_PATH}. "
                        "Please run code/data/download.py and code/data/clean.py first.")
    
    logger.info(f"Loading cleaned data from {RAW_DATA_PATH}")
    try:
        df = pd.read_csv(RAW_DATA_PATH)
        logger.info(f"Loaded {len(df)} rows from {RAW_DATA_PATH}")
        return df
    except Exception as e:
        raise DataError(f"Failed to load cleaned data from {RAW_DATA_PATH}: {e}")

def validate_adhesion_energy(df: pd.DataFrame) -> Tuple[bool, str]:
    """
    Validate that the 'adhesion_energy' column exists and has valid data.
    """
    if 'adhesion_energy' not in df.columns:
        return False, "Column 'adhesion_energy' is missing from the dataset."
    
    # Check for missing values
    missing_count = df['adhesion_energy'].isna().sum()
    total_count = len(df)
    missing_pct = (missing_count / total_count * 100) if total_count > 0 else 100
    
    if missing_pct > 5.0:
        return False, f"Missing values in 'adhesion_energy' exceed 5% ({missing_pct:.2f}%)."
    
    return True, "Adhesion energy validation passed."

def validate_row_count(df: pd.DataFrame) -> Tuple[bool, str]:
    """
    Validate that the dataset has at least 100 rows.
    """
    count = len(df)
    if count < 100:
        return False, f"Row count ({count}) is below the minimum threshold of 100."
    return True, f"Row count validation passed ({count} rows)."

def validate_missing_values(df: pd.DataFrame) -> Tuple[bool, str]:
    """
    Validate that missing values per column are <= 5%.
    """
    threshold = 0.05
    problematic_cols = []
    
    for col in df.columns:
        missing_pct = df[col].isna().sum() / len(df)
        if missing_pct > threshold:
            problematic_cols.append(f"{col} ({missing_pct*100:.2f}%)")
    
    if problematic_cols:
        return False, f"Columns with >5% missing values: {', '.join(problematic_cols)}"
    
    return True, "Missing value validation passed."

def calculate_margin_of_error(df: pd.DataFrame) -> float:
    """
    Calculate the margin of error for the adhesion energy measurements.
    Formula: 1.96 * std / sqrt(n)
    """
    adhesion_data = df['adhesion_energy'].dropna()
    if len(adhesion_data) < 2:
        return float('nan')
    
    std_val = adhesion_data.std()
    n = len(adhesion_data)
    moe = 1.96 * std_val / math.sqrt(n)
    return moe

def generate_curated_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate the curated dataset with the required schema.
    """
    # Select and rename columns if necessary
    required_cols = ['polymer_smiles', 'filler_smiles', 'adhesion_energy']
    
    # Check if all required columns exist
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise DataError(f"Required columns missing: {missing_cols}")
    
    # Create the curated dataframe
    curated_df = df[required_cols].copy()
    
    # Drop rows where any required value is missing
    initial_rows = len(curated_df)
    curated_df = curated_df.dropna(subset=required_cols)
    final_rows = len(curated_df)
    
    if initial_rows != final_rows:
        logger.warning(f"Dropped {initial_rows - final_rows} rows due to missing required values.")
    
    # Ensure adhesion_energy is float
    curated_df['adhesion_energy'] = curated_df['adhesion_energy'].astype(float)
    
    return curated_df

def main():
    """
    Main function to generate the curated dataset.
    """
    logger.info("Starting curated dataset generation...")
    
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load cleaned data
    df = load_cleaned_data()
    
    # Validate adhesion energy
    valid, msg = validate_adhesion_energy(df)
    if not valid:
        raise DataError(f"E-DATA-001: {msg}")
    logger.info(f"Adhesion energy validation: {msg}")
    
    # Validate row count
    valid, msg = validate_row_count(df)
    if not valid:
        raise DataError(f"E-DATA-001: {msg}")
    logger.info(f"Row count validation: {msg}")
    
    # Validate missing values
    valid, msg = validate_missing_values(df)
    if not valid:
        logger.warning(f"Missing value validation warning: {msg}")
        # Log warning but proceed as per T016 (Limited Power)
    else:
        logger.info(f"Missing value validation: {msg}")
    
    # Generate curated dataset
    curated_df = generate_curated_dataset(df)
    
    # Log margin of error if row count is between 100 and 500
    if 100 <= len(curated_df) < 500:
        moe = calculate_margin_of_error(curated_df)
        logger.warning(f"Limited Power Warning: Dataset has {len(curated_df)} rows. "
                       f"Margin of Error for adhesion_energy: {moe:.4f}")
    
    # Save curated dataset
    curated_df.to_csv(CURATED_OUTPUT_PATH, index=False)
    logger.info(f"Curated dataset saved to {CURATED_OUTPUT_PATH} with {len(curated_df)} rows.")
    
    # Verify the output file
    if not CURATED_OUTPUT_PATH.exists():
        raise DataError(f"Failed to create output file at {CURATED_OUTPUT_PATH}")
    
    logger.info("Curated dataset generation completed successfully.")
    return curated_df

if __name__ == "__main__":
    main()
