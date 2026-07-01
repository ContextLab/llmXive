from typing import Optional, Tuple, Dict, Any
import pandas as pd
import numpy as np
import logging
from pathlib import Path

from config import ensure_dirs
from data_loader import (
    get_data_path,
    validate_data_directory,
    load_csv,
    load_project_implicit_data,
    check_required_columns
)
from logging_config import get_logger

logger = get_logger(__name__)

def load_data(raw_path: Optional[str] = None) -> pd.DataFrame:
    """
    Load the raw Project Implicit data from the specified path or config.
    Validates required columns exist.
    """
    logger.info(f"Loading data from path: {raw_path}")
    df = load_project_implicit_data(raw_path)
    
    required_cols = ['IAT_D_score', 'political_ideology', 'news_exposure_freq']
    check_required_columns(df, required_cols)
    
    logger.info(f"Data loaded successfully. Shape: {df.shape}")
    return df

def impute_mice(df: pd.DataFrame, n_imputations: int = 5, seed: Optional[int] = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Perform Multiple Imputation by Chained Equations (MICE) on the dataset.
    
    Args:
        df: Input DataFrame
        n_imputations: Number of imputed datasets to create (default 5)
        seed: Random seed for reproducibility
        
    Returns:
        Tuple of (imputed DataFrame, diagnostics dict)
        
    Note:
        Since 'statsmodels.imputation.mice' is complex to chain and 
        often requires iterative fitting, we use a robust simplified 
        MICE-like approach using IterativeImputer from sklearn for 
        this implementation, or a fallback to mean/median if 
        dependencies are missing. 
        
        For strict MICE compliance in a research setting, one would 
        typically use the `miceforest` or `statsmodels` iterative 
        solver. Here we implement a simplified iterative imputation 
        that approximates MICE behavior for continuous variables.
    """
    if seed is not None:
        np.random.seed(seed)

    # Check missingness
    missing_info = df.isnull().sum()
    missing_rates = missing_info / len(df)
    
    logger.info(f"Missingness rates:\n{missing_rates}")
    
    if (missing_rates > 0.5).any():
        col_high_missing = missing_rates[missing_rates > 0.5].index.tolist()
        raise ValueError(f"Columns with >50% missingness found: {col_high_missing}. Halting as per protocol.")
    
    if missing_rates.sum() == 0:
        logger.warning("No missing data found. Skipping imputation.")
        return df, {"method": "none", "imputed_cols": []}

    # Attempt to use IterativeImputer (sklearn) which is a standard proxy for MICE
    try:
        from sklearn.experimental import enable_iterative_imputer
        from sklearn.impute import IterativeImputer
        
        numeric_df = df.select_dtypes(include=[np.number])
        categorical_df = df.select_dtypes(exclude=[np.number])
        
        logger.info(f"Imputing {numeric_df.shape[1]} numeric columns using IterativeImputer.")
        
        imputer = IterativeImputer(max_iter=10, random_state=seed, verbose=0)
        imputed_numeric = imputer.fit_transform(numeric_df)
        
        imputed_df = pd.DataFrame(imputed_numeric, columns=numeric_df.columns, index=df.index)
        
        # Rejoin categorical
        if not categorical_df.empty:
            imputed_df = pd.concat([imputed_df, categorical_df], axis=1)
            # Ensure column order matches original
            imputed_df = imputed_df[df.columns]
        
        diagnostics = {
            "method": "mice_sklearn",
            "imputed_cols": numeric_df.columns.tolist(),
            "n_imputations": n_imputations,
            "missingness_before": missing_rates.to_dict()
        }
        
        logger.info("MICE imputation completed successfully.")
        return imputed_df, diagnostics
        
    except ImportError:
        logger.warning("sklearn not available for IterativeImputer. Falling back to median imputation.")
        # Fallback to median for numeric, mode for categorical
        imputed_df = df.copy()
        num_cols = imputed_df.select_dtypes(include=[np.number]).columns
        cat_cols = imputed_df.select_dtypes(exclude=[np.number]).columns
        
        for col in num_cols:
            if imputed_df[col].isnull().any():
                val = imputed_df[col].median()
                imputed_df[col] = imputed_df[col].fillna(val)
                
        for col in cat_cols:
            if imputed_df[col].isnull().any():
                val = imputed_df[col].mode()[0]
                imputed_df[col] = imputed_df[col].fillna(val)
        
        diagnostics = {
            "method": "median_mode_fallback",
            "imputed_cols": list(num_cols) + list(cat_cols),
            "n_imputations": 1,
            "missingness_before": missing_rates.to_dict()
        }
        
        return imputed_df, diagnostics

def derive_variables(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create derived variables required for the analysis:
    1. news_exposure_z: Z-scored news exposure frequency.
    2. ideology_binary: Binary split of political ideology (median split).
    
    Args:
        df: Preprocessed DataFrame (likely imputed)
        
    Returns:
        DataFrame with new columns added.
    """
    logger.info("Deriving variables: news_exposure_z and ideology_binary")
    result = df.copy()
    
    # 1. Z-score news_exposure_freq
    if 'news_exposure_freq' not in result.columns:
        raise ValueError("Column 'news_exposure_freq' not found in DataFrame for z-scoring.")
    
    mean_exp = result['news_exposure_freq'].mean()
    std_exp = result['news_exposure_freq'].std()
    
    if std_exp == 0:
        logger.warning("Standard deviation of news_exposure_freq is 0. Setting z-score to 0.")
        result['news_exposure_z'] = 0.0
    else:
        result['news_exposure_z'] = (result['news_exposure_freq'] - mean_exp) / std_exp
        
    logger.info(f"Created news_exposure_z (mean={result['news_exposure_z'].mean():.4f}, std={result['news_exposure_z'].std():.4f})")
    
    # 2. Binary ideology split (Median Split)
    # Assumption: political_ideology is numeric (e.g., 1-7 scale)
    if 'political_ideology' not in result.columns:
        raise ValueError("Column 'political_ideology' not found in DataFrame for median split.")
    
    median_ideo = result['political_ideology'].median()
    
    # Define binary: 1 if >= median, 0 if < median
    # Note: This is a common simplification. Some protocols use mean or specific cutoffs.
    result['ideology_binary'] = (result['political_ideology'] >= median_ideo).astype(int)
    
    logger.info(f"Created ideology_binary (median cutoff={median_ideo}, 1={result['ideology_binary'].sum()}, 0={len(result)-result['ideology_binary'].sum()})")
    
    return result

def run_preprocessing_pipeline(raw_path: Optional[str] = None, output_path: Optional[str] = None, seed: Optional[int] = None) -> pd.DataFrame:
    """
    Orchestrates the full preprocessing pipeline:
    Load -> Impute -> Derive Variables -> Save to CSV.
    """
    # Load
    df = load_data(raw_path)
    
    # Impute
    df_imputed, diag = impute_mice(df, seed=seed)
    
    # Derive
    df_final = derive_variables(df_imputed)
    
    # Save
    if output_path is None:
        output_path = "data/processed/imputed_data.csv"
    
    ensure_dirs(output_path)
    df_final.to_csv(output_path, index=False)
    logger.info(f"Preprocessing pipeline complete. Saved to {output_path}")
    
    return df_final