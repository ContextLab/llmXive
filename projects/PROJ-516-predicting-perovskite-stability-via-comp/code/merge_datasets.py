"""
Merge logic for perovskite datasets from NREL and Materials Project.
Implements T012c: Concatenate data/raw/nrel_perovskites.csv and data/raw/mp_perovskites.csv
based on 'formula' and 'source'.
"""
import logging
import sys
from pathlib import Path
from typing import Tuple, Optional
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
NREL_PATH = PROJECT_ROOT / "data" / "raw" / "nrel_perovskites.csv"
MP_PATH = PROJECT_ROOT / "data" / "raw" / "mp_perovskites.csv"
MERGED_PATH = PROJECT_ROOT / "data" / "raw" / "perovskites_merged.csv"

def load_csv_safe(file_path: Path) -> Optional[pd.DataFrame]:
    """
    Safely load a CSV file. Returns None if file is missing or empty.
    """
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return None

    try:
        df = pd.read_csv(file_path)
        if df.empty:
            logger.error(f"File is empty: {file_path}")
            return None
        return df
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        return None

def merge_perovskite_datasets() -> Tuple[bool, str]:
    """
    Main merge logic for T012c.
    Concatenates NREL and MP datasets.
    Returns (success: bool, message: str).
    """
    logger.info("Starting merge process for T012c...")

    # Load NREL data
    nrel_df = load_csv_safe(NREL_PATH)
    if nrel_df is None:
        return False, f"Failed to load NREL data from {NREL_PATH}"

    logger.info(f"Loaded NREL data: {len(nrel_df)} rows")

    # Load MP data
    mp_df = load_csv_safe(MP_PATH)
    if mp_df is None:
        return False, f"Failed to load MP data from {MP_PATH}"

    logger.info(f"Loaded MP data: {len(mp_df)} rows")

    # Verify required columns exist
    required_cols = ['formula', 'source']
    for df, name in [(nrel_df, 'NREL'), (mp_df, 'MP')]:
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            return False, f"Missing columns {missing} in {name} dataset"

    # Concatenate datasets
    logger.info("Concatenating datasets...")
    try:
        merged_df = pd.concat([nrel_df, mp_df], ignore_index=True)
    except Exception as e:
        return False, f"Error during concatenation: {e}"

    initial_count = len(merged_df)
    logger.info(f"Total rows before deduplication: {initial_count}")

    # Log duplicate count based on formula + source
    # Note: T012d handles the actual removal, but T012c must log the count of duplicates found
    duplicates_mask = merged_df.duplicated(subset=['formula', 'source'], keep=False)
    # We count pairs that are duplicates. A set of 2 duplicates counts as 1 duplicate entry to remove.
    # However, the task says "logs duplicate count". Usually this implies the number of rows that will be dropped.
    # Let's count how many rows are duplicates (excluding the first occurrence).
    duplicates_to_drop = merged_df.duplicated(subset=['formula', 'source'], keep='first').sum()
    
    logger.info(f"Duplicate count (rows to be dropped by T012d): {duplicates_to_drop}")

    # Write merged dataset
    try:
        MERGED_PATH.parent.mkdir(parents=True, exist_ok=True)
        merged_df.to_csv(MERGED_PATH, index=False)
        logger.info(f"Successfully wrote merged dataset to {MERGED_PATH}")
        logger.info(f"Final row count: {len(merged_df)}")
        return True, f"Merge successful. Wrote {len(merged_df)} rows to {MERGED_PATH}"
    except Exception as e:
        return False, f"Error writing merged file: {e}"

def main():
    """
    Entry point for the merge script.
    """
    success, message = merge_perovskite_datasets()
    if success:
        logger.info(message)
        sys.exit(0)
    else:
        logger.error(message)
        sys.exit(1)

if __name__ == "__main__":
    main()
