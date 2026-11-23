"""
Preprocessing pipeline for the political news exposure study.

This module handles data loading, MICE imputation, and variable derivation.
"""

from typing import Optional, Tuple, Dict, Any
import pandas as pd
import numpy as np
import logging
from pathlib import Path
from sklearn.experimental import enable_iterative_imputer  # noqa: F401
from sklearn.impute import IterativeImputer

from config_manager import get_data_processed_path, get_config
from logging_config import get_logger

logger = get_logger(__name__)

class DataIntegrityError(ValueError):
    """Custom exception for data integrity issues."""
    pass

def load_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Perform initial data cleaning and type conversion.
    
    Args:
        df: Raw DataFrame.
    
    Returns:
        Cleaned DataFrame.
    """
    logger.info("Performing initial data cleaning...")
    
    # Ensure numeric columns are numeric
    numeric_cols = ['IAT_D_score', 'political_ideology', 'news_exposure_freq']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    return df

def impute_mice(df: pd.DataFrame, max_iter: int = 10, n_imputations: int = 5) -> pd.DataFrame:
    """
    Perform MICE (Multiple Imputation by Chained Equations) imputation.
    
    Args:
        df: DataFrame with missing values.
        max_iter: Maximum number of iterations for MICE.
        n_imputations: Number of imputations (currently using single imputation for simplicity).
    
    Returns:
        DataFrame with imputed values.
    
    Raises:
        DataIntegrityError: If missingness exceeds 50% for any key variable.
    """
    logger.info("Starting MICE imputation...")
    
    key_vars = ['IAT_D_score', 'political_ideology', 'news_exposure_freq']
    available_vars = [v for v in key_vars if v in df.columns]
    
    if not available_vars:
        logger.error("No key variables found for imputation.")
        return df
    
    # Check missingness rates
    for var in available_vars:
        missing_pct = df[var].isna().sum() / len(df) * 100
        logger.info(f"Missingness for {var}: {missing_pct:.2f}%")
        if missing_pct > 50:
            logger.warning(f"WARNING: Missingness exceeds 50% for variable {var} ({missing_pct:.2f}%). Halting per FR-008.")
            # Flush log
            for handler in logger.handlers:
                handler.flush()
            raise DataIntegrityError(f"Missingness exceeds 50% for variable {var}. Halting execution.")
    
    # Select columns for imputation
    cols_to_impute = [c for c in df.columns if df[c].isna().any() and df[c].dtype in ['float64', 'int64', 'object']]
    
    if not cols_to_impute:
        logger.info("No columns with missing values found.")
        return df
    
    # Prepare data for imputer
    impute_df = df[cols_to_impute].copy()
    
    # Use IterativeImputer (MICE)
    imputer = IterativeImputer(max_iter=max_iter, random_state=42)
    
    try:
        imputed_values = imputer.fit_transform(impute_df)
        imputed_df = pd.DataFrame(imputed_values, columns=cols_to_impute, index=df.index)
        
        # Replace missing values in original dataframe
        result_df = df.copy()
        result_df[cols_to_impute] = imputed_df
        
        logger.info(f"MICE imputation complete. Filled {impute_df.isna().sum().sum()} missing values.")
        return result_df
        
    except Exception as e:
        logger.error(f"MICE imputation failed: {e}")
        # Fallback to mean imputation if MICE fails (with warning)
        logger.warning("Falling back to mean imputation.")
        result_df = df.copy()
        for col in cols_to_impute:
            if result_df[col].dtype in ['float64', 'int64']:
                result_df[col] = result_df[col].fillna(result_df[col].mean())
            else:
                result_df[col] = result_df[col].fillna(result_df[col].mode()[0] if len(result_df[col].mode()) > 0 else 'Unknown')
        return result_df

def derive_variables(df: pd.DataFrame) -> pd.DataFrame:
    """
    Derive new variables needed for analysis.
    
    Args:
        df: Imputed DataFrame.
    
    Returns:
        DataFrame with derived variables.
    """
    logger.info("Deriving variables...")
    
    result_df = df.copy()
    
    # Z-score news exposure
    if 'news_exposure_freq' in result_df.columns:
        mean_exp = result_df['news_exposure_freq'].mean()
        std_exp = result_df['news_exposure_freq'].std()
        if std_exp > 0:
            result_df['news_exposure_z'] = (result_df['news_exposure_freq'] - mean_exp) / std_exp
        else:
            result_df['news_exposure_z'] = 0.0
        logger.info("Derived news_exposure_z (z-scored).")
    else:
        logger.warning("news_exposure_freq not found, skipping news_exposure_z derivation.")
    
    # Binary ideology (median split)
    if 'political_ideology' in result_df.columns:
        median_ideology = result_df['political_ideology'].median()
        result_df['ideology_binary'] = (result_df['political_ideology'] >= median_ideology).astype(int)
        logger.info(f"Derived ideology_binary (median split at {median_ideology:.2f}).")
    else:
        logger.warning("political_ideology not found, skipping ideology_binary derivation.")
    
    return result_df

def run_preprocessing_pipeline(raw_df: pd.DataFrame) -> Optional[pd.DataFrame]:
    """
    Run the full preprocessing pipeline: load -> impute -> derive.
    
    Args:
        raw_df: Raw DataFrame from data loader.
    
    Returns:
        Processed DataFrame or None if pipeline fails.
    """
    try:
        # Step 1: Load/Clean
        cleaned_df = load_data(raw_df)
        
        # Step 2: Impute
        imputed_df = impute_mice(cleaned_df)
        
        # Step 3: Derive
        processed_df = derive_variables(imputed_df)
        
        logger.info("Preprocessing pipeline completed successfully.")
        return processed_df
        
    except DataIntegrityError as e:
        logger.critical(f"Data integrity error during preprocessing: {e}")
        raise
    except Exception as e:
        logger.exception(f"Preprocessing pipeline failed: {e}")
        return None
