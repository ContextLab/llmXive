"""
Download and validate SuperCon dataset for MgB2 impurities.

Fetches the 'taqwa92/cm.mgb2' dataset from HuggingFace, validates that
>50% of entries have impurity data, and saves the raw CSV to data/raw.
Exits with code 1 if validation fails.
"""
import sys
import os
import pandas as pd
from pathlib import Path

# Add project root to path if running as script
project_root = Path(__file__).resolve().parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.utils.logging import get_ingestion_logger

logger = get_ingestion_logger(__name__)

# Configuration
DATASET_ID = "taqwa92/cm.mgb2"
OUTPUT_DIR = project_root / "data" / "raw"
OUTPUT_FILE = OUTPUT_DIR / "supercon_mgb2_raw.csv"

# Threshold for validation: fail if >50% (0.5) of entries lack impurity columns
MAX_NULL_RATIO = 0.5

# Columns that indicate impurity data (case-insensitive check in validation)
IMPURITY_KEYWORDS = ["impurity", "dopant", "substitution", "added", "wt%", "at%"]

def has_impurity_columns(df: pd.DataFrame) -> bool:
    """Check if DataFrame has columns likely to contain impurity data."""
    cols_lower = [str(c).lower() for c in df.columns]
    for keyword in IMPURITY_KEYWORDS:
        if any(keyword in col for col in cols_lower):
            return True
    return False

def validate_impurity_coverage(df: pd.DataFrame) -> float:
    """
    Calculate the ratio of rows that have ANY impurity data.
    
    Returns:
        float: Ratio of rows with impurity data (0.0 to 1.0).
    """
    if df.empty:
        return 0.0
    
    # Identify impurity-related columns
    impurity_cols = []
    for col in df.columns:
        col_lower = str(col).lower()
        if any(kw in col_lower for kw in IMPURITY_KEYWORDS):
            impurity_cols.append(col)
    
    if not impurity_cols:
        logger.warning("No impurity-related columns found in dataset.")
        return 0.0
    
    # Count rows where at least one impurity column is non-null
    valid_rows = df[impurity_cols].notna().any(axis=1).sum()
    total_rows = len(df)
    
    return valid_rows / total_rows

def load_supercon_dataset():
    """
    Load the SuperCon MgB2 dataset from HuggingFace.
    
    Returns:
        pd.DataFrame: The loaded dataset.
    """
    logger.info(f"Loading dataset: {DATASET_ID}")
    
    try:
        from datasets import load_dataset
    except ImportError:
        logger.error("The 'datasets' library is required. Install with: pip install datasets")
        sys.exit(1)
    
    try:
        dataset = load_dataset(DATASET_ID, split="train")
        df = dataset.to_pandas()
        logger.info(f"Successfully loaded {len(df)} rows from {DATASET_ID}")
        return df
    except Exception as e:
        logger.error(f"Failed to load dataset {DATASET_ID}: {e}")
        sys.exit(1)

def main():
    """Main execution function."""
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load data
    df = load_supercon_dataset()
    
    if df.empty:
        logger.error("Dataset is empty. Exiting.")
        sys.exit(1)
    
    # Validate impurity coverage
    valid_ratio = validate_impurity_coverage(df)
    null_ratio = 1.0 - valid_ratio
    
    logger.info(f"Impurity data coverage: {valid_ratio:.2%} ({valid_ratio * len(df):.0f} / {len(df)} rows)")
    logger.info(f"Null ratio for impurity data: {null_ratio:.2%}")
    
    if null_ratio > MAX_NULL_RATIO:
        logger.error(f"CRITICAL: More than {MAX_NULL_RATIO * 100:.0f}% of entries lack impurity data ({null_ratio:.2%}).")
        logger.error("This dataset is insufficient for the current analysis requirements.")
        logger.error("Exiting with code 1.")
        sys.exit(1)
    
    # Save raw data
    df.to_csv(OUTPUT_FILE, index=False)
    logger.info(f"Saved raw dataset to {OUTPUT_FILE}")
    
    logger.info("SuperCon dataset validation passed.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
