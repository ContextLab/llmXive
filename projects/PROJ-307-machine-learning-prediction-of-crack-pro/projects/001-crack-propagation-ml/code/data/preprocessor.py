"""
Data preprocessing for the crack propagation prediction pipeline.
"""
import pandas as pd
import logging
from code.logging_config import get_logger

logger = get_logger(__name__)

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean the crack propagation dataset.
    
    Args:
        df: Raw DataFrame
        
    Returns:
        Cleaned DataFrame
    """
    logger.info(f"Cleaning data: {df.shape}")
    
    # Remove rows with missing critical values
    critical_cols = ['da_dN', 'delta_K']
    df_clean = df.dropna(subset=critical_cols)
    
    # Filter valid ranges
    df_clean = df_clean[df_clean['da_dN'] > 0]
    df_clean = df_clean[df_clean['delta_K'] > 0]
    
    logger.info(f"Data after cleaning: {df_clean.shape}")
    return df_clean

def impute_missing(df: pd.DataFrame) -> pd.DataFrame:
    """
    Impute missing values in the dataset.
    
    Args:
        df: DataFrame with missing values
        
    Returns:
        DataFrame with imputed values
    """
    logger.info(f"Imputing missing values: {df.shape}")
    
    # Impute heat treatment with 'Unknown/Not Specified'
    if 'heat_treatment' in df.columns:
        df['heat_treatment'] = df['heat_treatment'].fillna('Unknown/Not Specified')
    
    # Impute composition with 0 for missing values
    composition_cols = [col for col in df.columns if col.startswith('composition_')]
    for col in composition_cols:
        if col in df.columns:
            df[col] = df[col].fillna(0)
    
    logger.info(f"Data after imputation: {df.shape}")
    return df
