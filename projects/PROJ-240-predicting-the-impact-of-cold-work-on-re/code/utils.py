"""
Utility functions for data processing and analysis.

Provides common operations used across multiple pipeline stages.
"""
from typing import Dict, List, Union
import pandas as pd
import numpy as np
from statsmodels.stats.outliers_influence import variance_inflation_factor


def normalize_time_to_minutes(df: pd.DataFrame, column: str = "time_to_peak_min") -> pd.DataFrame:
    """
    Ensure time-to-peak values are in minutes.

    Converts seconds to minutes if values exceed a threshold.

    Args:
        df: Input DataFrame
        column: Name of the time column

    Returns:
        DataFrame with normalized time values
    """
    df = df.copy()
    # If values are in seconds (very large numbers), convert to minutes
    # Assuming typical recrystallization times are in minutes range (1-1000)
    if df[column].max() > 60000:
        df[column] = df[column] / 60.0
    return df


def calculate_vif(df: pd.DataFrame, features: List[str]) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor for features.

    Args:
        df: DataFrame containing features
        features: List of feature column names

    Returns:
        Dictionary mapping feature names to VIF values
    """
    vif_data = {}
    # Prepare clean data for VIF calculation
    X = df[features].dropna()

    if len(X) == 0 or X.shape[1] < 2:
        for feature in features:
            vif_data[feature] = np.nan
        return vif_data

    for feature in features:
        if feature in df.columns:
            idx = features.index(feature)
            vif = variance_inflation_factor(X.values, idx)
            vif_data[feature] = vif
        else:
            vif_data[feature] = np.nan

    return vif_data


def validate_physical_bounds(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validate that physical bounds are respected.

    Checks:
    - 0 <= cold_work <= 100
    - time_to_peak > 0
    - composition values >= 0

    Args:
        df: Input DataFrame

    Returns:
        Filtered DataFrame with valid rows
    """
    df = df.copy()

    valid_cold_work = (df["cold_work_pct"] >= 0) & (df["cold_work_pct"] <= 100)
    valid_time = df["time_to_peak_min"] > 0

    composition_cols = ["Mn_wt", "Mg_wt", "Si_wt", "Cu_wt"]
    valid_compositions = pd.Series([True] * len(df), index=df.index)

    for col in composition_cols:
        if col in df.columns:
            valid_compositions &= (df[col] >= 0)

    valid_mask = valid_cold_work & valid_time & valid_compositions
    return df[valid_mask]


def clip_outliers(df: pd.DataFrame, column: str, percentile: int = 99) -> pd.DataFrame:
    """
    Clip outliers in a column to the specified percentile.

    Args:
        df: Input DataFrame
        column: Column name to clip
        percentile: Upper percentile threshold

    Returns:
        DataFrame with clipped values
    """
    df = df.copy()
    if column in df.columns:
        upper_bound = df[column].quantile(percentile / 100.0)
        df[column] = df[column].clip(upper=upper_bound)
    return df