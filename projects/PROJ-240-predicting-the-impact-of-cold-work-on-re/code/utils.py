"""
Utility functions for the llmXive project.

Provides constants, Variance Inflation Factor (VIF) calculation,
and unit normalization helpers.
"""

from typing import Dict, Union
import pandas as pd
import numpy as np
from statsmodels.stats.outliers_influence import variance_inflation_factor

# Constants
COLD_WORK_MAX_PERCENT = 100.0
COLD_WORK_MIN_PERCENT = 0.0
TIME_MINUTES_UNIT = "minutes"
TIME_SECONDS_UNIT = "seconds"
TIME_HOURS_UNIT = "hours"

# Physical bounds for validation
VALID_COLD_WORK_RANGE = (0.0, 100.0)
VALID_TIME_RANGE = (0.0, float('inf'))

def normalize_time_to_minutes(value: Union[float, int], unit: str) -> float:
    """
    Normalize time values to minutes.
    
    Args:
        value: The time value to normalize.
        unit: The unit of the input value ('minutes', 'seconds', 'hours').
        
    Returns:
        The time value normalized to minutes.
        
    Raises:
        ValueError: If the unit is not recognized.
    """
    if value < 0:
        raise ValueError(f"Time value cannot be negative: {value}")
        
    if unit == TIME_MINUTES_UNIT:
        return float(value)
    elif unit == TIME_SECONDS_UNIT:
        return float(value) / 60.0
    elif unit == TIME_HOURS_UNIT:
        return float(value) * 60.0
    else:
        raise ValueError(f"Unrecognized time unit: {unit}. Supported: {TIME_MINUTES_UNIT}, {TIME_SECONDS_UNIT}, {TIME_HOURS_UNIT}")

def calculate_vif(df: pd.DataFrame, exclude_intercept: bool = True) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor (VIF) for each feature in a DataFrame.
    
    VIF is used to detect multicollinearity in regression analysis.
    A VIF > 5 or 10 indicates high multicollinearity.
    
    Args:
        df: A pandas DataFrame containing numerical features.
        exclude_intercept: If True, the constant/intercept column is excluded from calculation.
        
    Returns:
        A dictionary mapping feature names to their VIF values.
        
    Raises:
        ValueError: If the DataFrame contains non-numeric columns or is empty.
    """
    if df.empty:
        raise ValueError("DataFrame cannot be empty for VIF calculation.")
        
    # Ensure all columns are numeric
    if not np.issubdtype(df.values.dtype, np.number):
        # Attempt to select only numeric columns
        numeric_df = df.select_dtypes(include=[np.number])
        if numeric_df.empty:
            raise ValueError("DataFrame must contain numeric columns for VIF calculation.")
        df = numeric_df
        
    # Add constant for intercept if not already present and requested
    # statsmodels VIF requires a constant column if calculating for intercept-inclusive models,
    # but typically we calculate VIF for predictors, so we add a constant column explicitly
    # if we want to see the VIF of the intercept (usually not useful), or just ensure
    # the matrix is full rank. The standard approach is to add a constant column.
    
    # We need to add a column of ones for the intercept to calculate VIF correctly
    # for the other features.
    df_with_const = df.copy()
    
    # Check if a constant column already exists (all 1s)
    has_constant = False
    for col in df_with_const.columns:
        if np.allclose(df_with_const[col].values, 1.0):
            has_constant = True
            break
    
    if not has_constant:
        df_with_const['const'] = 1.0
        
    vif_data = {}
    for i, col in enumerate(df_with_const.columns):
        # Skip the constant column if requested
        if exclude_intercept and col == 'const':
            continue
            
        try:
            vif = variance_inflation_factor(df_with_const.values, i)
            vif_data[col] = vif
        except Exception as e:
            # Handle cases where VIF cannot be calculated (e.g., perfect multicollinearity)
            vif_data[col] = float('inf')
            
    return vif_data

def validate_physical_bounds(
    cold_work: float, 
    time_to_peak: float
) -> bool:
    """
    Validate if cold work and time_to_peak are within physical bounds.
    
    Args:
        cold_work: Percentage of cold work (0-100).
        time_to_peak: Time to peak softening (must be positive).
        
    Returns:
        True if values are within bounds, False otherwise.
    """
    cw_valid = VALID_COLD_WORK_RANGE[0] <= cold_work <= VALID_COLD_WORK_RANGE[1]
    time_valid = time_to_peak > VALID_TIME_RANGE[0]
    
    return cw_valid and time_valid

def clip_outliers(
    df: pd.DataFrame, 
    column: str, 
    percentile: float = 99.0
) -> pd.DataFrame:
    """
    Clip outliers in a specific column to the specified percentile.
    
    Args:
        df: Input DataFrame.
        column: Name of the column to clip.
        percentile: Percentile value to clip at (e.g., 99.0 for 99th percentile).
        
    Returns:
        DataFrame with clipped values.
    """
    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found in DataFrame.")
        
    clip_value = df[column].quantile(percentile / 100.0)
    df_clipped = df.copy()
    df_clipped[column] = df_clipped[column].clip(upper=clip_value)
    
    return df_clipped