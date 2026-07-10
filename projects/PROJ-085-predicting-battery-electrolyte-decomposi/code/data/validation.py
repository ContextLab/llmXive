import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logging_config import get_logger

logger = get_logger(__name__)

def validate_feature_matrix(df: pd.DataFrame, required_columns: Optional[List[str]] = None) -> Tuple[bool, List[str]]:
    """
    Validate the feature matrix for missing values and required columns.
    
    Args:
        df: The feature DataFrame to validate
        required_columns: Optional list of columns that must be present
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    if df is None or df.empty:
        return False, ["DataFrame is empty or None"]
    
    # Check for missing values
    missing_counts = df.isnull().sum()
    if missing_counts.any():
        cols_with_missing = missing_counts[missing_counts > 0].index.tolist()
        errors.append(f"Missing values found in columns: {cols_with_missing}")
    
    # Check required columns if specified
    if required_columns:
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            errors.append(f"Missing required columns: {missing_cols}")
    
    return len(errors) == 0, errors

def clean_or_drop_missing(df: pd.DataFrame, strategy: str = "drop") -> pd.DataFrame:
    """
    Handle missing values in the feature matrix.
    
    Args:
        df: Input DataFrame
        strategy: 'drop' to remove rows with missing values, 'fill' to fill with 0
        
    Returns:
        Cleaned DataFrame
    """
    if strategy == "drop":
        initial_count = len(df)
        df_clean = df.dropna()
        dropped_count = initial_count - len(df_clean)
        if dropped_count > 0:
            logger.warning(f"Dropped {dropped_count} rows due to missing values")
        return df_clean
    elif strategy == "fill":
        return df.fillna(0)
    else:
        raise ValueError(f"Unknown strategy: {strategy}")

def run_validation_pipeline(
    input_path: str,
    output_path: str,
    required_columns: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Run the full validation pipeline: load, validate, clean, and save.
    
    Args:
        input_path: Path to the input CSV
        output_path: Path to save the cleaned CSV
        required_columns: Optional list of columns that must be present
        
    Returns:
        The validated and cleaned DataFrame
    """
    logger.info(f"Starting validation pipeline for {input_path}")
    
    # Load data
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} rows from {input_path}")
    
    # Validate
    is_valid, errors = validate_feature_matrix(df, required_columns)
    if not is_valid:
        logger.warning(f"Validation errors: {errors}")
        # Continue anyway but log warning, or raise if strict
        # For now, we proceed to cleaning
    
    # Clean
    df_clean = clean_or_drop_missing(df, strategy="drop")
    
    # Save
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    df_clean.to_csv(output_path, index=False)
    logger.info(f"Saved {len(df_clean)} rows to {output_path}")
    
    return df_clean

if __name__ == "__main__":
    # Example usage
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, required=True)
    parser.add_argument("--output", type=str, required=True)
    args = parser.parse_args()
    
    run_validation_pipeline(args.input, args.output)
