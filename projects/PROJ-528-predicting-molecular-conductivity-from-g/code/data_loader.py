"""
Data Loading Utilities (T013, T018, T026)

Functions:
- load_smiles: Load SMILES from a CSV file.
- filter_missing_targets: Drop rows with missing target values.
- load_and_validate_target: Load and validate the target variable.
- validate_target_variable: Check dynamic range and existence.
"""

import os
import sys
import pandas as pd
import numpy as np
from typing import List, Tuple, Optional
import logging

# Add project root to path
if __name__ == "__main__":
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

from code.config import TARGET_VAR, RAW_DATA_PATH, DATA_PATH
from code.logging_config import setup_logging

logger = logging.getLogger(__name__)

def load_smiles(path: str) -> pd.DataFrame:
    """
    Load SMILES from a CSV file.
    Returns a DataFrame with columns [smiles, valid, error_msg].
    T013 Implementation.
    """
    logger.info(f"Loading SMILES from {path}")
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")

    # Try to load as CSV
    try:
        df = pd.read_csv(path)
    except Exception as e:
        logger.error(f"Failed to read CSV: {e}")
        raise

    # Ensure 'smiles' column exists
    if 'smiles' not in df.columns:
        # Try common alternatives
        if 'SMILES' in df.columns:
            df['smiles'] = df['SMILES']
        elif 'smile' in df.columns:
            df['smiles'] = df['smile']
        else:
            raise ValueError("No 'smiles' column found in input file.")

    # Initialize validity columns
    df['valid'] = True
    df['error_msg'] = ""

    # Basic validation (SMILES string not empty)
    df['valid'] = df['smiles'].astype(str).str.strip() != ""
    df.loc[~df['valid'], 'error_msg'] = "Empty or invalid SMILES string"

    logger.info(f"Loaded {len(df)} rows from {path}")
    return df

def filter_missing_targets(df: pd.DataFrame, target_col: str) -> pd.DataFrame:
    """
    Filter out rows where the target column is NaN or missing.
    T018 Implementation.
    """
    if target_col not in df.columns:
        logger.warning(f"Target column '{target_col}' not found. Returning original DataFrame.")
        return df

    initial_count = len(df)
    # Drop rows where target_col is NaN
    df_filtered = df.dropna(subset=[target_col])
    dropped_count = initial_count - len(df_filtered)

    if dropped_count > 0:
        logger.info(f"Dropped {dropped_count} rows with missing target values ({target_col}).")
    else:
        logger.info("No rows dropped due to missing target values.")

    return df_filtered

def load_and_validate_target(path: str) -> Tuple[pd.DataFrame, str]:
    """
    Load raw data, check for target variable, and return the DataFrame with the target column.
    T026 Implementation (partial).
    """
    logger.info(f"Loading and validating target from {path}")
    df = pd.read_csv(path)

    # Check for conductivity or charge_carrier_mobility
    target_candidates = ['conductivity', 'charge_carrier_mobility']
    found_target = None

    for candidate in target_candidates:
        if candidate in df.columns:
            found_target = candidate
            break

    if found_target:
        # Check dynamic range (>= 3 orders of magnitude)
        # We assume the values are already in log scale or need to be log-transformed.
        # FR-011: Dynamic range >= 3 orders of magnitude.
        # We check the range of log10(values) if values are positive.
        valid_data = df[found_target].dropna()
        if len(valid_data) > 0:
            positive_data = valid_data[valid_data > 0]
            if len(positive_data) > 0:
                log_range = np.log10(positive_data.max()) - np.log10(positive_data.min())
                if log_range < 3.0:
                    logger.warning(f"Target '{found_target}' has dynamic range < 3 orders of magnitude ({log_range:.2f}).")
                    # Per T026, we might fall back, but for now we just log.
            else:
                logger.warning(f"No positive values in target '{found_target}'.")
    else:
        # Check for HOMO_LUMO_gap
        if 'HOMO_LUMO_gap' in df.columns:
            found_target = 'HOMO_LUMO_gap'
            logger.warning("Conductivity missing. Using HOMO-LUMO gap as proxy per Plan Scope Adjustment.")
        else:
            # Compute empirical proxy (T026 fallback)
            logger.warning("No direct target found. Using empirical proxy.")
            # This requires descriptors to be computed first, so we return a flag.
            found_target = 'log_conductivity_proxy'

    return df, found_target

def validate_target_variable(df: pd.DataFrame, target_col: str) -> bool:
    """
    Validate that the target variable has a sufficient dynamic range.
    """
    if target_col not in df.columns:
        return False

    valid_data = df[target_col].dropna()
    if len(valid_data) == 0:
        return False

    positive_data = valid_data[valid_data > 0]
    if len(positive_data) == 0:
        return False

    log_range = np.log10(positive_data.max()) - np.log10(positive_data.min())
    return log_range >= 3.0

def apply_log_transformation(df: pd.DataFrame, target_col: str) -> pd.DataFrame:
    """
    Apply natural logarithm to the target variable.
    """
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found.")

    df[f"log_{target_col}"] = np.log(df[target_col])
    return df

def process_molecule_with_error_handling(smiles: str) -> Optional[dict]:
    """
    Process a single SMILES string with error handling.
    """
    try:
        # Placeholder for molecule processing logic
        # In a real scenario, this would compute descriptors
        return {"smiles": smiles, "valid": True}
    except Exception as e:
        logger.error(f"Error processing SMILES '{smiles}': {e}")
        return None

def load_processed_data(path: str) -> pd.DataFrame:
    """
    Load processed data from a CSV file.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Processed data file not found: {path}")
    return pd.read_csv(path)

def main():
    """CLI for testing data loading."""
    import argparse
    parser = argparse.ArgumentParser(description="Test data loading.")
    parser.add_argument("--path", type=str, default=RAW_DATA_PATH, help="Path to data file.")
    args = parser.parse_args()

    setup_logging()
    try:
        df = load_smiles(args.path)
        print(f"Loaded {len(df)} rows.")
        print(df.head())
    except Exception as e:
        logger.error(f"Failed: {e}")
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
