"""
T015a: Filter descriptor dataset by missing values.

Excludes entries with >= 2 missing descriptor values and logs exclusion counts.
Writes filtered dataset to data/processed/descriptors_filtered.csv.
Writes exclusion log to data/processed/exclusion_log.csv.
"""
import logging
import sys
from pathlib import Path
from typing import Tuple

import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# Define paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_PATH = PROJECT_ROOT / "data" / "processed" / "descriptors_features.csv"
OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "descriptors_filtered.csv"
LOG_PATH = PROJECT_ROOT / "data" / "processed" / "exclusion_log.csv"

# Columns to check for missing values (descriptor columns)
# Based on T014b, T014c, T014e outputs:
DESCRIPTOR_COLUMNS = [
    "atomic_fraction_A",
    "atomic_fraction_B",
    "atomic_fraction_X",
    "weighted_ionic_radius",
    "weighted_electronegativity",
    "weighted_formation_enthalpy",
    "first_ionization_energy",
    "variance_ionic_radius",
    "variance_electronegativity",
]

# Columns that should be present but are not checked for missing values
# (e.g., formula, T_d, perovskite_family, total_uncertainty, etc.)
NON_DESCRIPTOR_COLUMNS = [
    "formula",
    "T_d",
    "source",
    "perovskite_family",
    "total_uncertainty",
    "instrument_model",
    "manufacturer",
    "precision_source",
    "precision_from_registry",
    "precision_celsius",
    "heating_rate",
]

def load_descriptors() -> pd.DataFrame:
    """Load the descriptors dataset."""
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_PATH}. "
            "Run T014c (feature engineering) before T015a."
        )
    logger.info(f"Loading descriptors from {INPUT_PATH}")
    df = pd.read_csv(INPUT_PATH)
    logger.info(f"Loaded {len(df)} rows")
    return df

def count_missing_values(df: pd.DataFrame) -> pd.Series:
    """Count missing values per row for descriptor columns."""
    return df[DESCRIPTOR_COLUMNS].isna().sum(axis=1)

def filter_entries(df: pd.DataFrame, threshold: int = 2) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Filter entries with >= threshold missing descriptor values.

    Returns:
        Tuple of (filtered_df, excluded_df)
    """
    missing_counts = count_missing_values(df)
    excluded_mask = missing_counts >= threshold
    filtered_mask = ~excluded_mask

    filtered_df = df[filtered_mask].reset_index(drop=True)
    excluded_df = df[excluded_mask].copy()
    excluded_df["missing_count"] = missing_counts[excluded_mask]

    logger.info(f"Total rows: {len(df)}")
    logger.info(f"Rows with >= {threshold} missing descriptors: {excluded_mask.sum()}")
    logger.info(f"Rows kept: {filtered_mask.sum()}")

    return filtered_df, excluded_df

def save_filtered_data(df: pd.DataFrame, path: Path) -> None:
    """Save the filtered dataset."""
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    logger.info(f"Saved filtered dataset to {path} ({len(df)} rows)")

def log_exclusion_counts(excluded_df: pd.DataFrame, log_path: Path) -> None:
    """Log exclusion counts to a CSV file."""
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Create a summary of exclusion counts
    summary_data = []
    if not excluded_df.empty:
        missing_counts = excluded_df["missing_count"]
        for count in sorted(missing_counts.unique()):
            summary_data.append({
                "missing_count": count,
                "excluded_count": (missing_counts == count).sum(),
            })

    summary_df = pd.DataFrame(summary_data)

    # Also include formula details for debugging
    if not excluded_df.empty:
        excluded_df["missing_count"] = excluded_df["missing_count"].astype(int)
        details_df = excluded_df[["formula", "missing_count"]]
        details_df.to_csv(log_path.with_name("exclusion_details.csv"), index=False)
        logger.info(f"Saved exclusion details to {log_path.with_name('exclusion_details.csv')}")

    summary_df.to_csv(log_path, index=False)
    logger.info(f"Saved exclusion summary to {log_path}")

def main() -> None:
    """Main entry point for T015a."""
    logger.info("Starting T015a: Filter descriptors by missing values")

    try:
        # Load data
        df = load_descriptors()

        # Verify required columns exist
        missing_cols = [col for col in DESCRIPTOR_COLUMNS if col not in df.columns]
        if missing_cols:
            raise ValueError(
                f"Missing required descriptor columns: {missing_cols}. "
                f"Available columns: {df.columns.tolist()}"
            )

        # Filter entries
        filtered_df, excluded_df = filter_entries(df, threshold=2)

        # Save filtered dataset
        save_filtered_data(filtered_df, OUTPUT_PATH)

        # Log exclusion counts
        log_exclusion_counts(excluded_df, LOG_PATH)

        logger.info("T015a completed successfully")

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
