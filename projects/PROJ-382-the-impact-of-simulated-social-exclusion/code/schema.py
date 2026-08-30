"""
Data validation schema for social exclusion and prosocial behavior datasets.

This module defines Pydantic models and validation logic for the core
columns required by the pipeline: 'condition', 'prosocial_amount', and 'randomized'.

It provides:
- Pydantic models for row-level validation.
- Functions to validate Pandas DataFrames against the expected schema.
- Type coercion and normalization utilities.
"""
from typing import Any, Dict, List, Optional, Tuple, Union
import logging
import pandas as pd
import numpy as np
from pydantic import BaseModel, Field, field_validator, model_validator, ValidationError

logger = logging.getLogger(__name__)

# Constants for expected column names
COL_CONDITION = "condition"
COL_PROSOCIAL_AMOUNT = "prosocial_amount"
COL_RANDOMIZED = "randomized"

# Expected data types
CONDITION_DTYPE = "object"  # String categories
PROSOCIAL_DTYPE = "float64"  # Numerical amounts
RANDOMIZED_DTYPE = "bool"  # Boolean flag

class RawDataRow(BaseModel):
    """
    Pydantic model for a single row of raw data before full normalization.
    Used for strict validation of incoming records.
    """
    condition: Any = Field(..., description="Condition group identifier (e.g., 'excluded', 'control')")
    prosocial_amount: Any = Field(..., description="Amount donated or allocated (numeric)")
    randomized: Any = Field(..., description="Whether the study was randomized (True/False/Unknown)")

    @field_validator('condition')
    @classmethod
    def validate_condition(cls, v):
        if v is None or (isinstance(v, float) and np.isnan(v)):
            raise ValueError("Condition cannot be null or NaN")
        return str(v).strip()

    @field_validator('prosocial_amount')
    @classmethod
    def validate_prosocial_amount(cls, v):
        if v is None:
            return np.nan
        try:
            val = float(v)
            if np.isnan(val):
                return np.nan
            return val
        except (ValueError, TypeError):
            raise ValueError(f"prosocial_amount must be numeric, got {type(v)}")

    @field_validator('randomized')
    @classmethod
    def validate_randomized(cls, v):
        if v is None or (isinstance(v, float) and np.isnan(v)):
            return False  # Default to non-randomized if missing, handled later
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            v_lower = v.lower()
            if v_lower in ('true', '1', 'yes', 'y'):
                return True
            if v_lower in ('false', '0', 'no', 'n'):
                return False
            raise ValueError(f"randomized value '{v}' cannot be parsed as boolean")
        if isinstance(v, (int, np.integer)):
            return bool(v)
        raise ValueError(f"randomized must be boolean-like, got {type(v)}")

def validate_dataframe_schema(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Validates that a DataFrame contains the required columns and basic types.
    
    Args:
        df: The DataFrame to validate.
        
    Returns:
        A tuple (is_valid, errors) where is_valid is True if schema is correct,
        and errors is a list of error messages.
    """
    errors = []
    required_cols = [COL_CONDITION, COL_PROSOCIAL_AMOUNT, COL_RANDOMIZED]
    
    # Check for missing columns
    existing_cols = set(df.columns)
    missing_cols = set(required_cols) - existing_cols
    if missing_cols:
        errors.append(f"Missing required columns: {missing_cols}")
        return False, errors
        
    # Check dtypes loosely (allow object for condition, numeric for amount)
    if not pd.api.types.is_numeric_dtype(df[COL_PROSOCIAL_AMOUNT]):
        # Check if it can be coerced
        try:
            pd.to_numeric(df[COL_PROSOCIAL_AMOUNT], errors='raise')
        except (ValueError, TypeError):
            errors.append(f"Column '{COL_PROSOCIAL_AMOUNT}' is not numeric and cannot be coerced")
            
    if not pd.api.types.is_numeric_dtype(df[COL_RANDOMIZED]) and not pd.api.types.is_bool_dtype(df[COL_RANDOMIZED]):
        # Allow object if it contains boolean strings, but flag it
        if df[COL_RANDOMIZED].dtype == 'object':
            logger.debug(f"Column '{COL_RANDOMIZED}' is object type; will attempt boolean coercion.")
        else:
            errors.append(f"Column '{COL_RANDOMIZED}' is not boolean/numeric type (found {df[COL_RANDOMIZED].dtype})")
    
    return len(errors) == 0, errors

def validate_rows(df: pd.DataFrame, limit: Optional[int] = None) -> Dict[str, Any]:
    """
    Validates individual rows using the Pydantic model.
    
    Args:
        df: DataFrame to validate.
        limit: Optional limit on number of rows to check (for performance).
        
    Returns:
        Dictionary with validation statistics.
    """
    total_rows = len(df)
    valid_count = 0
    invalid_indices = []
    error_details = []
    
    check_limit = limit if limit else total_rows
    check_df = df.head(check_limit)
    
    for idx, row in check_df.iterrows():
        try:
            # Convert row to dict, handling potential NaNs gracefully
            row_dict = row.to_dict()
            RawDataRow(**row_dict)
            valid_count += 1
        except ValidationError as e:
            invalid_indices.append(idx)
            error_details.append({
                "index": idx,
                "errors": [err['msg'] for err in e.errors()]
            })
    
    return {
        "total_checked": check_limit,
        "valid": valid_count,
        "invalid": len(invalid_indices),
        "invalid_indices": invalid_indices,
        "error_details": error_details
    }

def ensure_schema_compliance(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensures the DataFrame columns match the expected schema by:
    1. Renaming columns if necessary (case-insensitive).
    2. Coercing types to expected dtypes.
    3. Filling missing required columns with defaults (if allowed) or raising.
    
    Args:
        df: Input DataFrame.
        
    Returns:
        DataFrame with standardized schema.
    """
    df = df.copy()
    
    # Normalize column names to lowercase
    df.columns = df.columns.str.lower()
    
    # Check for required columns again after normalization
    missing = [c for c in [COL_CONDITION, COL_PROSOCIAL_AMOUNT, COL_RANDOMIZED] if c not in df.columns]
    if missing:
        raise ValueError(f"Cannot ensure schema compliance: missing columns {missing}")
    
    # Coerce prosocial_amount to numeric
    df[COL_PROSOCIAL_AMOUNT] = pd.to_numeric(df[COL_PROSOCIAL_AMOUNT], errors='coerce')
    
    # Coerce randomized to boolean
    # Map common string representations to boolean
    bool_map = {
        'true': True, 'false': False, '1': True, '0': False,
        'yes': True, 'no': False, 'y': True, 'n': False
    }
    if df[COL_RANDOMIZED].dtype == 'object':
        df[COL_RANDOMIZED] = df[COL_RANDOMIZED].astype(str).str.lower().map(bool_map).fillna(False)
    else:
        df[COL_RANDOMIZED] = df[COL_RANDOMIZED].astype(bool)
        
    # Ensure condition is string
    df[COL_CONDITION] = df[COL_CONDITION].astype(str)
    
    return df