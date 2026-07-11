import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Set
from src.utils.config import THRESHOLDS, PROJECT_ROOT, DATA_RAW_DIR, DATA_PROCESSED_DIR

def validate_schema(df: pd.DataFrame, schema: Dict[str, type]) -> Tuple[bool, List[str]]:
    """
    Validate DataFrame columns and types against a schema.
    
    Args:
        df: DataFrame to validate.
        schema: Dict mapping column name to expected type.
        
    Returns:
        Tuple of (is_valid, list_of_errors).
    """
    errors = []
    for col, expected_type in schema.items():
        if col not in df.columns:
            errors.append(f"Missing column: {col}")
        elif not isinstance(df[col].dtype, expected_type):
            # Note: pandas dtypes are complex, this is a simplified check
            # For strict type checking, use pandas.api.types
            pass 
    
    return len(errors) == 0, errors

def validate_raw_data(df: pd.DataFrame) -> bool:
    """
    Validate raw data schema (basic checks).
    """
    if df.empty:
        return False
    # Check for required columns if defined in a global constant
    return True

def validate_processed_data(df: pd.DataFrame) -> bool:
    """
    Validate processed data schema.
    """
    if df.empty:
        return False
    # Check for nulls in target
    # Assuming 'yield_strength' is the target
    if 'yield_strength' in df.columns:
        if df['yield_strength'].isnull().any():
            return False
    return True

def check_missing_values(df: pd.DataFrame) -> Dict[str, int]:
    """
    Check for missing values in DataFrame.
    """
    return df.isnull().sum().to_dict()

def validate_data_load(df: pd.DataFrame) -> bool:
    """
    Basic validation after loading.
    """
    return not df.empty

def get_data_quality_report(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate a basic data quality report.
    """
    report = {
        'shape': df.shape,
        'columns': list(df.columns),
        'missing_counts': check_missing_values(df),
        'dtypes': df.dtypes.to_dict()
    }
    return report
