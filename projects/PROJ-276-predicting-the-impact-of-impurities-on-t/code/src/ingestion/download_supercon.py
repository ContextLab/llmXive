import sys
import os
import pandas as pd
from pathlib import Path
from src.utils.logging import get_ingestion_logger

# Verify the dataset exists and is accessible
try:
    from datasets import load_dataset
except ImportError:
    print("ERROR: 'datasets' package not installed. Please run: pip install datasets")
    sys.exit(1)

logger = get_ingestion_logger()

def has_impurity_columns(df: pd.DataFrame) -> bool:
    """
    Check if the DataFrame has columns that likely represent impurity data.
    
    Args:
        df: Input DataFrame
        
    Returns:
        True if impurity columns are detected, False otherwise.
    """
    if df.empty:
        return False
    
    # Common column names for impurities in SuperCon dataset
    potential_impurity_cols = [
        'impurity', 'impurities', 'impurity_element', 'impurity_elements',
        'doping', 'dopant', 'substitution'
    ]
    
    for col in df.columns:
        col_lower = col.lower()
        for keyword in potential_impurity_cols:
            if keyword in col_lower:
                return True
    
    return False

def validate_impurity_coverage(df: pd.DataFrame, threshold: float = 0.5) -> bool:
    """
    Validate that at least (1 - threshold) of the entries have impurity data.
    
    Args:
        df: Input DataFrame
        threshold: Maximum allowed fraction of rows lacking impurity data (default 0.5)
        
    Returns:
        True if coverage is sufficient, False otherwise.
        
    Raises:
        SystemExit: If impurity coverage is below the threshold.
    """
    if df.empty:
        logger.error("DataFrame is empty. Cannot validate impurity coverage.")
        return False
    
    impurity_cols = [col for col in df.columns if 'impurity' in col.lower() or 'doping' in col.lower() or 'dopant' in col.lower()]
    
    if not impurity_cols:
        logger.error("No impurity-related columns found in dataset.")
        return False
    
    # Check for non-null values in any impurity column
    # We consider a row valid if it has at least one non-null impurity value
    valid_rows = df[impurity_cols].notna().any(axis=1)
    coverage = valid_rows.sum() / len(df)
    
    logger.info(f"Impurity coverage: {coverage:.2%} ({valid_rows.sum()}/{len(df)} rows)")
    
    if coverage < (1 - threshold):
        logger.error(f"Impurity coverage ({coverage:.2%}) is below the required threshold ({(1-threshold):.2%}).")
        logger.error(f"Aborting to prevent ingestion of low-quality data.")
        return False
    
    return True

def load_supercon_dataset() -> pd.DataFrame:
    """
    Load the MgB2 specific SuperCon dataset from HuggingFace.
    
    Returns:
        DataFrame containing the SuperCon dataset.
        
    Raises:
        SystemExit: If the dataset cannot be loaded or fails validation.
    """
    dataset_name = "taqwa92/cm.mgb2"
    logger.info(f"Loading SuperCon dataset: {dataset_name}")
    
    try:
        # Load the dataset
        dataset = load_dataset(dataset_name, split="train")
        df = dataset.to_pandas()
        
        logger.info(f"Successfully loaded {len(df)} rows from {dataset_name}")
        
        # Validate impurity coverage
        if not validate_impurity_coverage(df):
            logger.critical("Dataset failed impurity coverage validation.")
            sys.exit(1)
        
        return df
        
    except Exception as e:
        logger.error(f"Failed to load SuperCon dataset: {e}")
        sys.exit(1)

def main():
    """Main entry point for the SuperCon download script."""
    logger.info("Starting SuperCon dataset download and validation.")
    
    df = load_supercon_dataset()
    
    # Save to a temporary location or return for further processing
    # For this task, we just ensure the script runs and validates
    logger.info("SuperCon dataset validation complete.")
    
    # If we reach here, the dataset passed validation
    return df

if __name__ == "__main__":
    main()
