"""
T014: Preprocess the extracted features and exclude cell types with missing ATAC-seq data.

This script loads the raw feature extraction output, identifies cell types missing
ATAC-seq data, excludes them to ensure data integrity, and writes the cleaned
intermediate dataset to a CSV file for T015 to consume.

Output: data/processed/intermediate_ctcf_features.csv
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Set, Any, Optional
import pandas as pd

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

INPUT_FILE = PROJECT_ROOT / "data" / "processed" / "extracted_features.csv"
OUTPUT_FILE = PROJECT_ROOT / "data" / "processed" / "intermediate_ctcf_features.csv"
MIN_CELL_TYPES = 5

def load_processed_dataset() -> pd.DataFrame:
    """Load the dataset produced by extract_features.py."""
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Input file {INPUT_FILE} not found. Run extract_features.py first.")
    return pd.read_csv(INPUT_FILE)

def identify_missing_atac_cells(df: pd.DataFrame) -> Set[str]:
    """
    Identify cell types that have missing ATAC-seq data.
    Assumes 'atac_signal' column contains NaN for missing data.
    """
    missing_atac = df[df['atac_signal'].isna()]
    if missing_atac.empty:
        return set()
    
    # Group by cell_type to see which ones have missing entries
    # If a cell type has ANY missing ATAC data, we exclude the whole type (per spec)
    missing_types = missing_atac['cell_type'].unique().tolist()
    logger.warning(f"Cell types with missing ATAC-seq data: {missing_types}")
    return set(missing_types)

def filter_by_cell_types(df: pd.DataFrame, exclude_types: Set[str]) -> pd.DataFrame:
    """Filter the dataframe to exclude specified cell types."""
    if not exclude_types:
        return df
    
    initial_count = len(df)
    filtered_df = df[~df['cell_type'].isin(exclude_types)]
    final_count = len(filtered_df)
    
    logger.info(f"Filtered out {initial_count - final_count} rows from cell types: {exclude_types}")
    return filtered_df

def check_minimum_cell_types(df: pd.DataFrame) -> bool:
    """Ensure we still have at least MIN_CELL_TYPES after filtering."""
    unique_cells = df['cell_type'].nunique()
    if unique_cells < MIN_CELL_TYPES:
        logger.error(f"Insufficient cell types remaining: {unique_cells} (min: {MIN_CELL_TYPES})")
        return False
    logger.info(f"Remaining cell types: {unique_cells}")
    return True

def generate_scope_revision_trigger():
    """Generate a trigger file if we fall below the minimum cell types."""
    trigger_file = PROJECT_ROOT / "docs" / "scope_revision_trigger.md"
    trigger_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(trigger_file, 'w') as f:
        f.write("# Scope Revision Trigger\n\n")
        f.write("The data filtering process resulted in fewer than the required 5 cell types.\n")
        f.write("Please re-run the data search (T003) or consider imputation strategies.\n")
        f.write("Pipeline halted pending resolution.\n")
    logger.critical(f"Generated scope revision trigger: {trigger_file}")

def main():
    """Main entry point for T014."""
    logger.info("Starting data preprocessing (T014)...")
    
    # Load data
    try:
        df = load_processed_dataset()
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)

    logger.info(f"Loaded {len(df)} rows from {INPUT_FILE}")

    # Identify missing ATAC
    missing_types = identify_missing_atac_cells(df)
    
    if missing_types:
        df = filter_by_cell_types(df, missing_types)
    
    # Check minimum constraint
    if not check_minimum_cell_types(df):
        generate_scope_revision_trigger()
        sys.exit(1)

    # Save intermediate file for T015
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False)
    
    logger.info(f"Saved preprocessed dataset to {OUTPUT_FILE} ({len(df)} rows)")
    logger.info("T014 completed.")

if __name__ == "__main__":
    main()
