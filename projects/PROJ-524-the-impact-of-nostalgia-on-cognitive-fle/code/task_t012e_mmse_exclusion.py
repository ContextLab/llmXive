"""
Task T012e: MMSE Exclusion (Data Generation)

Reads the MMSE flag from data/processed/mmse_flag.json.
If has_mmse is True:
  - Filters data/processed/cleaned_score_filtered.csv for MMSE >= 24
  - Writes result to data/processed/cleaned_dataset.csv
If has_mmse is False:
  - Copies data/processed/cleaned_score_filtered.csv to data/processed/cleaned_dataset.csv

CRITICAL: Also generates data/processed/cleaned_dataset_no_mmse.csv by copying
data/processed/cleaned_score_filtered.csv (to preserve pre-MMSE state for sensitivity analysis).

Updates data/processed/exclusion_counts.json with the count of excluded records (ERR_MMSE_IMPAIRED).
"""
import os
import json
import logging
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define paths
PROJECT_ROOT = Path(__file__).parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
MMSE_FLAG_PATH = PROCESSED_DIR / "mmse_flag.json"
SCORE_FILTERED_PATH = PROCESSED_DIR / "cleaned_score_filtered.csv"
CLEANED_DATASET_PATH = PROCESSED_DIR / "cleaned_dataset.csv"
NO_MMSE_DATASET_PATH = PROCESSED_DIR / "cleaned_dataset_no_mmse.csv"
EXCLUSION_COUNTS_PATH = PROCESSED_DIR / "exclusion_counts.json"

MMSE_THRESHOLD = 24

def load_score_filtered_dataset() -> pd.DataFrame:
    """Load the score-filtered dataset."""
    if not SCORE_FILTERED_PATH.exists():
        raise FileNotFoundError(
            f"Required input file missing: {SCORE_FILTERED_PATH}. "
            "Ensure T012b has been completed successfully."
        )
    logger.info(f"Loading score-filtered dataset from {SCORE_FILTERED_PATH}")
    df = pd.read_csv(SCORE_FILTERED_PATH)
    logger.info(f"Loaded {len(df)} records")
    return df

def load_mmse_flag() -> Dict[str, Any]:
    """Load the MMSE flag from JSON."""
    if not MMSE_FLAG_PATH.exists():
        raise FileNotFoundError(
            f"Required input file missing: {MMSE_FLAG_PATH}. "
            "Ensure T012d has been completed successfully."
        )
    logger.info(f"Loading MMSE flag from {MMSE_FLAG_PATH}")
    with open(MMSE_FLAG_PATH, 'r') as f:
        return json.load(f)

def filter_mmse(df: pd.DataFrame, has_mmse: bool) -> tuple[pd.DataFrame, int]:
    """
    Filter dataset based on MMSE presence and threshold.

    Args:
        df: Input dataframe
        has_mmse: Whether MMSE column exists and has non-null values

    Returns:
        Tuple of (filtered dataframe, count of excluded records)
    """
    initial_count = len(df)
    excluded_count = 0

    if has_mmse:
        if 'MMSE' not in df.columns:
            logger.warning("MMSE column missing from dataset despite flag indicating presence. Skipping filter.")
            return df, 0

        # Filter for MMSE >= 24
        # Handle potential NaNs in MMSE column by treating them as excluded
        valid_mask = df['MMSE'].notna() & (df['MMSE'] >= MMSE_THRESHOLD)
        excluded_count = initial_count - valid_mask.sum()
        filtered_df = df[valid_mask].reset_index(drop=True)
        logger.info(f"Filtered for MMSE >= {MMSE_THRESHOLD}. Excluded {excluded_count} records.")
    else:
        logger.info("has_mmse is False. No MMSE filtering applied.")
        filtered_df = df.copy()

    return filtered_df, excluded_count

def update_exclusion_counts(excluded_count: int) -> Dict[str, Any]:
    """Update the exclusion counts JSON file."""
    if EXCLUSION_COUNTS_PATH.exists():
        with open(EXCLUSION_COUNTS_PATH, 'r') as f:
            counts = json.load(f)
    else:
        counts = {
            "ERR_MISSING_AGE_FIELD": 0,
            "ERR_MISSING_SCORE": 0,
            "ERR_MMSE_IMPAIRED": 0
        }

    current_mmse_excluded = counts.get("ERR_MMSE_IMPAIRED", 0)
    counts["ERR_MMSE_IMPAIRED"] = current_mmse_excluded + excluded_count

    logger.info(f"Updated exclusion counts: ERR_MMSE_IMPAIRED = {counts['ERR_MMSE_IMPAIRED']}")
    return counts

def save_exclusion_counts(counts: Dict[str, Any]) -> None:
    """Save exclusion counts to JSON file."""
    with open(EXCLUSION_COUNTS_PATH, 'w') as f:
        json.dump(counts, f, indent=2)
    logger.info(f"Saved exclusion counts to {EXCLUSION_COUNTS_PATH}")

def save_cleaned_dataset(df: pd.DataFrame, path: Path) -> None:
    """Save the cleaned dataset to CSV."""
    df.to_csv(path, index=False)
    logger.info(f"Saved cleaned dataset ({len(df)} records) to {path}")

def main() -> None:
    """Main execution function for T012e."""
    logger.info("Starting Task T012e: MMSE Exclusion (Data Generation)")

    try:
        # Load inputs
        mmse_flag = load_mmse_flag()
        has_mmse = mmse_flag.get("has_mmse", False)
        
        df_score_filtered = load_score_filtered_dataset()

        # Filter based on MMSE flag
        df_cleaned, mmse_excluded = filter_mmse(df_score_filtered, has_mmse)

        # Generate cleaned_dataset_no_mmse.csv (copy of pre-MMSE state)
        # This preserves the dataset before MMSE exclusion for sensitivity analysis (T027)
        save_cleaned_dataset(df_score_filtered, NO_MMSE_DATASET_PATH)

        # Generate cleaned_dataset.csv (final filtered dataset)
        save_cleaned_dataset(df_cleaned, CLEANED_DATASET_PATH)

        # Update exclusion counts
        counts = update_exclusion_counts(mmse_excluded)
        save_exclusion_counts(counts)

        logger.info("Task T012e completed successfully.")
        logger.info(f"  - Created: {CLEANED_DATASET_PATH} ({len(df_cleaned)} records)")
        logger.info(f"  - Created: {NO_MMSE_DATASET_PATH} ({len(df_score_filtered)} records)")
        logger.info(f"  - Updated: {EXCLUSION_COUNTS_PATH}")

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during T012e execution: {e}")
        raise

if __name__ == "__main__":
    main()