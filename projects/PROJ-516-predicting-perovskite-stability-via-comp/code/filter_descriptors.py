"""
Filter descriptors based on missing values.

This module implements T015a: Exclude entries with ≥ 2 missing descriptor values
and log exclusion counts.

It reads from data/processed/descriptors_vif_filtered.csv and writes to
data/processed/descriptors_final_filtered.csv.
"""
import logging
import sys
from pathlib import Path
from typing import Tuple, Set

import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("data/processed/exclusion_log.csv", mode="w")
    ]
)
logger = logging.getLogger(__name__)

# Define paths
INPUT_PATH = Path("data/processed/descriptors_vif_filtered.csv")
OUTPUT_PATH = Path("data/processed/descriptors_final_filtered.csv")
EXCLUSION_LOG_PATH = Path("data/processed/exclusion_log.csv")
EXCLUSION_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

# Descriptor columns to check for missing values.
# These are the compositional fingerprint features.
DESCRIPTOR_COLUMNS = [
    "atomic_fraction_A",
    "atomic_fraction_B",
    "atomic_fraction_X",
    "weighted_ionic_radius",
    "weighted_electronegativity",
    "weighted_formation_enthalpy",
    "first_ionization_energy",
    "variance_ionic_radius",
    "variance_electronegativity"
]

def load_descriptors() -> pd.DataFrame:
    """Load the VIF-filtered descriptors dataset."""
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Input file {INPUT_PATH} not found. "
            "Ensure T016d (VIF filtering) has completed successfully."
        )
    df = pd.read_csv(INPUT_PATH)
    logger.info(f"Loaded {len(df)} rows from {INPUT_PATH}")
    return df

def count_missing_values(df: pd.DataFrame, columns: Set[str]) -> pd.Series:
    """Count missing values per row for the specified columns."""
    return df[list(columns)].isna().sum(axis=1)

def filter_entries(df: pd.DataFrame, threshold: int = 2) -> Tuple[pd.DataFrame, int]:
    """
    Filter out entries with >= threshold missing descriptor values.

    Args:
        df: Input DataFrame
        threshold: Number of missing values that triggers exclusion (default 2)

    Returns:
        Tuple of (filtered DataFrame, count of excluded rows)
    """
    # Ensure we only check columns that exist in the dataframe
    available_descriptors = [col for col in DESCRIPTOR_COLUMNS if col in df.columns]
    if not available_descriptors:
        logger.warning("No descriptor columns found in the dataset.")
        return df, 0

    missing_counts = count_missing_values(df, set(available_descriptors))
    excluded_mask = missing_counts >= threshold
    excluded_count = excluded_mask.sum()

    filtered_df = df[~excluded_mask].copy()

    logger.info(f"Excluding {excluded_count} rows with >= {threshold} missing descriptor values.")
    return filtered_df, excluded_count

def save_filtered_data(df: pd.DataFrame, output_path: Path) -> None:
    """Save the filtered dataset to CSV."""
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(df)} rows to {output_path}")

def log_exclusion_counts(excluded_count: int, total_rows: int, features_count: int) -> None:
    """
    Log exclusion counts to the exclusion log file.

    This includes the count of excluded rows and the verification threshold check.
    """
    # Log to the exclusion log file (which we opened as a file handler)
    logger.info(f"Total rows before filtering: {total_rows}")
    logger.info(f"Rows excluded: {excluded_count}")
    logger.info(f"Rows remaining: {total_rows - excluded_count}")
    logger.info(f"Number of features after VIF filtering: {features_count}")

    # Check the threshold condition: n >= 10 * features
    remaining_rows = total_rows - excluded_count
    min_required_rows = 10 * features_count

    if remaining_rows < min_required_rows:
        logger.warning(
            f"WARNING: Remaining rows ({remaining_rows}) is less than "
            f"10x features ({min_required_rows}). Model training may be unreliable."
        )
    else:
        logger.info(
            f"Verification passed: {remaining_rows} >= {min_required_rows} (10x features)."
        )

def main() -> None:
    """Main entry point for T015a."""
    try:
        # Load data
        df = load_descriptors()
        total_rows = len(df)

        # Count features after VIF filtering (excluding non-descriptor columns)
        # We assume the first few columns are metadata (formula, T_d, etc.)
        # and the rest are descriptors.
        descriptor_cols_in_df = [col for col in DESCRIPTOR_COLUMNS if col in df.columns]
        features_count = len(descriptor_cols_in_df)

        if features_count == 0:
            logger.error("No descriptor columns found. Cannot proceed with filtering.")
            sys.exit(1)

        # Filter entries
        filtered_df, excluded_count = filter_entries(df, threshold=2)

        # Log exclusion counts
        log_exclusion_counts(excluded_count, total_rows, features_count)

        # Save filtered data
        save_filtered_data(filtered_df, OUTPUT_PATH)

        logger.info("T015a completed successfully.")

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during filtering: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()