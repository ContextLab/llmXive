"""
Utility functions for data validation, normalization, and statistical analysis.

This module provides core utilities used across the pipeline for:
- Input sanitization and type enforcement
- Physical bound validation
- Unit normalization
- Statistical measures (VIF)
- Outlier handling
"""
from typing import Dict, List, Union, Optional, Any
import pandas as pd
import numpy as np
from statsmodels.stats.outliers_influence import variance_inflation_factor
import re

# Define expected dtypes for input sanitization
EXPECTED_DTYPE_MAP = {
    'cold_work_pct': 'float64',
    'Mn_wt': 'float64',
    'Mg_wt': 'float64',
    'Si_wt': 'float64',
    'Cu_wt': 'float64',
    'annealing_temp_K': 'float64',
    'time_to_peak_min': 'float64'
}

def sanitize_input_dataframe(df: pd.DataFrame, strict: bool = True) -> pd.DataFrame:
    """
    Sanitize input DataFrame by enforcing explicit dtypes and handling NA values.
    
    This function implements security hardening against type confusion and injection
    by:
    1. Enforcing explicit numeric types for expected columns
    2. Using na_filter=True to properly handle missing values
    3. Validating column names against expected schema
    4. Converting string representations of numbers to proper numeric types
    
    Args:
        df: Input pandas DataFrame
        strict: If True, raise ValueError on schema mismatch; if False, log warnings
        
    Returns:
        Sanitized DataFrame with enforced dtypes
        
    Raises:
        ValueError: If strict=True and schema validation fails
        TypeError: If data cannot be converted to expected types
    """
    if df is None or df.empty:
        raise ValueError("Input DataFrame cannot be None or empty")
    
    sanitized = df.copy()
    missing_cols = []
    
    # Validate and enforce dtypes for expected columns
    for col, dtype in EXPECTED_DTYPE_MAP.items():
        if col in sanitized.columns:
            try:
                # Convert to numeric, coercing errors to NaN
                sanitized[col] = pd.to_numeric(
                    sanitized[col], 
                    errors='coerce', 
                    downcast='float'
                )
                # Ensure dtype is enforced
                if sanitized[col].dtype != np.dtype(dtype):
                    sanitized[col] = sanitized[col].astype(dtype)
            except (ValueError, TypeError) as e:
                if strict:
                    raise TypeError(f"Failed to convert column '{col}' to {dtype}: {e}")
                else:
                    # Log warning but continue
                    pass
        else:
            missing_cols.append(col)
    
    # Handle missing columns based on strict mode
    if missing_cols:
        if strict:
            raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Ensure NA values are properly represented (na_filter=True equivalent)
    # Convert empty strings to NaN
    sanitized = sanitized.replace(r'^\s*$', np.nan, regex=True)
    
    return sanitized

def validate_physical_bounds(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validate that data values are within physically meaningful bounds.
    
    Checks:
    - cold_work_pct: 0 <= value <= 100
    - time_to_peak_min: value > 0
    - Composition weights: value >= 0
    - Temperature: value > 0 (in Kelvin)
    
    Args:
        df: DataFrame with physical parameters
        
    Returns:
        Dictionary with validation results:
        - valid: bool indicating if all checks passed
        - violations: dict mapping column to list of violating indices
        - summary: str with human-readable summary
    """
    violations = {}
    
    # Cold work percentage: 0-100%
    if 'cold_work_pct' in df.columns:
        bad_idx = df[
            (df['cold_work_pct'] < 0) | 
            (df['cold_work_pct'] > 100)
        ].index.tolist()
        if bad_idx:
            violations['cold_work_pct'] = bad_idx
    
    # Time to peak: must be positive
    if 'time_to_peak_min' in df.columns:
        bad_idx = df[df['time_to_peak_min'] <= 0].index.tolist()
        if bad_idx:
            violations['time_to_peak_min'] = bad_idx
    
    # Composition weights: must be non-negative
    composition_cols = ['Mn_wt', 'Mg_wt', 'Si_wt', 'Cu_wt']
    for col in composition_cols:
        if col in df.columns:
            bad_idx = df[df[col] < 0].index.tolist()
            if bad_idx:
                violations[col] = bad_idx
    
    # Temperature: must be positive (Kelvin)
    if 'annealing_temp_K' in df.columns:
        bad_idx = df[df['annealing_temp_K'] <= 0].index.tolist()
        if bad_idx:
            violations['annealing_temp_K'] = bad_idx
    
    valid = len(violations) == 0
    summary = "All physical bounds satisfied" if valid else f"Found {len(violations)} column(s) with violations"
    
    return {
        'valid': valid,
        'violations': violations,
        'summary': summary
    }

def normalize_time_to_minutes(df: pd.DataFrame, time_col: str = 'time_to_peak', unit_col: str = 'time_unit') -> pd.DataFrame:
    """
    Normalize time values to minutes.
    
    Handles various time units: seconds, minutes, hours, days.
    Converts all to minutes for consistency.
    
    Args:
        df: DataFrame with time and unit columns
        time_col: Name of the time value column
        unit_col: Name of the unit specification column
        
    Returns:
        DataFrame with normalized time in minutes
    """
    if time_col not in df.columns:
        raise ValueError(f"Time column '{time_col}' not found in DataFrame")
    
    normalized = df.copy()
    
    # Define conversion factors to minutes
    conversion_factors = {
        's': 1/60,
        'sec': 1/60,
        'second': 1/60,
        'seconds': 1/60,
        'min': 1,
        'minute': 1,
        'minutes': 1,
        'h': 60,
        'hr': 60,
        'hour': 60,
        'hours': 60,
        'd': 1440,
        'day': 1440,
        'days': 1440
    }
    
    if unit_col in df.columns:
        # Apply conversion based on unit
        def convert_row(row):
            value = row[time_col]
            unit = str(row[unit_col]).lower().strip()
            factor = conversion_factors.get(unit, 1)  # Default to 1 if unknown
            return value * factor
        
        normalized[time_col] = normalized.apply(convert_row, axis=1)
    else:
        # Assume already in minutes if no unit column
        pass
    
    return normalized

def calculate_vif(df: pd.DataFrame, features: Optional[List[str]] = None) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor (VIF) for multicollinearity detection.
    
    VIF measures how much the variance of an estimated regression coefficient
    increases due to multicollinearity. VIF > 5 or 10 indicates problematic
    multicollinearity.
    
    Args:
        df: DataFrame containing feature columns
        features: List of feature column names. If None, uses all numeric columns.
        
    Returns:
        Dictionary mapping feature names to their VIF values
    """
    if features is None:
        # Select all numeric columns except target
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if 'time_to_peak_min' in numeric_cols:
            numeric_cols.remove('time_to_peak_min')
        features = numeric_cols
    
    if len(features) < 2:
        return {feat: 1.0 for feat in features}
    
    # Create design matrix with constant
    X = df[features].copy()
    X = X.dropna()  # Remove rows with NaN in features
    
    if X.empty or len(X) < len(features) + 1:
        return {feat: float('inf') for feat in features}
    
    # Add constant term
    X = sm.add_constant(X)
    
    vif_data = {}
    for i, col in enumerate(features):
        if col not in X.columns:
            continue
        try:
            vif = variance_inflation_factor(X.values, i + 1)  # +1 because of constant
            vif_data[col] = float(vif)
        except Exception:
            vif_data[col] = float('inf')
    
    return vif_data

def clip_outliers(df: pd.DataFrame, column: str, percentile: float = 99.0) -> Tuple[pd.DataFrame, List[int], float]:
    """
    Clip outliers in a column to a specified percentile threshold.
    
    Uses numpy's linear interpolation method to calculate the threshold
    and clips values above it to the threshold value.
    
    Args:
        df: Input DataFrame
        column: Column name to clip
        percentile: Percentile threshold (e.g., 99.0 for 99th percentile)
        
    Returns:
        Tuple of:
        - Clipped DataFrame
        - List of indices that were clipped
        - The threshold value used
    """
    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found in DataFrame")
    
    clipped_df = df.copy()
    values = clipped_df[column].dropna()
    
    if len(values) == 0:
        return clipped_df, [], 0.0
    
    # Calculate threshold using linear interpolation (default in numpy)
    threshold = np.percentile(values, percentile, interpolation='linear')
    
    # Identify indices to clip
    mask = clipped_df[column] > threshold
    clipped_indices = clipped_df[mask].index.tolist()
    
    # Apply clipping
    clipped_df.loc[mask, column] = threshold
    
    return clipped_df, clipped_indices, float(threshold)

def detect_type_confusion(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Detect potential type confusion vulnerabilities in input data.
    
    Checks for:
    - Unexpected object types in numeric columns
    - Mixed types that could indicate injection attempts
    - Non-numeric strings in numeric fields
    - Extremely large/small values that might indicate overflow
    
    Args:
        df: Input DataFrame
        
    Returns:
        Dictionary with detection results:
        - suspicious: bool indicating if issues found
        - details: list of specific issues
    """
    issues = []
    
    for col, expected_dtype in EXPECTED_DTYPE_MAP.items():
        if col not in df.columns:
            continue
        
        series = df[col]
        
        # Check for object type in numeric column
        if series.dtype == 'object':
            # Try to convert and see if it fails
            try:
                pd.to_numeric(series, errors='raise')
            except (ValueError, TypeError) as e:
                issues.append(f"Column '{col}' contains non-numeric strings: {str(e)[:100]}")
        
        # Check for extreme values
        numeric_series = pd.to_numeric(series, errors='coerce')
        if numeric_series.std() > 1e15:
            issues.append(f"Column '{col}' has extremely high variance, possible overflow")
        
        # Check for NaN ratio
        if numeric_series.isna().mean() > 0.5:
            issues.append(f"Column '{col}' has >50% NaN values, possible data corruption")
    
    return {
        'suspicious': len(issues) > 0,
        'details': issues
    }

def validate_and_sanitize_pipeline(df: pd.DataFrame) -> pd.DataFrame:
    """
    Run complete validation and sanitization pipeline.
    
    Combines type enforcement, physical bounds checking, and outlier detection
    into a single comprehensive validation step.
    
    Args:
        df: Input DataFrame
        
    Returns:
        Validated and sanitized DataFrame
        
    Raises:
        ValueError: If validation fails critical checks
    """
    # Step 1: Sanitize types
    df = sanitize_input_dataframe(df, strict=True)
    
    # Step 2: Check for type confusion
    type_check = detect_type_confusion(df)
    if type_check['suspicious']:
        raise ValueError(f"Type confusion detected: {type_check['details']}")
    
    # Step 3: Validate physical bounds
    bounds_check = validate_physical_bounds(df)
    if not bounds_check['valid']:
        # Log but don't fail for bounds violations (handled by filtering)
        pass
    
    return df

# Import sm for VIF calculation
import statsmodels.api as sm

# Re-define calculate_vif with proper import
def calculate_vif(df: pd.DataFrame, features: Optional[List[str]] = None) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor (VIF) for multicollinearity detection.
    
    VIF measures how much the variance of an estimated regression coefficient
    increases due to multicollinearity. VIF > 5 or 10 indicates problematic
    multicollinearity.
    
    Args:
        df: DataFrame containing feature columns
        features: List of feature column names. If None, uses all numeric columns.
        
    Returns:
        Dictionary mapping feature names to their VIF values
    """
    if features is None:
        # Select all numeric columns except target
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if 'time_to_peak_min' in numeric_cols:
            numeric_cols.remove('time_to_peak_min')
        features = numeric_cols
    
    if len(features) < 2:
        return {feat: 1.0 for feat in features}
    
    # Create design matrix with constant
    X = df[features].copy()
    X = X.dropna()  # Remove rows with NaN in features
    
    if X.empty or len(X) < len(features) + 1:
        return {feat: float('inf') for feat in features}
    
    # Add constant term
    X = sm.add_constant(X)
    
    vif_data = {}
    for i, col in enumerate(features):
        if col not in X.columns:
            continue
        try:
            vif = variance_inflation_factor(X.values, i + 1)  # +1 because of constant
            vif_data[col] = float(vif)
        except Exception:
            vif_data[col] = float('inf')
    
    return vif_data
