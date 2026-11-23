import os
import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from code.utils.logging import get_logger

def standardize_units(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize units in the dataframe (e.g., convert to SI)."""
    # Placeholder for unit conversion logic
    return df

def impute_median(df: pd.DataFrame, threshold: float = 0.2) -> pd.DataFrame:
    """Impute missing values with median if missingness <= threshold."""
    df_copy = df.copy()
    for col in df_copy.columns:
        if df_copy[col].isnull().mean() <= threshold:
            df_copy[col].fillna(df_copy[col].median(), inplace=True)
        elif df_copy[col].isnull().mean() > 0:
            get_logger().warning(f"Column {col} has > {threshold*100}% missing values. Dropping or skipping imputation.")
    return df_copy

def remove_outliers_3sigma(df: pd.DataFrame) -> pd.DataFrame:
    """Remove rows where any feature is > 3 sigma from the mean."""
    df_copy = df.copy()
    # Only apply to numeric columns
    numeric_cols = df_copy.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) == 0:
        return df_copy
    
    mask = np.ones(len(df_copy), dtype=bool)
    for col in numeric_cols:
        mean = df_copy[col].mean()
        std = df_copy[col].std()
        if std == 0:
            continue
        z_scores = np.abs((df_copy[col] - mean) / std)
        mask &= (z_scores <= 3)
    
    return df_copy[mask]

def derive_physics_features(df: pd.DataFrame) -> pd.DataFrame:
    """Derive physics-based features like strain rate, Zener-Hollomon."""
    df_copy = df.copy()
    # Example: Zener-Hollomon parameter Z = strain_rate * exp(Q/RT)
    # Assuming columns 'strain_rate', 'temperature' exist
    if 'strain_rate' in df_copy.columns and 'temperature' in df_copy.columns:
        R = 8.314 # J/(mol*K)
        Q = 140000 # Activation energy J/mol (example for Al)
        df_copy['Zener_Hollomon'] = df_copy['strain_rate'] * np.exp(Q / (R * df_copy['temperature']))
    return df_copy

def process_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """Full pipeline: standardize, impute, remove outliers, derive features."""
    df = standardize_units(df)
    df = impute_median(df)
    df = remove_outliers_3sigma(df)
    df = derive_physics_features(df)
    return df
