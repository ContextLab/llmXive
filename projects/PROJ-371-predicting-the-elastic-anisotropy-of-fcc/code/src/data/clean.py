"""
Data cleaning module for elastic anisotropy dataset.

Filters for single-phase FCC entries, handles edge cases for division by zero,
and calculates the Zener anisotropy ratio A1.
"""
import os
import sys
import logging
from pathlib import Path
from typing import Optional

import pandas as pd

# Add project root to path for imports if running as script
if "code" in os.getcwd():
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.config import get_path
from src.utils.logging import get_logger, log_info, log_warning, log_error, log_success

# Configure logger for this module
logger = get_logger(__name__)

def clean_elastic_data(
    input_path: Optional[str] = None,
    output_path: Optional[str] = None,
    min_entries: int = 1
) -> pd.DataFrame:
    """
    Clean the elastic constants dataset.
    
    Operations:
    1. Filter for single-phase FCC entries (assuming 'phase' column or similar indicator).
       Since the specific column name for phase isn't defined in the prompt's API surface,
       we assume the input data from T012 (ingest) already contains a 'structure' or 'phase'
       column indicating FCC, or we filter by the presence of all required elastic constants.
       Based on standard practices in this domain, we will filter rows where C11, C12, C44 exist.
       If a 'structure' column exists with value 'FCC', we use that.
    2. Exclude entries where C11 == C12 to prevent division by zero in A1 calculation.
    3. Calculate A1 = 2 * C44 / (C11 - C12).
    4. Log removed entries and final dataset statistics.
    
    Args:
        input_path: Path to the input CSV (default: data/processed/ingested_elastic.csv).
        output_path: Path to save the cleaned CSV (default: data/processed/cleaned_elastic.csv).
        min_entries: Minimum number of entries required to proceed (safety check).
        
    Returns:
        Cleaned DataFrame with A1 column added.
    """
    # Resolve paths
    if input_path is None:
        input_path = get_path("data_processed", "ingested_elastic.csv")
    else:
        input_path = get_path("data_processed", input_path) if not Path(input_path).is_absolute() else input_path
        
    if output_path is None:
        output_path = get_path("data_processed", "cleaned_elastic.csv")
    else:
        output_path = get_path("data_processed", output_path) if not Path(output_path).is_absolute() else output_path

    input_path = Path(input_path)
    output_path = Path(output_path)

    if not input_path.exists():
        error_msg = f"Input file not found: {input_path}"
        log_error(error_msg)
        raise FileNotFoundError(error_msg)

    log_info(f"Loading data from {input_path}")
    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        log_error(f"Failed to read CSV: {e}")
        raise

    initial_count = len(df)
    log_info(f"Loaded {initial_count} rows")

    # 1. Filter for single-phase FCC entries
    # Check if a structural identifier column exists
    structural_cols = [col for col in df.columns if col.lower() in ["structure", "phase", "crystal_system", "bravais_lattice"]]
    
    if structural_cols:
        # Prefer 'structure' or 'phase' if available
        target_col = structural_cols[0]
        log_info(f"Filtering by {target_col} == 'FCC'")
        # Case-insensitive check for FCC
        fcc_mask = df[target_col].astype(str).str.upper().str.contains("FCC")
        df = df[fcc_mask]
        dropped_struct = initial_count - len(df)
        if dropped_struct > 0:
            log_warning(f"Dropped {dropped_struct} rows due to non-FCC structure")
    else:
        log_warning("No structural column found; assuming all entries are FCC based on input source.")

    # 2. Ensure required columns exist
    required_cols = ["C11", "C12", "C44"]
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        error_msg = f"Missing required elastic constant columns: {missing_cols}"
        log_error(error_msg)
        raise ValueError(error_msg)

    # Convert to numeric, coercing errors to NaN
    for col in required_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Drop rows with any missing elastic constants
    before_na = len(df)
    df = df.dropna(subset=required_cols)
    dropped_na = before_na - len(df)
    if dropped_na > 0:
        log_warning(f"Dropped {dropped_na} rows due to missing elastic constant values")

    # 3. Exclude entries where C11 == C12 (prevents division by zero)
    # Use a small tolerance for floating point comparison if needed, but strict equality is safer for data integrity
    before_zero = len(df)
    # Using a small epsilon for float comparison safety
    epsilon = 1e-6
    valid_diff_mask = (df["C11"] - df["C12"]).abs() > epsilon
    df = df[valid_diff_mask]
    dropped_zero = before_zero - len(df)
    if dropped_zero > 0:
        log_warning(f"Dropped {dropped_zero} rows where C11 approx equals C12 (division by zero risk)")

    # 4. Calculate A1 = 2 * C44 / (C11 - C12)
    df["A1"] = 2 * df["C44"] / (df["C11"] - df["C12"])
    log_info("Calculated Zener Anisotropy Ratio (A1)")

    # Validate A1 values (Physical bounds: A1 should be > 0 for stable FCC, though theoretical range varies)
    # We do not drop negative values here as they might indicate unstable phases or measurement errors,
    # but we log them.
    negative_a1 = df[df["A1"] <= 0]
    if len(negative_a1) > 0:
        log_warning(f"Found {len(negative_a1)} entries with A1 <= 0. These may be physically unstable.")

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save to CSV
    df.to_csv(output_path, index=False)
    log_success(f"Cleaned dataset saved to {output_path} ({len(df)} rows)")

    if len(df) < min_entries:
        log_error(f"Final dataset size ({len(df)}) is below minimum required ({min_entries})")
        raise ValueError(f"Insufficient data: {len(df)} < {min_entries}")

    return df

def main():
    """Entry point for running the cleaning script directly."""
    try:
        clean_elastic_data()
    except Exception as e:
        log_error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
