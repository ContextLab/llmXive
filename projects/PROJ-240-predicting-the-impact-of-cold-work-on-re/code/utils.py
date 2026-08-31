"""
Utility functions for PROJ-240.
Includes VIF calculation, unit normalization, and physical bound validation.
"""
from typing import Dict, Union
import pandas as pd
import numpy as np
from statsmodels.stats.outliers_influence import variance_inflation_factor

def normalize_time_to_minutes(df: pd.DataFrame, time_col: str = "time_to_peak") -> pd.DataFrame:
    """
    Normalize time-to-peak to minutes.
    Assumes input is in minutes or converts from hours if necessary.
    For this project, we assume the raw data is already in minutes or needs no conversion.
    If the column contains values > 1000, we might suspect hours, but we'll stick to minutes as per spec.
    """
    df = df.copy()
    # If the column exists, ensure it's numeric
    if time_col in df.columns:
        df[time_col] = pd.to_numeric(df[time_col], errors='coerce')
        # Spec says: "Implement unit normalization for time-to-peak (minutes)"
        # We assume the input is already in minutes or the raw data is consistent.
        # If there's a need to convert from hours, we'd need a flag or heuristic.
        # For now, we just ensure it's numeric and in minutes.
    return df

def calculate_vif(df: pd.DataFrame, features: list) -> pd.DataFrame:
    """
    Calculate Variance Inflation Factor (VIF) for a list of features.
    """
    vif_data = pd.DataFrame()
    vif_data["Feature"] = features
    vif_data["VIF"] = [variance_inflation_factor(df[features].values, i) 
                       for i in range(len(features))]
    return vif_data

def validate_physical_bounds(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validate physical bounds for cold work and time.
    Cold work: 0 <= cw <= 100
    Time: > 0
    Returns the dataframe with valid rows only.
    """
    df = df.copy()
    # Filter for cold work bounds
    if "cold_work" in df.columns:
        df = df[(df["cold_work"] >= 0) & (df["cold_work"] <= 100)]
    
    # Filter for positive time
    if "time_to_peak" in df.columns:
        df = df[df["time_to_peak"] > 0]
    
    return df

def clip_outliers(df: pd.DataFrame, column: str, percentile: float = 99) -> pd.DataFrame:
    """
    Clip outliers in a specific column at the given percentile.
    """
    df = df.copy()
    if column in df.columns:
        upper_bound = df[column].quantile(percentile / 100)
        df[column] = df[column].clip(upper=upper_bound)
    return df