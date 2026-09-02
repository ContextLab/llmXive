import os
import sys
import logging
import json
import math
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np

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

RAW_DATA_PATH = Path("data/raw/molnet_raw.csv")
CURATED_DATA_PATH = Path("data/curated/curated_dataset.csv")
CURATED_DIR = Path("data/curated")

# Thresholds
MIN_ROWS = 100
MAX_MISSING_PERCENT = 5.0

def validate_adhesion_energy(df: pd.DataFrame) -> bool:
    """
    Validate that the dataframe has an adhesion energy column.
    Returns True if valid, raises DataError otherwise.
    """
    cols = [c.lower() for c in df.columns]
    energy_cols = [c for c in cols if 'energy' in c and 'adhesion' in c]
    
    if not energy_cols:
        # Try to find any energy column if adhesion is missing
        generic_energy = [c for c in cols if 'energy' in c]
        if generic_energy:
            logger.warning(f"No specific 'adhesion_energy' column found. Found: {generic_energy}. Mapping to 'adhesion_energy'.")
            # We will handle mapping in the cleaning step
            return True
        else:
            raise DataError("E-DATA-001: No energy column found in dataset. Required: adhesion_energy.")
    return True

def validate_row_count(df: pd.DataFrame) -> bool:
    """Validate row count meets minimum threshold."""
    if len(df) < MIN_ROWS:
        raise DataError(f"E-DATA-001: Dataset has {len(df)} rows, which is less than the required minimum of {MIN_ROWS}.")
    return True

def validate_missing_values(df: pd.DataFrame) -> bool:
    """Validate missing values per column are within threshold."""
    missing_pct = df.isnull().mean() * 100
    high_missing = missing_pct[missing_pct > MAX_MISSING_PERCENT]
    
    if not high_missing.empty:
        logger.warning(f"Columns with >{MAX_MISSING_PERCENT}% missing values: {high_missing.to_dict()}")
        # We proceed but log a warning, as per T015 requirements
        # The task says "flag missing values" and "process if row count >= 100"
        # It does not explicitly say to abort if missing > 5%, just to flag it.
        # However, T017 requires <= 5% missing for the final output.
        # We will drop rows with missing critical fields to satisfy T017.
        return True
    return True

def calculate_margin_of_error(n: int, std: float, confidence: float = 0.95) -> float:
    """Calculate margin of error: 1.96 * std / sqrt(n)."""
    if n < 2:
        return 0.0
    z_score = 1.96 # For 95% confidence
    return z_score * std / math.sqrt(n)

def clean_and_validate(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and validate the dataset.
    - Ensures required columns exist (polymer_smiles, filler_smiles, adhesion_energy).
    - Drops rows with missing critical values to satisfy T017 <= 5% missing.
    - Validates row count.
    """
    # 1. Validate Adhesion Energy
    validate_adhesion_energy(df)
    
    # 2. Standardize column names
    # Map common variations to standard names
    col_mapping = {}
    for col in df.columns:
        lower_col = col.lower()
        if 'smiles' in lower_col and 'polymer' in lower_col:
            col_mapping[col] = 'polymer_smiles'
        elif 'smiles' in lower_col and 'filler' in lower_col:
            col_mapping[col] = 'filler_smiles'
        elif 'smiles' in lower_col and 'poly' in lower_col:
            col_mapping[col] = 'polymer_smiles'
        elif 'smiles' in lower_col and 'fill' in lower_col:
            col_mapping[col] = 'filler_smiles'
        elif 'energy' in lower_col and 'adhesion' in lower_col:
            col_mapping[col] = 'adhesion_energy'
        elif 'energy' in lower_col:
            # If no specific adhesion column, use this as a proxy if needed, 
            # but for T017 we strictly need 'adhesion_energy'.
            # If we have two SMILES and one energy, we assume the energy corresponds to the pair.
            col_mapping[col] = 'adhesion_energy'
    
    # If we have generic 'smiles' and 'energy', we might need to infer pairs.
    # For this implementation, we assume the dataset structure is close enough
    # or we have a 'pair' identifier. If not, we might need to duplicate rows
    # or assume a 1:1 mapping if only one SMILES column exists (unlikely for interface pairs).
    
    # Check for presence of at least one SMILES column and one energy column
    has_smiles = any('smiles' in c.lower() for c in df.columns)
    has_energy = any('energy' in c.lower() for c in df.columns)
    
    if not has_smiles or not has_energy:
        raise DataError("E-DATA-001: Dataset must contain SMILES and Energy columns.")
    
    # Rename columns
    df = df.rename(columns=col_mapping)
    
    # Ensure we have the required columns
    required_cols = ['polymer_smiles', 'filler_smiles', 'adhesion_energy']
    
    # If we only have one 'smiles' column, it might be a single molecule dataset.
    # The task T017 explicitly asks for 'polymer_smiles' and 'filler_smiles'.
    # If the source data doesn't have two distinct SMILES columns, we cannot fabricate them.
    # We check if we have two SMILES columns (or one that can be split).
    
    smiles_cols = [c for c in df.columns if c in ['polymer_smiles', 'filler_smiles']]
    if len(smiles_cols) < 2:
        # Try to find any two SMILES columns
        all_smiles = [c for c in df.columns if 'smiles' in c.lower()]
        if len(all_smiles) >= 2:
            # Assume first is polymer, second is filler
            df['polymer_smiles'] = df[all_smiles[0]]
            df['filler_smiles'] = df[all_smiles[1]]
            # Remove the old columns if they were renamed
            for old in all_smiles:
                if old not in ['polymer_smiles', 'filler_smiles']:
                    df.drop(columns=[old], inplace=True)
        else:
            # If only one SMILES column, we cannot create pairs.
            # This is a data source issue. We abort.
            raise DataError("E-DATA-001: Dataset must contain at least two SMILES columns for polymer and filler.")
    
    # Ensure adhesion_energy exists
    if 'adhesion_energy' not in df.columns:
        # Try to find any energy column
        energy_cols = [c for c in df.columns if 'energy' in c.lower()]
        if energy_cols:
            df['adhesion_energy'] = df[energy_cols[0]]
            df.drop(columns=[energy_cols[0]], inplace=True)
        else:
            raise DataError("E-DATA-001: Dataset must contain an adhesion energy column.")
    
    # Select only required columns
    df = df[required_cols].copy()
    
    # 3. Validate Row Count
    validate_row_count(df)
    
    # 4. Handle Missing Values
    # T017 requires <= 5% missing per column. We drop rows with missing critical data.
    initial_count = len(df)
    df = df.dropna()
    final_count = len(df)
    
    if final_count < MIN_ROWS:
        raise DataError(f"E-DATA-001: After cleaning missing values, dataset has {final_count} rows, which is less than {MIN_ROWS}.")
    
    missing_pct = (initial_count - final_count) / initial_count * 100
    if missing_pct > MAX_MISSING_PERCENT:
        logger.warning(f"More than {MAX_MISSING_PERCENT}% of rows were dropped due to missing values ({missing_pct:.1f}%).")
        # T017 says "missing values per column must be <= 5%".
        # By dropping rows, we ensure the remaining dataset has 0% missing.
        # The warning is logged, but we proceed if count >= 100.
    
    # 5. Calculate Margin of Error if rows < 500
    if final_count < 500:
        std = df['adhesion_energy'].std()
        moe = calculate_margin_of_error(final_count, std)
        logger.warning(f"Limited Power Warning: Dataset size ({final_count}) is less than 500. "
                       f"Margin of Error (95% CI) for adhesion energy: {moe:.4f}")
    
    return df

def main():
    """Main entry point for data cleaning."""
    try:
        # Load raw data
        if not RAW_DATA_PATH.exists():
            raise DataError(f"Raw data file not found: {RAW_DATA_PATH}. Run download.py first.")
        
        df = pd.read_csv(RAW_DATA_PATH)
        logger.info(f"Loaded {len(df)} rows from {RAW_DATA_PATH}")
        
        # Clean and validate
        df_cleaned = clean_and_validate(df)
        
        # Ensure output directory exists
        CURATED_DIR.mkdir(parents=True, exist_ok=True)
        
        # Save curated dataset
        df_cleaned.to_csv(CURATED_DATA_PATH, index=False)
        logger.info(f"Saved curated dataset to {CURATED_DATA_PATH} with {len(df_cleaned)} rows.")
        
        # Validate output
        if len(df_cleaned) < MIN_ROWS:
            raise DataError(f"Output dataset has {len(df_cleaned)} rows, less than required {MIN_ROWS}.")
        
        # Check missing values in output
        missing_pct = df_cleaned.isnull().mean() * 100
        if (missing_pct > MAX_MISSING_PERCENT).any():
            raise DataError(f"Output dataset has columns with >{MAX_MISSING_PERCENT}% missing values.")
        
        logger.info("Data cleaning and validation completed successfully.")
        
    except DataError as e:
        logger.error(f"Data error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
