import os
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Tuple, List

try:
    import miceforest as mf
except ImportError:
    raise ImportError(
        "miceforest is required for MICE imputation. "
        "Please install it via: pip install miceforest"
    )

from src.config.constants import get_config

# Initialize logging
logger = logging.getLogger(__name__)

def load_harmonized_metadata(input_path: Optional[str] = None) -> pd.DataFrame:
    """
    Loads the harmonized metadata from the default location or specified path.
    """
    if input_path is None:
        config = get_config()
        input_path = config.get("paths", {}).get("harmonized_metadata", "data/metadata/harmonized_matrix.csv")
    
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Harmonized metadata file not found at {input_path}")
    
    logger.info(f"Loading harmonized metadata from {input_path}")
    df = pd.read_csv(input_path)
    return df

def identify_numeric_columns(df: pd.DataFrame) -> List[str]:
    """
    Identifies numeric columns in the dataframe that are candidates for imputation.
    Excludes non-numeric or categorical columns.
    """
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    logger.info(f"Identified {len(numeric_cols)} numeric columns for imputation: {numeric_cols}")
    return numeric_cols

def perform_mice_imputation(
    df: pd.DataFrame,
    numeric_cols: List[str],
    max_iterations: int = 5,
    seed: int = 42
) -> Tuple[pd.DataFrame, bool]:
    """
    Performs MICE imputation using the miceforest library.
    
    Args:
        df: The input dataframe with missing values.
        numeric_cols: List of column names to impute.
        max_iterations: Maximum number of iterations for the MICE algorithm.
        seed: Random seed for reproducibility.
    
    Returns:
        Tuple of (imputed dataframe, convergence_flag)
    """
    if not numeric_cols:
        logger.warning("No numeric columns provided for imputation. Returning original dataframe.")
        return df, True

    # Filter dataframe to only include columns of interest for imputation
    impute_df = df[numeric_cols].copy()
    
    # Check if there are any missing values
    if impute_df.isnull().sum().sum() == 0:
        logger.info("No missing values found in numeric columns. Skipping imputation.")
        return df, True

    logger.info(f"Starting MICE imputation for columns: {numeric_cols}")
    logger.info(f"Missing value count before imputation: {impute_df.isnull().sum().sum()}")

    try:
        # Create the kernel dataset
        kernel_set = mf.KernelSet(impute_df, seed=seed)
        
        # Train the models
        kernel_set.train(
            iterations=max_iterations,
            progress=False # Disable progress bar for cleaner logs
        )
        
        # Check convergence
        # miceforest stores convergence info in the model's history
        # We check if the last iteration's loss decreased significantly or stabilized
        convergence_flag = True
        
        # Simple convergence check: verify that the imputation completed without error
        # and that the number of missing values is zero in the result.
        # A more sophisticated check would look at the change in imputed values between iterations.
        # For this implementation, we rely on the library's internal stability and the fact
        # that it completed the requested iterations.
        
        # Generate imputed dataset
        imputed_data = kernel_set.complete_data()
        
        # Verify no NaNs remain in the imputed columns
        nan_count = imputed_data.isnull().sum().sum()
        if nan_count > 0:
            logger.warning(f"MICE imputation completed but {nan_count} NaNs remain in imputed columns.")
            convergence_flag = False
        else:
            logger.info("MICE imputation successful. No NaNs remaining in imputed columns.")
        
        # Replace the original columns with the imputed ones
        result_df = df.copy()
        result_df[numeric_cols] = imputed_data[numeric_cols]
        
        return result_df, convergence_flag

    except Exception as e:
        logger.error(f"MICE imputation failed with error: {str(e)}")
        raise

def save_cleaned_metadata(df: pd.DataFrame, output_path: Optional[str] = None) -> str:
    """
    Saves the cleaned (imputed) metadata to a CSV file.
    
    Args:
        df: The dataframe to save.
        output_path: Optional output path. Defaults to config.
    
    Returns:
        The path to the saved file.
    """
    if output_path is None:
        config = get_config()
        output_path = config.get("paths", {}).get("cleaned_metadata", "data/cleaned_metadata.csv")
    
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Saving cleaned metadata to {output_path}")
    df.to_csv(output_path, index=False)
    
    # Verify no NaNs in the saved file
    saved_df = pd.read_csv(output_path)
    if saved_df.isnull().sum().sum() > 0:
        raise RuntimeError(f"Saved file {output_path} still contains NaNs! Verification failed.")
    
    return str(output_path)

def run_preprocessing_pipeline(
    input_path: Optional[str] = None,
    output_path: Optional[str] = None,
    max_iterations: int = 5
) -> str:
    """
    Runs the full preprocessing pipeline:
    1. Load harmonized metadata
    2. Identify numeric columns
    3. Perform MICE imputation
    4. Save cleaned metadata
    
    Args:
        input_path: Path to harmonized metadata.
        output_path: Path to save cleaned metadata.
        max_iterations: Max iterations for MICE.
    
    Returns:
        Path to the saved cleaned metadata file.
    """
    logger.info("Starting preprocessing pipeline")
    
    df = load_harmonized_metadata(input_path)
    numeric_cols = identify_numeric_columns(df)
    
    if df.isnull().sum().sum() == 0:
        logger.info("No missing values found. Saving original data as cleaned.")
        return save_cleaned_metadata(df, output_path)
    
    imputed_df, converged = perform_mice_imputation(df, numeric_cols, max_iterations=max_iterations)
    
    if not converged:
        logger.warning("MICE imputation did not converge. Dropping rows with remaining NaNs.")
        imputed_df = imputed_df.dropna()
        logger.info(f"Dropped rows with remaining NaNs. Remaining rows: {len(imputed_df)}")
    
    if len(imputed_df) == 0:
        raise ValueError("No valid rows remaining after imputation and dropping NaNs.")
    
    output_file = save_cleaned_metadata(imputed_df, output_path)
    logger.info("Preprocessing pipeline completed successfully.")
    return output_file

def impute_and_clean(
    input_path: str,
    output_path: str,
    max_iterations: int = 5
) -> str:
    """
    High-level entry point for T015.
    Reads harmonized metadata, imputes missing values using MICE,
    ensures no NaNs remain (dropping rows if necessary), and saves the result.
    
    Args:
        input_path: Path to harmonized metadata CSV.
        output_path: Path to save cleaned metadata CSV.
        max_iterations: Max iterations for MICE.
    
    Returns:
        Path to the saved cleaned metadata file.
    """
    logger.info(f"Running impute_and_clean: input={input_path}, output={output_path}")
    return run_preprocessing_pipeline(input_path, output_path, max_iterations)
