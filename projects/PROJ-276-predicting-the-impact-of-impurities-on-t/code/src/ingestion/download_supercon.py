import sys
import os
import pandas as pd
from pathlib import Path
from src.utils.logging import get_ingestion_logger

# Ensure we can import from the project root if running as a script
if 'code' not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from datasets import load_dataset

# Constants
DATASET_ID = "taqwa92/cm.mgb2"
MIN_IMPURITY_COVERAGE = 0.50  # 50% threshold
IMPURITY_COLUMNS = [
    "impurity", "impurity_element", "impurity_type", 
    "doping_element", "dopant", "substitution_element"
]

logger = get_ingestion_logger()

def has_impurity_columns(df: pd.DataFrame) -> bool:
    """
    Check if the DataFrame contains any columns that could represent impurities.
    
    Args:
        df: Input DataFrame
        
    Returns:
        True if at least one potential impurity column exists, False otherwise.
    """
    if df.empty:
        return False
    
    # Check for any column that matches our impurity column patterns
    for col in df.columns:
        col_lower = col.lower()
        for pattern in IMPURITY_COLUMNS:
            if pattern.lower() in col_lower:
                return True
    return False

def validate_impurity_coverage(df: pd.DataFrame) -> bool:
    """
    Validate that at least 50% of entries have impurity data.
    
    Args:
        df: Input DataFrame
        
    Returns:
        True if >= 50% of rows have at least one non-null impurity column,
        False otherwise.
        
    Raises:
        SystemExit: If coverage is below threshold (exits with code 1)
    """
    if df.empty:
        logger.error("DataFrame is empty, cannot validate impurity coverage")
        sys.exit(1)
    
    if not has_impurity_columns(df):
        logger.error("No impurity columns found in dataset")
        sys.exit(1)
    
    # Identify actual impurity columns in this dataset
    impurity_cols = []
    for col in df.columns:
        col_lower = col.lower()
        for pattern in IMPURITY_COLUMNS:
            if pattern.lower() in col_lower:
                impurity_cols.append(col)
                break
    
    if not impurity_cols:
        logger.error("No impurity columns found after pattern matching")
        sys.exit(1)
    
    # Count rows with at least one non-null impurity value
    valid_rows = df[impurity_cols].dropna(how='all').shape[0]
    total_rows = df.shape[0]
    
    coverage = valid_rows / total_rows if total_rows > 0 else 0.0
    
    logger.info(f"Total entries: {total_rows}")
    logger.info(f"Entries with impurity data: {valid_rows}")
    logger.info(f"Impurity coverage: {coverage:.2%}")
    
    if coverage < MIN_IMPURITY_COVERAGE:
        logger.error(f"Impurity coverage ({coverage:.2%}) is below threshold ({MIN_IMPURITY_COVERAGE:.0%})")
        logger.error(f"Failing validation: too many entries lack impurity columns")
        sys.exit(1)
    
    logger.info(f"Impurity coverage validation passed: {coverage:.2%} >= {MIN_IMPURITY_COVERAGE:.0%}")
    return True

def load_supercon_dataset() -> pd.DataFrame:
    """
    Load the SuperCon MgB2 dataset from HuggingFace.
    
    Returns:
        DataFrame containing the SuperCon dataset
        
    Raises:
        SystemExit: If dataset loading fails or validation fails
    """
    logger.info(f"Loading SuperCon dataset: {DATASET_ID}")
    
    try:
        # Load dataset with streaming to handle potential size issues
        dataset = load_dataset(DATASET_ID, split="train", streaming=True)
        
        # Convert to DataFrame (materializing only what we need)
        # We'll collect all data since we need to validate coverage
        logger.info("Converting dataset to DataFrame...")
        df = pd.DataFrame(dataset)
        
        logger.info(f"Loaded {len(df)} entries from SuperCon dataset")
        
        # Validate impurity coverage
        validate_impurity_coverage(df)
        
        return df
        
    except Exception as e:
        logger.error(f"Failed to load SuperCon dataset: {e}")
        sys.exit(1)

def main():
    """
    Main entry point for downloading and validating SuperCon dataset.
    
    This script:
    1. Loads the SuperCon MgB2 dataset from HuggingFace
    2. Validates that >= 50% of entries have impurity data
    3. Exits with code 1 if validation fails
    4. Exits with code 0 if validation passes
    
    The validated DataFrame is printed to stdout in CSV format for piping
    to subsequent processing steps.
    """
    logger.info("Starting SuperCon dataset download and validation")
    
    try:
        df = load_supercon_dataset()
        
        # Output the validated DataFrame as CSV to stdout
        # This allows piping to preprocess.py
        logger.info("Validation passed, outputting dataset")
        print(df.to_csv(index=False))
        
        logger.info("SuperCon dataset processing completed successfully")
        sys.exit(0)
        
    except SystemExit:
        # Re-raise SystemExit to preserve exit code
        raise
    except Exception as e:
        logger.error(f"Unexpected error during processing: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
