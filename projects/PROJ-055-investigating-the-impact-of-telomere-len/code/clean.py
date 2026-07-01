"""
Utility functions for cleaning telomere data and unit conversion.
"""
import pandas as pd
import numpy as np
from typing import Union, List, Dict, Any

# Conversion factors to kilobases (kb)
# 1 kb = 1000 bp
# 1 kb = 1000 bases (assuming bases ~ bp for dsDNA)
CONVERSION_FACTORS = {
    'bp': 1.0 / 1000.0,
    'bases': 1.0 / 1000.0,
    'base_pairs': 1.0 / 1000.0,
    'kb': 1.0,
    'kilobases': 1.0,
    'kbp': 1.0,
    'relative': None, # Cannot convert relative units without a standard
    'ct': None,       # Cycle threshold, needs calibration curve
    'cycles': None,
    'ratio': None,
}

def convert_to_kb(value: Union[float, int, str], unit: str) -> Union[float, None]:
    """
    Convert a telomere length value to kilobases (kb).
    
    Args:
        value: The numeric value of the telomere length.
        unit: The unit of the value (e.g., 'bp', 'kb', 'relative').
    
    Returns:
        The value in kb, or None if conversion is not possible.
    
    Raises:
        ValueError: If the unit is unknown or conversion fails.
    """
    if pd.isna(value):
        return None
    
    try:
        num_val = float(value)
    except (ValueError, TypeError):
        raise ValueError(f"Invalid numeric value: {value}")
    
    unit_lower = str(unit).strip().lower()
    
    if unit_lower not in CONVERSION_FACTORS:
        raise ValueError(f"Unknown unit: {unit}")
    
    factor = CONVERSION_FACTORS[unit_lower]
    
    if factor is None:
        raise ValueError(f"Cannot convert unit '{unit}' to kb without calibration.")
    
    return num_val * factor

def clean_telomere_units(df: pd.DataFrame, unit_col: str = 'unit', value_col: str = 'telomere_length') -> pd.DataFrame:
    """
    Standardize unit strings in a dataframe column to match CONVERSION_FACTORS keys.
    
    Args:
        df: The dataframe containing the data.
        unit_col: The name of the column containing units.
        value_col: The name of the column containing values.
    
    Returns:
        A copy of the dataframe with standardized units.
    """
    df_clean = df.copy()
    
    def standardize_unit(u):
        if pd.isna(u):
            return 'unknown'
        u_lower = str(u).strip().lower()
        # Map common variations
        if u_lower in ['bp', 'base pairs', 'basepair']:
            return 'bp'
        if u_lower in ['kb', 'kilobase', 'kilobases']:
            return 'kb'
        if u_lower in ['relative', 'rel', 't/s ratio']:
            return 'relative'
        if u_lower in ['ct', 'cycle threshold']:
            return 'ct'
        return u_lower # Return as is if not matched, will raise error in conversion if needed
    
    df_clean[unit_col] = df_clean[unit_col].apply(standardize_unit)
    return df_clean
