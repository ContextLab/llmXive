"""
Data cleaning module for elastic anisotropy pipeline.

Filters for single-phase FCC entries, excludes entries where C11=C12
(preventing division by zero in A1), and calculates A1 = 2*C44 / (C11-C12).
"""
import os
import sys
import logging
from pathlib import Path
from typing import Optional

import pandas as pd

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.utils.logging import get_logger, log_info, log_warning, log_error, log_debug
from src.utils.config import get_path, ensure_directories

# Initialize logger
logger = get_logger(__name__)

def clean_elastic_data(
    input_path: Optional[str] = None,
    output_path: Optional[str] = None,
    fcc_only: bool = True
) -> pd.DataFrame:
    """
    Clean elastic constants data by filtering FCC entries and calculating anisotropy.
    
    Args:
        input_path: Path to input CSV file. Defaults to config path.
        output_path: Path to output CSV file. Defaults to config path.
        fcc_only: If True, filter for single-phase FCC entries only.
        
    Returns:
        Cleaned DataFrame with calculated A1 values.
        
    Raises:
        FileNotFoundError: If input file does not exist.
        ValueError: If required columns are missing.
    """
    # Resolve paths
    if input_path is None:
        input_path = get_path("data_processed", "elastic_constants_raw.csv")
    if output_path is None:
        output_path = get_path("data_processed", "elastic_anisotropy.csv")
    
    input_file = Path(input_path)
    output_file = Path(output_path)
    
    # Ensure output directory exists
    ensure_directories([output_file.parent])
    
    # Load data
    log_info(logger, f"Loading data from {input_file}")
    if not input_file.exists():
        log_error(logger, f"Input file not found: {input_file}")
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    try:
        df = pd.read_csv(input_file)
    except Exception as e:
        log_error(logger, f"Failed to read CSV: {e}")
        raise
    
    log_debug(logger, f"Loaded {len(df)} rows")
    
    # Validate required columns
    required_cols = ["C11", "C12", "C44"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        msg = f"Missing required columns: {missing_cols}"
        log_error(logger, msg)
        raise ValueError(msg)
    
    initial_count = len(df)
    
    # Filter for FCC entries if requested
    if fcc_only:
        # Check if crystal_system column exists
        if "crystal_system" in df.columns:
            fcc_count = (df["crystal_system"] == "fcc").sum()
            log_info(logger, f"Found {fcc_count} FCC entries out of {initial_count}")
            
            if fcc_count == 0:
                log_warning(logger, "No FCC entries found in dataset")
            
            df = df[df["crystal_system"] == "fcc"].copy()
        else:
            log_warning(logger, "No 'crystal_system' column found, skipping FCC filter")
    
    fcc_count = len(df)
    log_info(logger, f"After FCC filter: {fcc_count} rows (dropped {initial_count - fcc_count})")
    
    # Exclude entries where C11 == C12 to prevent division by zero
    if "C11" in df.columns and "C12" in df.columns:
        zero_diff_mask = df["C11"] == df["C12"]
        zero_diff_count = zero_diff_mask.sum()
        if zero_diff_count > 0:
            log_warning(logger, f"Excluding {zero_diff_count} entries where C11 == C12")
            df = df[~zero_diff_mask].copy()
    
    # Check for NaN values in required columns before calculation
    nan_mask = df[["C11", "C12", "C44"]].isna().any(axis=1)
    nan_count = nan_mask.sum()
    if nan_count > 0:
        log_warning(logger, f"Excluding {nan_count} entries with NaN in C11, C12, or C44")
        df = df[~nan_mask].copy()
    
    # Calculate A1 = 2*C44 / (C11 - C12)
    df["A1"] = (2 * df["C44"]) / (df["C11"] - df["C12"])
    
    # Log statistics
    log_info(logger, f"Calculated A1 for {len(df)} entries")
    log_debug(logger, f"A1 stats: min={df['A1'].min():.4f}, max={df['A1'].max():.4f}, mean={df['A1'].mean():.4f}")
    
    # Save to output
    log_info(logger, f"Saving cleaned data to {output_file}")
    df.to_csv(output_file, index=False)
    
    log_success(logger if hasattr(logger, 'success') else logger, 
               f"Cleaned data saved: {len(df)} rows -> {output_file}")
    
    return df

def main():
    """Main entry point for cleaning script."""
    log_info(logger, "Starting elastic data cleaning pipeline")
    
    try:
        df = clean_elastic_data()
        log_info(logger, f"Successfully cleaned data. Output: {len(df)} rows")
        return 0
    except FileNotFoundError as e:
        log_error(logger, f"File not found: {e}")
        return 1
    except ValueError as e:
        log_error(logger, f"Validation error: {e}")
        return 2
    except Exception as e:
        log_error(logger, f"Unexpected error: {e}")
        raise

if __name__ == "__main__":
    sys.exit(main())
