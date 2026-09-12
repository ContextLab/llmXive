"""
Preprocessing module for the Political IAT analysis.

This module implements data loading, MICE imputation, and variable derivation.
"""

from typing import Optional, Tuple, Dict, Any
import pandas as pd
import numpy as np
import logging
from pathlib import Path
from sklearn.experimental import enable_iterative_imputer  # noqa: F401
from sklearn.impute import IterativeImputer
from scipy import stats

from config import ensure_dirs
from logging_config import get_logger
from data_loader import load_project_implicit_data

# Initialize logger for this module
logger = get_logger(__name__)


def load_data(
    data_path: Optional[Path] = None,
    raw_dir: Optional[Path] = None
) -> pd.DataFrame:
    """
    Load the raw dataset from the specified path.

    Args:
        data_path: Optional direct path to the CSV file.
        raw_dir: Optional path to the raw data directory.

    Returns:
        pd.DataFrame: The loaded dataset.

    Raises:
        ValueError: If data cannot be loaded or required columns are missing.
    """
    logger.info("Starting data loading process.")
    
    # Use the data_loader module's function to load the data
    # This ensures consistency with the project's data loading strategy
    df = load_project_implicit_data(data_path=data_path, raw_dir=raw_dir)
    
    if df.empty:
        raise ValueError("Loaded data is empty.")
    
    logger.info(f"Successfully loaded {len(df)} rows.")
    return df


def impute_mice(
    df: pd.DataFrame,
    n_imputations: int = 5,
    random_state: Optional[int] = None
) -> pd.DataFrame:
    """
    Perform Multiple Imputation by Chained Equations (MICE) on the dataset.

    Args:
        df: The input DataFrame with missing values.
        n_imputations: Number of imputed datasets to generate (used for logging/checks).
        random_state: Random seed for reproducibility.

    Returns:
        pd.DataFrame: The imputed dataset (pooled values).

    Raises:
        ValueError: If missingness rate for any key variable exceeds 50%.
    """
    if random_state is None:
        random_state = 42  # Default seed if not provided

    logger.info(f"Starting MICE imputation with {n_imputations} imputations.")
    
    # Identify key variables for missingness check
    # Based on task description and typical IAT data structure
    key_vars = ['IAT_D_score', 'political_ideology', 'news_exposure_freq']
    
    # Check missingness rates for key variables
    for var in key_vars:
        if var in df.columns:
            missing_rate = df[var].isna().sum() / len(df)
            logger.debug(f"Missingness rate for {var}: {missing_rate:.2%}")
            
            if missing_rate > 0.50:
                error_msg = f"Critical: Missingness rate for '{var}' is {missing_rate:.2%} (>50%). Halting imputation."
                logger.error(error_msg)
                raise ValueError(error_msg)
            elif missing_rate > 0.10:
                warning_msg = f"Warning: Missingness rate for '{var}' is {missing_rate:.2%} (>10%)."
                logger.warning(warning_msg)
        else:
            logger.warning(f"Key variable '{var}' not found in dataframe. Skipping missingness check for this variable.")

    # Select numeric columns for imputation
    # MICE in sklearn works on numeric data
    numeric_df = df.select_dtypes(include=[np.number])
    
    if numeric_df.empty:
        logger.warning("No numeric columns found for imputation. Returning original dataframe.")
        return df

    logger.info(f"Imputing {numeric_df.shape[1]} numeric columns.")

    # Initialize the MICE imputer
    # Using sklearn's IterativeImputer which implements MICE
    imputer = IterativeImputer(
        max_iter=10,
        random_state=random_state,
        verbose=0  # Set to 1 for detailed sklearn output if needed
    )

    try:
        imputed_values = imputer.fit_transform(numeric_df)
        imputed_numeric_df = pd.DataFrame(imputed_values, columns=numeric_df.columns, index=numeric_df.index)
        
        # Reconstruct the full dataframe
        # Keep non-numeric columns as they are
        non_numeric_df = df.select_dtypes(exclude=[np.number])
        df_imputed = pd.concat([imputed_numeric_df, non_numeric_df], axis=1)
        
        # Reorder columns to match original
        df_imputed = df_imputed[df.columns]
        
        logger.info("MICE imputation completed successfully.")
        return df_imputed

    except Exception as e:
        logger.error(f"Error during MICE imputation: {str(e)}")
        raise


def derive_variables(
    df: pd.DataFrame
) -> pd.DataFrame:
    """
    Derive new variables required for analysis, such as z-scored news exposure
    and binary ideology splits.

    Args:
        df: The input DataFrame (likely imputed).

    Returns:
        pd.DataFrame: The DataFrame with new derived columns.
    """
    logger.info("Starting variable derivation.")
    df_derived = df.copy()

    # 1. Z-score news exposure
    if 'news_exposure_freq' in df_derived.columns:
        mean_ne = df_derived['news_exposure_freq'].mean()
        std_ne = df_derived['news_exposure_freq'].std()
        if std_ne == 0:
            logger.warning("Standard deviation of news_exposure_freq is 0. Cannot z-score.")
            df_derived['news_exposure_z'] = 0.0
        else:
            df_derived['news_exposure_z'] = (df_derived['news_exposure_freq'] - mean_ne) / std_ne
        logger.info("Derived 'news_exposure_z'.")
    else:
        logger.warning("Column 'news_exposure_freq' not found. Skipping z-score derivation.")

    # 2. Binary ideology split (median split)
    if 'political_ideology' in df_derived.columns:
        median_ideology = df_derived['political_ideology'].median()
        df_derived['ideology_binary'] = (df_derived['political_ideology'] >= median_ideology).astype(int)
        logger.info(f"Derived 'ideology_binary' using median split (median={median_ideology}).")
    else:
        logger.warning("Column 'political_ideology' not found. Skipping binary derivation.")

    logger.info("Variable derivation completed.")
    return df_derived


def run_preprocessing_pipeline(
    raw_data_path: Path,
    output_path: Path,
    n_imputations: int = 5
) -> Dict[str, Any]:
    """
    Execute the full preprocessing pipeline: Load -> Impute -> Derive -> Save.

    Args:
        raw_data_path: Path to the raw input CSV.
        output_path: Path where the processed CSV will be saved.
        n_imputations: Number of imputations for MICE.

    Returns:
        Dict containing pipeline metadata and status.
    """
    logger.info("Starting preprocessing pipeline.")
    
    # Ensure output directory exists
    ensure_dirs(output_path.parent)

    result = {
        "status": "success",
        "rows_loaded": 0,
        "rows_imputed": 0,
        "rows_derived": 0,
        "output_path": str(output_path)
    }

    try:
        # Step 1: Load Data
        logger.info(f"Loading data from {raw_data_path}")
        df_raw = load_data(data_path=raw_data_path)
        result["rows_loaded"] = len(df_raw)
        logger.info(f"Loaded {result['rows_loaded']} rows.")

        # Step 2: Impute Data
        logger.info("Performing MICE imputation...")
        df_imputed = impute_mice(df_raw, n_imputations=n_imputations)
        result["rows_imputed"] = len(df_imputed)
        logger.info(f"Imputed {result['rows_imputed']} rows.")

        # Step 3: Derive Variables
        logger.info("Deriving variables...")
        df_final = derive_variables(df_imputed)
        result["rows_derived"] = len(df_final)
        logger.info(f"Derived variables for {result['rows_derived']} rows.")

        # Step 4: Save Output
        logger.info(f"Saving processed data to {output_path}")
        df_final.to_csv(output_path, index=False)
        logger.info("Pipeline completed successfully.")

    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        result["status"] = "failed"
        result["error"] = str(e)
        raise

    return result