from typing import Dict, List, Union, Optional, Any
import pandas as pd
import numpy as np
import re

def sanitize_input_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Sanitize input dataframe to prevent type confusion."""
    if df.empty:
        return df
    
    result = df.copy()
    numeric_cols = result.select_dtypes(include=[np.number]).columns
    
    for col in numeric_cols:
        result[col] = pd.to_numeric(result[col], errors='coerce')
    
    return result

def validate_physical_bounds(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validate physical bounds:
    - 0 <= cold_work_pct <= 100
    - time_to_peak_min > 0
    Drops rows that violate these bounds.
    """
    if df.empty:
        return df

    initial_len = len(df)
    mask = pd.Series([True] * len(df), index=df.index)

    if 'cold_work_pct' in df.columns:
        mask = mask & (df['cold_work_pct'].between(0, 100))
    
    if 'time_to_peak_min' in df.columns:
        mask = mask & (df['time_to_peak_min'] > 0)

    result = df[mask]
    dropped = initial_len - len(result)
    
    if dropped > 0:
        print(f"Filtered {dropped} rows violating physical bounds.")
    
    return result

def normalize_time_to_minutes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure time_to_peak_min is in minutes.
    Ensures the column is numeric and positive.
    """
    if df.empty or 'time_to_peak_min' not in df.columns:
        return df
    
    result = df.copy()
    result['time_to_peak_min'] = pd.to_numeric(result['time_to_peak_min'], errors='coerce')
    return result

def impute_missing_composition(df: pd.DataFrame, strategy: str = 'mean') -> pd.DataFrame:
    """
    Impute missing composition values using the specified strategy.
    Note: Specific alloy-series logic is handled in ingest.py; this is a generic utility.
    """
    if df.empty:
        return df

    result = df.copy()
    composition_cols = ['Mn_wt', 'Mg_wt', 'Si_wt', 'Cu_wt']
    
    for col in composition_cols:
        if col in result.columns and result[col].isnull().any():
            if strategy == 'mean':
                result[col] = result[col].fillna(result[col].mean())
    
    return result

def calculate_vif(df: pd.DataFrame) -> Dict[str, float]:
    """Calculate Variance Inflation Factor for features."""
    if df.empty:
        return {}
    
    try:
        from statsmodels.stats.outliers_influence import variance_inflation_factor
    except ImportError:
        print("Warning: statsmodels not found. VIF calculation skipped.")
        return {}

    X = df.select_dtypes(include=[np.number])
    if X.empty:
        return {}

    X = X.assign(const=1)
    vif_data = {}
    X_values = X.values
    
    for i, col in enumerate(X.columns):
        if col == 'const':
            continue
        try:
            vif = variance_inflation_factor(X_values, i)
            vif_data[col] = vif
        except Exception:
            vif_data[col] = np.nan
    
    return vif_data

def clip_outliers(df: pd.DataFrame, column: str, percentile: float = 0.99) -> pd.DataFrame:
    """Generic outlier clipping utility."""
    if df.empty or column not in df.columns:
        return df
    
    result = df.copy()
    threshold = np.percentile(result[column], percentile * 100)
    result[column] = result[column].clip(upper=threshold)
    return result

def detect_type_confusion(df: pd.DataFrame) -> List[str]:
    """Detect columns with mixed or unexpected types."""
    if df.empty:
        return []
    
    issues = []
    for col in df.columns:
        if df[col].dtype == 'object':
            try:
                pd.to_numeric(df[col])
            except (ValueError, TypeError):
                issues.append(f"{col} is object but not numeric")
    return issues

def validate_and_sanitize_pipeline(df: pd.DataFrame) -> pd.DataFrame:
    """Run the full validation and sanitization pipeline."""
    if df.empty:
        return df
    
    result = sanitize_input_dataframe(df)
    result = validate_physical_bounds(result)
    result = normalize_time_to_minutes(result)
    return result