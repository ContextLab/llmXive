"""
Filter descriptors to exclude entries with excessive missing values.

Implements T015: Exclude entries with ≥2 missing descriptor values and log exclusion counts.
"""
import logging
import sys
from pathlib import Path
from typing import Tuple

import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Define the path constants based on project structure
PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_PATH = PROJECT_ROOT / "data" / "processed" / "descriptors.csv"
OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "descriptors_filtered.csv"
LOG_PATH = PROJECT_ROOT / "data" / "processed" / "filter_exclusion_log.txt"

def load_descriptors(path: Path = INPUT_PATH) -> pd.DataFrame:
    """Load the descriptors DataFrame from CSV."""
    if not path.exists():
        raise FileNotFoundError(f"Input descriptors file not found: {path}")
    logger.info(f"Loading descriptors from {path}")
    return pd.read_csv(path)

def count_missing_values(df: pd.DataFrame) -> int:
    """
    Count the number of missing values per row in the descriptor columns.
    Excludes the target variable 'T_d' and index/ID columns if present.
    """
    # Identify descriptor columns (exclude 'T_d', 'formula', 'id' if they exist)
    exclude_cols = {'T_d', 'formula', 'id', 'T_d_uncertainty'}
    descriptor_cols = [col for col in df.columns if col not in exclude_cols]
    
    if not descriptor_cols:
        raise ValueError("No descriptor columns found to check for missing values.")
    
    # Count missing values per row across descriptor columns
    missing_counts = df[descriptor_cols].isna().sum(axis=1)
    return missing_counts

def filter_entries(df: pd.DataFrame, max_missing: int = 1) -> Tuple[pd.DataFrame, int]:
    """
    Filter entries to keep only those with <= max_missing missing values.
    Default max_missing is 1, meaning we exclude entries with >= 2 missing values.
    
    Args:
        df: Input DataFrame
        max_missing: Maximum allowed missing values per row (default 1)
        
    Returns:
        Tuple of (filtered DataFrame, count of excluded rows)
    """
    missing_counts = count_missing_values(df)
    
    # Filter rows where missing count is within the limit
    valid_mask = missing_counts <= max_missing
    filtered_df = df[valid_mask].reset_index(drop=True)
    
    excluded_count = len(df) - len(filtered_df)
    
    logger.info(f"Total rows before filtering: {len(df)}")
    logger.info(f"Rows excluded (missing values > {max_missing}): {excluded_count}")
    logger.info(f"Rows remaining after filtering: {len(filtered_df)}")
    
    return filtered_df, excluded_count

def save_filtered_data(df: pd.DataFrame, path: Path = OUTPUT_PATH) -> None:
    """Save the filtered DataFrame to CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    logger.info(f"Filtered descriptors saved to {path}")

def log_exclusion_counts(excluded_count: int, path: Path = LOG_PATH) -> None:
    """Log the exclusion counts to a text file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        f.write(f"Filter Exclusion Log\n")
        f.write(f"====================\n")
        f.write(f"Exclusion Criteria: Exclude entries with >= 2 missing descriptor values.\n")
        f.write(f"Total Entries Excluded: {excluded_count}\n")
        f.write(f"Output File: {OUTPUT_PATH}\n")
    logger.info(f"Exclusion log saved to {path}")

def main() -> None:
    """Main entry point for the filtering script."""
    try:
        # Load data
        df = load_descriptors()
        
        # Filter entries (exclude if >= 2 missing)
        filtered_df, excluded_count = filter_entries(df, max_missing=1)
        
        # Save results
        save_filtered_data(filtered_df)
        log_exclusion_counts(excluded_count)
        
        logger.info("Filtering completed successfully.")
        
    except Exception as e:
        logger.error(f"Error during filtering process: {e}")
        raise

if __name__ == "__main__":
    main()
