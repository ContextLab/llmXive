"""
Regression Module for Power Gap Analysis (User Story 3).

This module handles the preprocessing of data for regression analysis,
specifically encoding categorical variables and enforcing the constraint
to exclude `sample_size_category` to avoid mathematical coupling.

It also includes the guardrail to halt execution if the dataset size
is below the minimum threshold (30 studies) defined in T026a.
"""

import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
import numpy as np

# Import constants from the project's global configuration
# Assuming T005 populated code/__init__.py with MIN_SAMPLE_SIZE
# We import it directly if available, otherwise define a fallback constant.
try:
    from code import MIN_SAMPLE_SIZE
except ImportError:
    # Fallback if __init__.py is not fully loaded in this context
    MIN_SAMPLE_SIZE = 30

from code.power_analysis_guardrail import load_power_analysis, filter_valid_records, write_error_artifact

logger = logging.getLogger(__name__)

class RegressionPreprocessingError(Exception):
    """Raised when preprocessing steps fail."""
    pass

def load_power_gap_data(input_path: Path) -> pd.DataFrame:
    """
    Loads the power analysis CSV produced by T026.

    Args:
        input_path: Path to `data/derived/power_analysis.csv`.

    Returns:
        A pandas DataFrame containing the study records.
    """
    logger.info(f"Loading power analysis data from {input_path}")
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} records. Columns: {list(df.columns)}")
    return df

def enforce_minimum_sample_size(df: pd.DataFrame, threshold: int = MIN_SAMPLE_SIZE) -> pd.DataFrame:
    """
    Enforces the minimum sample size constraint (SC-004).
    
    If the number of valid records is less than the threshold,
    this function halts execution by raising a RuntimeError.
    
    Args:
        df: The DataFrame to check.
        threshold: The minimum number of records required (default 30).
    
    Raises:
        RuntimeError: If the dataset size is below the threshold.
    
    Returns:
        The DataFrame if the check passes.
    """
    count = len(df)
    logger.info(f"Checking sample size constraint: {count} records >= {threshold} required?")
    
    if count < threshold:
        error_msg = f"Dataset size ({count}) is below the minimum threshold ({threshold}). " \
                    f"Halting execution to prevent invalid statistical inference (SC-004)."
        logger.error(error_msg)
        
        # Write the error artifact as required by T026a
        error_path = Path("results/error/sample_size_insufficient.json")
        error_path.parent.mkdir(parents=True, exist_ok=True)
        write_error_artifact(error_path, error_msg, {"records_found": count, "threshold": threshold})
        
        raise RuntimeError(error_msg)
    
    logger.info(f"Sample size constraint satisfied ({count} >= {threshold}).")
    return df

def preprocess_for_regression(df: pd.DataFrame, exclude_categories: List[str] = None) -> pd.DataFrame:
    """
    Preprocesses the data for regression modeling.
    
    - Encodes categorical variables (`field`, `effect_size_domain`) as dummy/one-hot variables.
    - Explicitly EXCLUDES `sample_size_category` from the feature set to avoid mathematical coupling.
    
    Args:
        df: The raw DataFrame from load_power_gap_data.
        exclude_categories: List of column names to exclude from the model (default: ['sample_size_category']).
    
    Returns:
        A DataFrame ready for regression (with dummy variables encoded).
    """
    if exclude_categories is None:
        exclude_categories = ['sample_size_category']
    
    logger.info(f"Preprocessing data. Excluding columns: {exclude_categories}")
    
    # Validate that the target variable exists
    if 'power_gap' not in df.columns:
        raise RegressionPreprocessingError("Target variable 'power_gap' not found in dataset.")
    
    # Identify categorical columns to encode
    # We look for columns that are likely categorical based on typical schema
    # and exclude the target and numeric IDs.
    categorical_cols = []
    for col in df.columns:
        if col in exclude_categories:
            continue
        if col in ['study_id', 'osf_id', 'planned_power', 'sensitivity_power', 'power_gap']:
            continue
        if df[col].dtype == 'object' or (df[col].dtype.name.startswith('category')):
            categorical_cols.append(col)
    
    logger.info(f"Identified categorical columns for encoding: {categorical_cols}")
    
    # Create dummy variables for categorical columns
    # drop_first=True to avoid the dummy variable trap (perfect multicollinearity)
    df_processed = pd.get_dummies(df, columns=categorical_cols, drop_first=True, dtype=float)
    
    # Explicitly verify that sample_size_category is NOT in the columns
    if 'sample_size_category' in df_processed.columns:
        raise RegressionPreprocessingError(
            "CRITICAL ERROR: 'sample_size_category' was found in the processed features. "
            "This violates the Plan Constraint to avoid mathematical coupling."
        )
    
    logger.info(f"Preprocessing complete. Final columns: {list(df_processed.columns)}")
    return df_processed

def main():
    """
    Main entry point for the regression preprocessing step.
    
    This function:
    1. Loads the power analysis data.
    2. Enforces the minimum sample size guardrail (T026a).
    3. Preprocesses the data (encoding, exclusion of coupling variables).
    4. Saves the preprocessed dataset to `data/derived/power_analysis_preprocessed.csv`.
    """
    logger.info("Starting regression preprocessing (T031)...")
    
    input_path = Path("data/derived/power_analysis.csv")
    output_path = Path("data/derived/power_analysis_preprocessed.csv")
    
    try:
        # 1. Load Data
        df = load_power_gap_data(input_path)
        
        # 2. Enforce Sample Size Guardrail
        df = enforce_minimum_sample_size(df, threshold=MIN_SAMPLE_SIZE)
        
        # 3. Preprocess
        df_final = preprocess_for_regression(df)
        
        # 4. Save Output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df_final.to_csv(output_path, index=False)
        logger.info(f"Successfully wrote preprocessed data to {output_path}")
        
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        sys.exit(1)
    except RuntimeError as e:
        # This is the expected failure mode for insufficient data
        logger.error(f"Execution halted: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during preprocessing: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    main()
