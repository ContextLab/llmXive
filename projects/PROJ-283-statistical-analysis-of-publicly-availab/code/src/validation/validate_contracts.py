"""
Contract validation module for the chess Elo analysis pipeline.

Loads YAML schemas from specs/contracts/ and validates in-memory
pandas DataFrames against them.
"""
import os
import re
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, field

import pandas as pd
import yaml


@dataclass
class ValidationResult:
    """Result of a contract validation run."""
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    schema_path: Optional[str] = None
    df_shape: Optional[Tuple[int, int]] = None

def _load_schema(schema_path: str) -> Dict[str, Any]:
    """Load a YAML schema file."""
    path = Path(schema_path)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        schema = yaml.safe_load(f)
    
    if not isinstance(schema, dict):
        raise ValueError(f"Invalid schema format in {schema_path}: expected a dictionary")
    
    return schema

def _validate_columns(df: pd.DataFrame, schema: Dict[str, Any]) -> List[str]:
    """Validate that DataFrame has all required columns defined in schema."""
    errors = []
    
    if 'columns' not in schema:
        return errors
    
    required_columns = schema.get('columns', {})
    if not isinstance(required_columns, dict):
        errors.append(f"Invalid 'columns' definition in schema: expected a dictionary")
        return errors
    
    df_columns = set(df.columns)
    schema_columns = set(required_columns.keys())
    
    missing = schema_columns - df_columns
    if missing:
        errors.append(f"Missing required columns: {sorted(missing)}")
    
    extra = df_columns - schema_columns
    # Warn about extra columns but don't fail
    if extra:
        pass  # Could add warnings here if needed
    
    return errors

def _validate_types(df: pd.DataFrame, schema: Dict[str, Any]) -> List[str]:
    """Validate column types match schema definitions."""
    errors = []
    
    if 'columns' not in schema:
        return errors
    
    column_specs = schema.get('columns', {})
    if not isinstance(column_specs, dict):
        return errors
    
    for col_name, col_spec in column_specs.items():
        if col_name not in df.columns:
            continue  # Already reported in column validation
        
        if not isinstance(col_spec, dict):
            continue
        
        expected_type = col_spec.get('type')
        if not expected_type:
            continue
        
        actual_dtype = df[col_name].dtype
        
        # Map common YAML types to pandas dtypes
        type_mapping = {
            'integer': ['int64', 'int32', 'int16', 'int8', 'UInt64', 'UInt32', 'UInt16', 'UInt8'],
            'number': ['float64', 'float32', 'int64', 'int32', 'int16', 'int8'],
            'string': ['object', 'string'],
            'boolean': ['bool'],
            'datetime': ['datetime64[ns]'],
        }
        
        expected_pandas_types = type_mapping.get(expected_type.lower(), [expected_type])
        
        # Check if actual type matches expected
        type_match = False
        for exp_type in expected_pandas_types:
            if exp_type in str(actual_dtype):
                type_match = True
                break
        
        if not type_match:
            errors.append(
                f"Column '{col_name}': expected type '{expected_type}' "
                f"(pandas: {expected_pandas_types}), got '{actual_dtype}'"
            )
    
    return errors

def _validate_constraints(df: pd.DataFrame, schema: Dict[str, Any]) -> List[str]:
    """Validate data constraints (nulls, ranges, etc.)."""
    errors = []
    
    if 'columns' not in schema:
        return errors
    
    column_specs = schema.get('columns', {})
    if not isinstance(column_specs, dict):
        return errors
    
    for col_name, col_spec in column_specs.items():
        if col_name not in df.columns:
            continue
        
        if not isinstance(col_spec, dict):
            continue
        
        # Check for null values if required
        is_required = col_spec.get('required', False)
        if is_required and df[col_name].isna().any():
            null_count = df[col_name].isna().sum()
            errors.append(
                f"Column '{col_name}' is marked as required but contains {null_count} null values"
            )
        
        # Check for unique values if specified
        is_unique = col_spec.get('unique', False)
        if is_unique and df[col_name].duplicated().any():
            dup_count = df[col_name].duplicated().sum()
            errors.append(
                f"Column '{col_name}' is marked as unique but contains {dup_count} duplicate values"
            )
        
        # Check numeric ranges if specified
        if 'min' in col_spec or 'max' in col_spec:
            if not pd.api.types.is_numeric_dtype(df[col_name]):
                continue
            
            min_val = col_spec.get('min')
            max_val = col_spec.get('max')
            
            if min_val is not None:
                below_min = (df[col_name] < min_val).sum()
                if below_min > 0:
                    errors.append(
                        f"Column '{col_name}': {below_min} values below minimum {min_val}"
                    )
            
            if max_val is not None:
                above_max = (df[col_name] > max_val).sum()
                if above_max > 0:
                    errors.append(
                        f"Column '{col_name}': {above_max} values above maximum {max_val}"
                    )
        
        # Check for allowed values if specified
        allowed_values = col_spec.get('allowed_values')
        if allowed_values is not None:
            if not isinstance(allowed_values, list):
                continue
            
            invalid_mask = ~df[col_name].isin(allowed_values)
            if invalid_mask.any():
                invalid_count = invalid_mask.sum()
                invalid_examples = df[invalid_mask].head(5).unique()
                errors.append(
                    f"Column '{col_name}': {invalid_count} values not in allowed set. "
                    f"Examples: {invalid_examples[:3]}"
                )
    
    return errors

def validate_dataframe(
    df: pd.DataFrame,
    schema_path: str,
    schema_name: Optional[str] = None
) -> ValidationResult:
    """
    Validate a pandas DataFrame against a YAML schema.
    
    Args:
        df: The DataFrame to validate
        schema_path: Path to the YAML schema file
        schema_name: Optional name for the schema (used in error messages)
    
    Returns:
        ValidationResult with validation status and any errors/warnings
    """
    errors = []
    warnings = []
    
    try:
        schema = _load_schema(schema_path)
    except FileNotFoundError as e:
        return ValidationResult(
            valid=False,
            errors=[str(e)],
            schema_path=schema_path,
            df_shape=(df.shape[0], df.shape[1])
        )
    except Exception as e:
        return ValidationResult(
            valid=False,
            errors=[f"Error loading schema: {str(e)}"],
            schema_path=schema_path,
            df_shape=(df.shape[0], df.shape[1])
        )
    
    # Run all validators
    errors.extend(_validate_columns(df, schema))
    errors.extend(_validate_types(df, schema))
    errors.extend(_validate_constraints(df, schema))
    
    return ValidationResult(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        schema_path=schema_path,
        df_shape=(df.shape[0], df.shape[1])
    )

def validate_game_records(df: pd.DataFrame) -> ValidationResult:
    """
    Validate a DataFrame against the game_record schema.
    
    Args:
        df: DataFrame to validate
    
    Returns:
        ValidationResult
    """
    from src.config import get_contract_path
    schema_path = get_contract_path('game_record.schema.yaml')
    return validate_dataframe(df, schema_path, 'game_record')

def validate_model_output(df: pd.DataFrame) -> ValidationResult:
    """
    Validate a DataFrame against the model_output schema.
    
    Args:
        df: DataFrame to validate
    
    Returns:
        ValidationResult
    """
    from src.config import get_contract_path
    schema_path = get_contract_path('model_output.schema.yaml')
    return validate_dataframe(df, schema_path, 'model_output')

def assert_valid(
    df: pd.DataFrame,
    schema_path: str,
    schema_name: str
) -> None:
    """
    Validate DataFrame and raise AssertionError if invalid.
    
    Args:
        df: DataFrame to validate
        schema_path: Path to schema file
        schema_name: Name for error messages
    
    Raises:
        AssertionError: If validation fails
    """
    result = validate_dataframe(df, schema_path, schema_name)
    if not result.valid:
        error_msg = f"Validation failed for {schema_name}:\n"
        error_msg += "\n".join(f"  - {err}" for err in result.errors)
        raise AssertionError(error_msg)

def assert_game_records_valid(df: pd.DataFrame) -> None:
    """Assert that DataFrame matches game_record schema."""
    from src.config import get_contract_path
    schema_path = get_contract_path('game_record.schema.yaml')
    assert_valid(df, schema_path, 'GameRecord')

def assert_model_output_valid(df: pd.DataFrame) -> None:
    """Assert that DataFrame matches model_output schema."""
    from src.config import get_contract_path
    schema_path = get_contract_path('model_output.schema.yaml')
    assert_valid(df, schema_path, 'ModelOutput')
