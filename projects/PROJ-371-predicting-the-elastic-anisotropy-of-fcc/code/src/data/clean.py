import os
import sys
import logging
from pathlib import Path
from typing import Optional

import pandas as pd
import numpy as np

# Import project utilities
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.utils.logging import get_logger, log_info, log_warning, log_error, log_success
from src.utils.config import get_path

logger = get_logger(__name__)

def clean_elastic_data(input_path: str, output_path: Optional[str] = None) -> pd.DataFrame:
    """
    Clean the ingested elastic data by:
    1. Filtering for single-phase FCC entries (Crystal system == 'cubic').
    2. Excluding entries where C11 == C12 (prevents division by zero).
    3. Calculating the anisotropy factor A1 = 2*C44 / (C11 - C12).
    4. Handling NaN/Inf values.

    Args:
        input_path: Path to the input CSV (merged MP/AFLOW data).
        output_path: Path to save the cleaned CSV. If None, uses default processed path.

    Returns:
        The cleaned DataFrame.
    """
    if output_path is None:
        output_path = get_path("data_processed", "elastic_anisotropy.csv")

    log_info(logger, f"Loading data from {input_path}")
    try:
        df = pd.read_csv(input_path)
    except FileNotFoundError:
        log_error(logger, f"Input file not found: {input_path}")
        raise
    except Exception as e:
        log_error(logger, f"Failed to read input file: {e}")
        raise

    initial_count = len(df)
    log_info(logger, f"Loaded {initial_count} rows.")

    # Ensure required columns exist
    required_cols = ['C11', 'C12', 'C44']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        log_error(logger, f"Missing required columns in input: {missing_cols}")
        raise ValueError(f"Missing required columns: {missing_cols}")

    # 1. Filter for Cubic Crystal System
    # The column name might vary slightly depending on merge, check common variations
    crystal_col = None
    for col in ['crystal_system', 'symmetry_crystal_system', 'structure_symmetry_crystal_system']:
        if col in df.columns:
            crystal_col = col
            break

    if crystal_col:
        log_info(logger, f"Filtering for cubic crystal system using column: {crystal_col}")
        # Normalize to lowercase for robust comparison
        df = df[df[crystal_col].str.lower() == 'cubic']
        log_success(logger, f"Filtered cubic entries: {len(df)} remaining.")
    else:
        log_warning(logger, "No crystal system column found. Skipping cubic filter. "
                            "Assuming all input is FCC/Cubic or handled upstream.")

    # 2. Exclude entries where C11 == C12 (Division by Zero Prevention)
    # Using a small epsilon for float comparison safety, though exact equality is the spec
    epsilon = 1e-9
    mask_div_zero = np.abs(df['C11'] - df['C12']) > epsilon
    dropped_div_zero = initial_count - len(df) - (len(df) - mask_div_zero.sum()) # Approximate logic
    dropped_div_zero = len(df) - mask_div_zero.sum()
    
    if dropped_div_zero > 0:
        log_warning(logger, f"Dropped {dropped_div_zero} entries where C11 ≈ C12 to prevent division by zero.")
    
    df = df[mask_div_zero]

    # 3. Calculate A1 = 2 * C44 / (C11 - C12)
    log_info(logger, "Calculating Anisotropy Factor A1.")
    df['A1'] = (2.0 * df['C44']) / (df['C11'] - df['C12'])

    # 4. Handle NaN and Inf values resulting from calculation or bad input
    nan_count = df['A1'].isna().sum()
    inf_count = np.isinf(df['A1']).sum()
    
    if nan_count > 0 or inf_count > 0:
        log_warning(logger, f"Found {nan_count} NaN and {inf_count} Inf values in A1. Dropping them.")
        df = df.replace([np.inf, -np.inf], np.nan)
        df = df.dropna(subset=['A1'])

    final_count = len(df)
    log_success(logger, f"Cleaning complete. Started with {initial_count}, ended with {final_count} valid entries.")

    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    log_info(logger, f"Saving cleaned data to {output_path}")
    df.to_csv(output_path, index=False)

    return df

def main():
    """
    CLI entry point for the cleaning task.
    Expects input from the validated ingest stage.
    """
    # Default paths based on project structure
    # Assuming T012c produced data/processed/validated_elastic_data.csv or similar
    # We look for the most recent merged file or a specific name defined in config if available.
    # For now, we assume the pipeline passes the output of T012c to this.
    # If run standalone, we check for a default location.
    
    input_file = get_path("data_processed", "validated_elastic_data.csv")
    if not os.path.exists(input_file):
        # Fallback if T012c output name differs, check raw merged
        input_file = get_path("data_processed", "merged_elastic_data.csv")
    
    if not os.path.exists(input_file):
        log_error(logger, "No validated/merged input file found. Run T012c first.")
        sys.exit(1)

    output_file = get_path("data_processed", "elastic_anisotropy.csv")

    try:
        clean_elastic_data(input_file, output_file)
        log_success(logger, "Task T013 completed successfully.")
    except Exception as e:
        log_error(logger, f"Task T013 failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()