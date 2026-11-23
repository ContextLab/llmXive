"""
Validation module for enforcing schema contracts.
Provides functions to load schemas, validate field types, enums, ranges,
and entire dataframes against defined contracts.
"""
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import pandas as pd
import numpy as np
import yaml

logger = logging.getLogger(__name__)

def load_schema(schema_path: Union[str, Path]) -> Dict[str, Any]:
    """Load a YAML schema file."""
    path = Path(schema_path)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {path}")
    
    with open(path, 'r') as f:
        return yaml.safe_load(f)

    Args:
        schema_path: Path to the schema YAML file.

    Returns:
        Dictionary containing the schema definition.
    """
    try:
        with open(schema_path, 'r') as f:
            schema = yaml.safe_load(f)
        logger.info(f"Schema loaded from {schema_path}")
        return schema
    except Exception as e:
        logger.error(f"Error loading schema from {schema_path}: {e}")
        raise

def validate_field_type(value: Any, expected_type: str) -> bool:
    """
    Validate if a value matches the expected type.

    Args:
        value: The value to check.
        expected_type: The expected type as a string ('str', 'int', 'float', 'bool').

    Returns:
        True if valid, False otherwise.
    """
    if pd.isna(value):
        return True  # Null handling is separate

    if expected_type == 'str':
        return isinstance(value, str)
    elif expected_type == 'int':
        # Allow numpy integer types
        return isinstance(value, (int, np.integer))
    elif expected_type == 'float':
        # Allow numpy float types
        return isinstance(value, (float, np.floating))
    elif expected_type == 'bool':
        # Allow numpy bool types
        return isinstance(value, (bool, np.bool_))
    else:
        logger.warning(f"Unknown type definition: {expected_type}")
        return False

def validate_enum(value: Any, allowed_values: List[str]) -> bool:
    """
    Validate if a value is in the allowed list for an enum field.

    Args:
        value: The value to check.
        allowed_values: List of allowed string values.

    Returns:
        True if valid, False otherwise.
    """
    if pd.isna(value):
        return True

    # Convert to string for comparison if necessary
    str_value = str(value)
    return str_value in allowed_values

def validate_range(value: Any, constraints: Dict[str, Any]) -> bool:
    """
    Validate if a numeric value is within specified constraints.

    Args:
        value: The value to check.
        constraints: Dictionary containing 'min' and/or 'max' keys.

    Returns:
        True if valid, False otherwise.
    """
    if pd.isna(value):
        return True

    try:
        num_value = float(value)
    except (ValueError, TypeError):
        return False

    if 'min' in constraints and num_value < constraints['min']:
        return False
    if 'max' in constraints and num_value > constraints['max']:
        return False

    return True

def validate_dataframe_against_schema(df: pd.DataFrame, schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate a pandas DataFrame against a schema definition.

    Args:
        df: The DataFrame to validate.
        schema: The schema dictionary.

    Returns:
        Dictionary with 'valid' (bool) and 'details' (list of errors).
    """
    errors = []
    valid = True

    # Get entity definition (assuming single entity for now)
    if 'entities' not in schema or not schema['entities']:
        errors.append("Schema must define at least one entity.")
        return {"valid": False, "details": errors}

    entity = schema['entities'][0]
    fields = entity.get('fields', [])

    # Check for required columns
    for field in fields:
        field_name = field['name']
        if field_name not in df.columns:
            errors.append(f"Missing required column: {field_name}")
            valid = False

    if not valid:
        return {"valid": False, "details": errors}

    # Validate each row (vectorized where possible, row-by-row for complex checks)
    for field in fields:
        field_name = field['name']
        field_type = field['type']
        constraints = field.get('constraints', [])

        # Check for not_null
        if 'not_null' in constraints:
            null_count = df[field_name].isna().sum()
            if null_count > 0:
                errors.append(f"Column '{field_name}' contains {null_count} null values, but 'not_null' constraint is set.")
                valid = False

        # Check type
        if field_type in ['int', 'float', 'bool', 'str']:
            # Pandas usually infers types, but we check specific values for robustness
            # For strict int, we ensure no floats are stored if type is int
            if field_type == 'int':
                # Check if any non-integer floats exist
                non_int_mask = df[field_name].apply(lambda x: not (isinstance(x, (int, np.integer)) or pd.isna(x) or (isinstance(x, float) and x.is_integer())))
                if non_int_mask.any():
                    errors.append(f"Column '{field_name}' contains non-integer values, but type is defined as 'int'.")
                    valid = False
            elif field_type == 'bool':
                # Check if values are boolean
                non_bool_mask = df[field_name].apply(lambda x: not (isinstance(x, (bool, np.bool_)) or pd.isna(x)))
                if non_bool_mask.any():
                    errors.append(f"Column '{field_name}' contains non-boolean values, but type is defined as 'bool'.")
                    valid = False

        # Check enum
        if field_type == 'enum':
            allowed_values = field.get('values', [])
            invalid_enum_mask = df[field_name].apply(lambda x: not (pd.isna(x) or validate_enum(x, allowed_values)))
            if invalid_enum_mask.any():
                invalid_vals = df.loc[invalid_enum_mask, field_name].unique()
                errors.append(f"Column '{field_name}' contains invalid enum values: {invalid_vals}. Allowed: {allowed_values}")
                valid = False

        # Check range
        if field_type in ['int', 'float']:
            constraints_dict = {k: v for k, v in field.items() if k in ['min', 'max']}
            if constraints_dict:
                # Apply range check row by row or via apply
                def check_range(val):
                    if pd.isna(val):
                        return True
                    try:
                        return validate_range(val, constraints_dict)
                    except:
                        return False

                out_of_range_mask = df[field_name].apply(lambda x: not check_range(x))
                if out_of_range_mask.any():
                    errors.append(f"Column '{field_name}' contains values outside the defined range.")
                    valid = False

    return {"valid": valid, "details": errors if not valid else ["All checks passed."]}

def validate_dataset(df: pd.DataFrame, schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Wrapper to validate a dataset against a schema.
    This is the primary entry point for validation tasks.

    Args:
        df: The DataFrame to validate.
        schema: The schema dictionary.

    Returns:
        Dictionary with 'valid' and 'details'.
    """
    return validate_dataframe_against_schema(df, schema)

def validate_result_against_analysis_schema(result: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate a result dictionary against the analysis output schema.
    """
    errors = []
    valid = True
    
    if 'entities' not in schema or not schema['entities']:
        return {"valid": False, "details": ["Analysis schema must define an entity."]}

    entity = schema['entities'][0]
    fields = entity.get('fields', [])

    for field in fields:
        field_name = field['name']
        if field_name not in result:
            errors.append(f"Missing required result field: {field_name}")
            valid = False
        else:
            # Basic type check for results
            expected_type = field['type']
            val = result[field_name]
            if expected_type == 'float' and not isinstance(val, (float, int)):
                errors.append(f"Field '{field_name}' should be float, got {type(val)}")
                valid = False
            elif expected_type == 'str' and not isinstance(val, str):
                errors.append(f"Field '{field_name}' should be str, got {type(val)}")
                valid = False
            elif expected_type == 'array' and not isinstance(val, list):
                errors.append(f"Field '{field_name}' should be array, got {type(val)}")
                valid = False

    return {"valid": valid, "details": errors if not valid else ["Result structure is valid."]}

def main():
    """Entry point for standalone validation script testing."""
    pass
