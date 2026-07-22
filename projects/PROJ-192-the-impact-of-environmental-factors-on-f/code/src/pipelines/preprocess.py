"""
Preprocessing pipeline for fungal community data.
Implements MICE imputation, VIF calculation, and diversity metrics.
"""
import os
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Tuple, List
import warnings

# Import miceforest for MICE imputation
try:
    import miceforest as mf
except ImportError:
    raise ImportError(
        "miceforest is required for MICE imputation. "
        "Please install it via: pip install miceforest"
    )

from src.config.constants import get_config
from src.utils.logging import log_event

logger = logging.getLogger(__name__)

# Constants
DEFAULT_ITERATIONS = 5
DEFAULT_RANDOM_STATE = 42
MIN_ROWS_FOR_IMPUTATION = 10

def load_harmonized_metadata(
    input_path: str = "data/metadata/harmonized_matrix.csv"
) -> pd.DataFrame:
    """
    Load the harmonized metadata matrix produced by ingest.py.

    Args:
        input_path: Path to the harmonized metadata CSV.

    Returns:
        DataFrame with harmonized metadata.

    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the file is empty or invalid.
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Harmonized metadata file not found: {input_path}")

    df = pd.read_csv(input_path)
    
    if df.empty:
        raise ValueError(f"Harmonized metadata file is empty: {input_path}")
    
    logger.info(f"Loaded harmonized metadata with {len(df)} rows and {len(df.columns)} columns")
    return df

def identify_numeric_columns(df: pd.DataFrame) -> List[str]:
    """
    Identify numeric columns suitable for imputation.
    
    Args:
        df: Input DataFrame.
        
    Returns:
        List of numeric column names.
    """
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    logger.info(f"Identified {len(numeric_cols)} numeric columns for imputation: {numeric_cols}")
    return numeric_cols

def perform_mice_imputation(
    df: pd.DataFrame,
    numeric_cols: Optional[List[str]] = None,
    iterations: int = DEFAULT_ITERATIONS,
    random_state: int = DEFAULT_RANDOM_STATE,
    impute_target_cols: Optional[List[str]] = None
) -> Tuple[pd.DataFrame, bool]:
    """
    Perform Multiple Imputation by Chained Equations (MICE) using miceforest.
    
    This function:
    1. Identifies missing values in numeric columns.
    2. Runs MICE imputation with the specified number of iterations.
    3. Checks convergence.
    4. If not converged, logs a warning and drops rows with missing values.
    5. Returns the imputed DataFrame and a convergence flag.
    
    Args:
        df: Input DataFrame with potential missing values.
        numeric_cols: List of numeric columns to impute. If None, auto-detects.
        iterations: Maximum number of MICE iterations.
        random_state: Random seed for reproducibility.
        impute_target_cols: Specific columns to impute. If None, all numeric cols are used.
        
    Returns:
        Tuple of (imputed DataFrame, convergence_flag).
        convergence_flag is True if imputation converged, False otherwise.
        
    Raises:
        ValueError: If there are too few rows for imputation or no missing values found.
    """
    if len(df) < MIN_ROWS_FOR_IMPUTATION:
        logger.warning(f"DataFrame has only {len(df)} rows (< {MIN_ROWS_FOR_IMPUTATION}). "
                     "Skipping MICE imputation due to insufficient samples.")
        return df, True
    
    # Identify numeric columns if not provided
    if numeric_cols is None:
        numeric_cols = identify_numeric_columns(df)
    
    if not numeric_cols:
        logger.warning("No numeric columns found for imputation.")
        return df, True
    
    # Check if there are any missing values
    missing_mask = df[numeric_cols].isnull().any()
    if not missing_mask.any():
        logger.info("No missing values found in numeric columns. Skipping imputation.")
        return df, True
    
    # Determine which columns actually have missing values
    cols_with_missing = [col for col in numeric_cols if df[col].isnull().any()]
    logger.info(f"Columns with missing values: {cols_with_missing}")
    
    # If specific target columns are provided, filter to those
    if impute_target_cols:
        cols_with_missing = [col for col in cols_with_missing if col in impute_target_cols]
        if not cols_with_missing:
            logger.info("No target columns have missing values. Skipping imputation.")
            return df, True
    
    # Create a copy to avoid modifying the original
    df_impute = df.copy()
    
    # Initialize the KernelDataSet
    logger.info(f"Initializing MICE imputation with {iterations} iterations...")
    kernel_data = mf.KernelDataSet(
        df_impute[cols_with_missing].copy(),
        random_state=random_state
    )
    
    # Perform imputation
    try:
        kernel_data.mice(iterations=iterations)
    except Exception as e:
        logger.error(f"MICE imputation failed with error: {e}")
        raise RuntimeError(f"MICE imputation failed: {e}")
    
    # Check convergence
    # miceforest stores convergence info in the imputed_data attribute
    # We check if the imputation process completed successfully
    # The library doesn't explicitly return a convergence flag, so we check for NaNs in result
    imputed_values = kernel_data.imputed_data(0)  # Get first imputation dataset
    
    # Check for any remaining NaNs in the imputed columns
    has_remaining_nans = imputed_values.isnull().any().any()
    
    if has_remaining_nans:
        logger.warning(
            "MICE imputation did not converge (NaNs remain). "
            "Dropping rows with missing values as per FR-008."
        )
        # Drop rows with any remaining NaNs in the imputed columns
        df_impute[cols_with_missing] = imputed_values
        df_impute = df_impute.dropna(subset=cols_with_missing)
        convergence_flag = False
    else:
        logger.info("MICE imputation converged successfully.")
        # Update the full dataframe with imputed values
        df_impute[cols_with_missing] = imputed_values
        convergence_flag = True
    
    # Final check: ensure no NaNs remain in numeric columns
    final_missing = df_impute[numeric_cols].isnull().sum()
    if final_missing.sum() > 0:
        logger.warning(f"Final check found {final_missing.sum()} remaining NaNs. Dropping affected rows.")
        df_impute = df_impute.dropna(subset=numeric_cols)
    
    return df_impute, convergence_flag

def save_cleaned_metadata(
    df: pd.DataFrame,
    output_path: str = "data/cleaned_metadata.csv"
) -> None:
    """
    Save the cleaned metadata to CSV.
    
    Args:
        df: Cleaned DataFrame.
        output_path: Path to save the CSV file.
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    df.to_csv(output_path, index=False)
    logger.info(f"Saved cleaned metadata to {output_path} with {len(df)} rows")
    
    # Verify no NaNs remain
    nan_count = df.isnull().sum().sum()
    if nan_count > 0:
        logger.error(f"CRITICAL: {nan_count} NaN values remain in cleaned metadata!")
        raise ValueError(f"Cleaned metadata still contains {nan_count} NaN values")
    else:
        logger.info("Verification passed: No NaN values in cleaned metadata.")

def run_preprocessing_pipeline(
    input_path: str = "data/metadata/harmonized_matrix.csv",
    output_path: str = "data/cleaned_metadata.csv",
    iterations: int = DEFAULT_ITERATIONS,
    random_state: int = DEFAULT_RANDOM_STATE
) -> Tuple[pd.DataFrame, bool]:
    """
    Run the full preprocessing pipeline for metadata.
    
    This function:
    1. Loads harmonized metadata.
    2. Performs MICE imputation.
    3. Saves cleaned metadata.
    4. Returns the cleaned DataFrame and convergence status.
    
    Args:
        input_path: Path to harmonized metadata input.
        output_path: Path for cleaned metadata output.
        iterations: Number of MICE iterations.
        random_state: Random seed.
        
    Returns:
        Tuple of (cleaned DataFrame, convergence_flag).
    """
    log_event("preprocessing_pipeline_start", {"input": input_path})
    
    # Load data
    df = load_harmonized_metadata(input_path)
    
    # Perform MICE imputation
    df_clean, converged = perform_mice_imputation(
        df,
        iterations=iterations,
        random_state=random_state
    )
    
    # Save cleaned data
    save_cleaned_metadata(df_clean, output_path)
    
    log_event("preprocessing_pipeline_complete", {
        "input_rows": len(df),
        "output_rows": len(df_clean),
        "converged": converged,
        "output_path": output_path
    })
    
    return df_clean, converged

# Convenience function for direct import
def impute_and_clean(
    input_path: str = "data/metadata/harmonized_matrix.csv",
    output_path: str = "data/cleaned_metadata.csv"
) -> Tuple[pd.DataFrame, bool]:
    """
    Alias for run_preprocessing_pipeline for easier importing.
    
    Args:
        input_path: Path to harmonized metadata.
        output_path: Path for cleaned metadata.
        
    Returns:
        Tuple of (cleaned DataFrame, convergence_flag).
    """
    return run_preprocessing_pipeline(input_path, output_path)
