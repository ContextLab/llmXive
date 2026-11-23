"""
Validation utilities and custom exceptions for the project.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml
import pandas as pd
from pydantic import BaseModel, ValidationError


class DataFetchError(Exception):
    """Exception raised for errors during data fetching."""
    pass


class NoRealDataFoundError(Exception):
    """Exception raised when no real data is found."""
    pass


class VerifiedDataSourceError(Exception):
    """Exception raised when a verified data source is invalid or missing."""
    pass


def load_schema(schema_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load a JSON or YAML schema from a file.

    Args:
        schema_path: Path to the schema file.

    Returns:
        The schema as a dictionary.
    """
    path = Path(schema_path)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {path}")

    with open(path, 'r') as f:
        if path.suffix in ['.yaml', '.yml']:
            return yaml.safe_load(f)
        elif path.suffix == '.json':
            return json.load(f)
        else:
            raise ValueError(f"Unsupported schema format: {path.suffix}")


def validate_dataframe_schema(df: pd.DataFrame, schema: Dict[str, Any]) -> bool:
    """
    Validate a DataFrame against a JSON Schema-like dictionary.

    Args:
        df: The DataFrame to validate.
        schema: The schema dictionary.

    Returns:
        True if valid, raises ValueError otherwise.
    """
    required_fields = schema.get('required', [])
    properties = schema.get('properties', {})

    # Check required columns
    missing_cols = [col for col in required_fields if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    # Check types (basic check)
    for col, props in properties.items():
        if col in df.columns:
            expected_type = props.get('type')
            if expected_type == 'integer':
                if not pd.api.types.is_integer_dtype(df[col]):
                    # Allow float that are whole numbers
                    if not pd.api.types.is_float_dtype(df[col]):
                        raise ValueError(f"Column {col} should be integer")
            elif expected_type == 'number':
                if not pd.api.types.is_numeric_dtype(df[col]):
                    raise ValueError(f"Column {col} should be numeric")
            elif expected_type == 'string':
                if not pd.api.types.is_string_dtype(df[col]):
                    raise ValueError(f"Column {col} should be string")

    return True


def validate_json_against_schema(data: Any, schema: Dict[str, Any]) -> bool:
    """
    Validate a JSON object against a schema.

    Args:
        data: The data to validate.
        schema: The schema dictionary.

    Returns:
        True if valid, raises ValueError otherwise.
    """
    # Basic validation for required keys
    required = schema.get('required', [])
    if isinstance(data, dict):
        missing_keys = [k for k in required if k not in data]
        if missing_keys:
            raise ValueError(f"Missing required keys in JSON: {missing_keys}")
    return True


def validate_dataset(df: pd.DataFrame, schema_path: Union[str, Path]) -> bool:
    """
    Validate a dataset against a schema file.

    Args:
        df: The DataFrame to validate.
        schema_path: Path to the schema file.

    Returns:
        True if valid.
    """
    schema = load_schema(schema_path)
    return validate_dataframe_schema(df, schema)


def validate_output(data: Any, schema_path: Union[str, Path]) -> bool:
    """
    Validate output data against a schema file.

    Args:
        data: The data to validate.
        schema_path: Path to the schema file.

    Returns:
        True if valid.
    """
    schema = load_schema(schema_path)
    return validate_json_against_schema(data, schema)


def assert_valid(condition: bool, message: str):
    """
    Assert a condition and raise ValueError if false.

    Args:
        condition: The condition to check.
        message: Error message if condition is false.
    """
    if not condition:
        raise ValueError(message)


def validate_pydantic_model(model: BaseModel, data: Dict[str, Any]) -> bool:
    """
    Validate data against a Pydantic model.

    Args:
        model: The Pydantic model class.
        data: The data dictionary.

    Returns:
        True if valid.
    """
    try:
        model(**data)
        return True
    except ValidationError as e:
        raise ValueError(f"Pydantic validation failed: {e}")


def validate_pydantic_list(model: BaseModel, data_list: List[Dict[str, Any]]) -> bool:
    """
    Validate a list of data dictionaries against a Pydantic model.

    Args:
        model: The Pydantic model class.
        data_list: The list of data dictionaries.

    Returns:
        True if valid.
    """
    for data in data_list:
        validate_pydantic_model(model, data)
    return True
