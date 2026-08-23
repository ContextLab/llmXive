"""
Schema validation utilities for the Chatbot Politeness project.
Validates datasets against contracts defined in YAML schema files.
"""
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import yaml

class SchemaValidationError(Exception):
    """Custom exception for schema validation errors."""
    pass

def load_schema(schema_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load a YAML schema definition from a file.

    Args:
        schema_path: Path to the YAML schema file.

    Returns:
        Dictionary containing the schema definition.

    Raises:
        FileNotFoundError: If the schema file does not exist.
        yaml.YAMLError: If the file is not valid YAML.
    """
    path = Path(schema_path)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def validate_type(value: Any, expected_type: str) -> bool:
    """
    Validate that a value matches the expected JSON schema type.

    Args:
        value: The value to check.
        expected_type: The expected type string (e.g., 'string', 'integer', 'number').

    Returns:
        True if the type matches, False otherwise.
    """
    if value is None:
        return True  # Null handling is often separate or depends on required flag

    type_map = {
        'string': str,
        'integer': int,
        'number': (int, float),
        'boolean': bool,
        'array': list,
        'object': dict,
        'null': type(None)
    }

    if expected_type not in type_map:
        return False

    expected_python_type = type_map[expected_type]
    
    # Special case: integer should not match float if strictly integer is required
    if expected_type == 'integer' and isinstance(value, bool):
        return False
    if expected_type == 'integer' and isinstance(value, float) and not value.is_integer():
        return False

    return isinstance(value, expected_python_type)

def validate_value_constraints(value: Any, constraints: Optional[Dict[str, Any]]) -> bool:
    """
    Validate value against constraints like min, max, or allowed_values.

    Args:
        value: The value to check.
        constraints: Dictionary of constraints.

    Returns:
        True if constraints are met, False otherwise.
    """
    if value is None:
        return True

    if 'min' in constraints:
        if value < constraints['min']:
            return False
    
    if 'max' in constraints:
        if value > constraints['max']:
            return False

    if 'allowed_values' in constraints:
        if value not in constraints['allowed_values']:
            return False

    return True

def validate_object(field_def: Dict[str, Any], value: Any) -> Tuple[bool, Optional[str]]:
    """
    Validate a single field value against its definition.

    Args:
        field_def: The field definition from the schema.
        value: The actual value from the dataset.

    Returns:
        Tuple of (is_valid, error_message).
    """
    required = field_def.get('required', False)
    
    if value is None:
        if required:
            return False, f"Field is required but is null"
        return True, None

    data_type = field_def.get('data_type')
    if data_type:
        if not validate_type(value, data_type):
            return False, f"Type mismatch: expected {data_type}, got {type(value).__name__}"

    constraints = field_def.get('constraints', {})
    if not validate_value_constraints(value, constraints):
        return False, f"Value constraints not met for value {value}"

    return True, None

def validate_dataset(df: Any, schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate a pandas DataFrame against a schema definition.

    Args:
        df: The pandas DataFrame to validate.
        schema: The loaded schema dictionary.

    Returns:
        Tuple of (is_valid, list_of_errors).
    """
    import pandas as pd
    
    errors = []
    fields_def = schema.get('properties', {}).get('fields', {}).get('properties', {})
    
    if not isinstance(df, pd.DataFrame):
        return False, ["Input must be a pandas DataFrame"]

    # Check for required fields first
    for field_name, field_def in fields_def.items():
        if field_def.get('required', False):
            if field_name not in df.columns:
                errors.append(f"Missing required field: {field_name}")

    # If critical fields are missing, stop here to avoid cascading errors
    if errors:
        return False, errors

    # Validate each row for each field
    # Note: For large datasets, this might be slow. Consider vectorized checks if possible.
    for field_name, field_def in fields_def.items():
        if field_name not in df.columns:
            continue  # Already handled in required check

        col = df[field_name]
        # Sample check or full check? Full check for correctness.
        # To optimize, we can check types first, then constraints.
        
        # Type check
        if field_def.get('data_type'):
            # Pandas might infer int as float64 if NaN exists. 
            # We'll do a loose check or convert if necessary.
            # For this implementation, we check the dtype kind or specific values.
            if field_def['data_type'] == 'string':
                if not pd.api.types.is_string_dtype(col) and not pd.api.types.is_object_dtype(col):
                    # Allow object if it contains strings
                    pass 
            elif field_def['data_type'] == 'integer':
                if not pd.api.types.is_integer_dtype(col):
                    # Check if it's float but contains integers
                    if pd.api.types.is_float_dtype(col):
                        if not col.isna().all() and not (col % 1 == 0).all():
                            errors.append(f"Column {field_name} contains non-integer values")
            elif field_def['data_type'] == 'number':
                if not pd.api.types.is_numeric_dtype(col):
                    errors.append(f"Column {field_name} is not numeric")

        # Constraint check (value by value for safety)
        constraints = field_def.get('constraints', {})
        if constraints:
            # Vectorized check for min/max
            if 'min' in constraints:
                if col.min() < constraints['min']:
                    errors.append(f"Column {field_name} has values below min {constraints['min']}")
            if 'max' in constraints:
                if col.max() > constraints['max']:
                    errors.append(f"Column {field_name} has values above max {constraints['max']}")
            
            if 'allowed_values' in constraints:
                unique_vals = col.unique()
                invalid = [v for v in unique_vals if pd.notna(v) and v not in constraints['allowed_values']]
                if invalid:
                    errors.append(f"Column {field_name} contains invalid values: {invalid[:5]}...")

    return len(errors) == 0, errors

def validate_dataset_schema(df: Any, schema_path: Union[str, Path]) -> Tuple[bool, List[str]]:
    """
    Convenience function to load schema and validate dataset.

    Args:
        df: The pandas DataFrame.
        schema_path: Path to the schema YAML file.

    Returns:
        Tuple of (is_valid, list_of_errors).
    """
    schema = load_schema(schema_path)
    return validate_dataset(df, schema)

def get_missing_fields(df: Any, schema_path: Union[str, Path]) -> List[str]:
    """
    Identify which required fields are missing from the DataFrame.

    Args:
        df: The pandas DataFrame.
        schema_path: Path to the schema YAML file.

    Returns:
        List of missing required field names.
    """
    import pandas as pd
    schema = load_schema(schema_path)
    fields_def = schema.get('properties', {}).get('fields', {}).get('properties', {})
    
    missing = []
    for field_name, field_def in fields_def.items():
        if field_def.get('required', False):
            if field_name not in df.columns:
                missing.append(field_name)
    
    return missing