"""
T015: Filter descriptor dataset to exclude entries with >= 2 missing values.

This script reads the processed descriptors CSV, counts missing values per row,
excludes entries with 2 or more missing descriptor values, and logs the exclusion
counts to the project log.
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
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(Path(__file__).parent.parent / 'logs' / 'pipeline.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

# Constants
INPUT_PATH = Path(__file__).parent.parent / 'data' / 'processed' / 'descriptors.csv'
OUTPUT_PATH = Path(__file__).parent.parent / 'data' / 'processed' / 'descriptors_cleaned.csv'
MISSING_THRESHOLD = 2  # Exclude entries with >= 2 missing values

def load_descriptors(input_path: Path) -> pd.DataFrame:
    """Load the descriptors CSV file."""
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    logger.info(f"Loading descriptors from {input_path}")
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} rows")
    return df

def count_missing_values(df: pd.DataFrame, exclude_columns: list = None) -> pd.Series:
    """
    Count missing values per row, excluding specified columns.
    
    Args:
        df: Input DataFrame
        exclude_columns: List of column names to exclude from missing value count
                       (e.g., 'formula', 'T_d', 'source_id')
    
    Returns:
        Series with missing value counts per row
    """
    if exclude_columns is None:
        exclude_columns = ['formula', 'T_d', 'source_id', 'T_d_uncertainty']
    
    # Select only numeric/descriptor columns
    descriptor_cols = [col for col in df.columns if col not in exclude_columns]
    
    if not descriptor_cols:
        logger.warning("No descriptor columns found to check for missing values")
        return pd.Series([0] * len(df))
    
    return df[descriptor_cols].isna().sum(axis=1)

def filter_entries(df: pd.DataFrame, threshold: int) -> Tuple[pd.DataFrame, int, int]:
    """
    Filter entries based on missing value count.
    
    Args:
        df: Input DataFrame
        threshold: Exclude entries with >= threshold missing values
    
    Returns:
        Tuple of (filtered DataFrame, original count, excluded count)
    """
    missing_counts = count_missing_values(df)
    
    # Filter: keep rows with missing counts < threshold
    mask = missing_counts < threshold
    filtered_df = df[mask].reset_index(drop=True)
    
    original_count = len(df)
    excluded_count = original_count - len(filtered_df)
    
    logger.info(f"Missing value analysis:")
    logger.info(f"  - Original rows: {original_count}")
    logger.info(f"  - Rows with < {threshold} missing values: {len(filtered_df)}")
    logger.info(f"  - Rows excluded (>= {threshold} missing values): {excluded_count}")
    
    # Log distribution of missing values
    if excluded_count > 0:
        missing_dist = missing_counts.value_counts().sort_index()
        logger.info("Missing value distribution (excluded rows):")
        for count, freq in missing_dist[missing_dist.index >= threshold].items():
            logger.info(f"  - {count} missing values: {freq} rows")
    
    return filtered_df, original_count, excluded_count

def save_filtered_data(df: pd.DataFrame, output_path: Path):
    """Save the filtered DataFrame to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved filtered data to {output_path}")

def main():
    """Main execution function."""
    try:
        # Ensure logs directory exists
        logs_dir = Path(__file__).parent.parent / 'logs'
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Load data
        df = load_descriptors(INPUT_PATH)
        
        # Filter entries
        filtered_df, original_count, excluded_count = filter_entries(df, MISSING_THRESHOLD)
        
        # Save results
        save_filtered_data(filtered_df, OUTPUT_PATH)
        
        # Summary
        logger.info("=" * 50)
        logger.info("T015 EXECUTION COMPLETE")
        logger.info(f"  Input:  {INPUT_PATH} ({original_count} rows)")
        logger.info(f"  Output: {OUTPUT_PATH} ({len(filtered_df)} rows)")
        logger.info(f"  Excluded: {excluded_count} rows (>= {MISSING_THRESHOLD} missing values)")
        logger.info("=" * 50)
        
        return 0
        
    except Exception as e:
        logger.error(f"Execution failed: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())