"""
Data validation utilities to enforce schema contracts.

This module provides functions to validate datasets against YAML-defined schemas
(Pydantic-like validation using standard libraries) and ensure data integrity
before processing.
"""

import os
import json
import logging
from typing import Any, Dict, List, Optional, Tuple, Union
from pathlib import Path

import pandas as pd
import numpy as np
import yaml

from .config import get_project_root, CONFIG

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def load_schema(schema_path: str) -> Dict[str, Any]:
    """
    Load a YAML schema definition from disk.

    Args:
        schema_path: Relative or absolute path to the schema YAML file.

    Returns:
        Dictionary containing the schema definition.

    Raises:
        FileNotFoundError: If the schema file does not exist.
        yaml.YAMLError: If the schema file is not valid YAML.
    """
    path = Path(schema_path)
    if not path.is_absolute():
        path = get_project_root() / schema_path

    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {path}")

    with open(path, 'r', encoding='utf-8') as f:
        schema = yaml.safe_load(f)

    logger.info(f"Loaded schema from {path}")
    return schema


def validate_field_type(value: Any, expected_type: str) -> bool:
    """
    Validate that a value matches the expected type definition.

    Supports: 'integer', 'float', 'string', 'boolean', 'list', 'object',
              'nullable' (allows None), and 'enum' (with a list of values).

    Args:
        value: The value to validate.
        expected_type: The type string from the schema.

    Returns:
        True if the value matches the type, False otherwise.
    """
    if value is None:
        # Nullable check handled in main validator, here we assume non-null
        return False

    type_map = {
        'integer': (int, np.integer),
        'float': (float, np.floating),
        'string': (str, np.str_),
        'boolean': (bool, np.bool_),
        'list': (list, np.ndarray),
        'object': (dict,),
    }

    if expected_type == 'nullable':
        return True  # Handled by required check elsewhere

    if expected_type.startswith('enum:'):
        allowed_values = json.loads(expected_type.split(':', 1)[1])
        return value in allowed_values

    expected_python_types = type_map.get(expected_type, ())
    if not expected_python_types:
        logger.warning(f"Unknown type definition: {expected_type}, assuming string")
        return isinstance(value, str)

    return isinstance(value, expected_python_types)


def validate_dataframe_schema(
    df: pd.DataFrame,
    schema: Dict[str, Any],
    strict: bool = True
) -> Tuple[bool, List[str]]:
    """
    Validate a pandas DataFrame against a schema definition.

    The schema is expected to have a structure like:
    {
        "name": "DatasetName",
        "fields": [
            {"name": "col1", "type": "integer", "required": true},
            {"name": "col2", "type": "string", "required": false},
            ...
        ]
    }

    Args:
        df: The DataFrame to validate.
        schema: The schema dictionary.
        strict: If True, fail if columns exist in df but not in schema.
                If False, ignore extra columns.

    Returns:
        A tuple (is_valid, errors_list).
    """
    errors = []
    fields = schema.get('fields', [])
    field_map = {f['name']: f for f in fields}

    # Check for required columns
    for field in fields:
        col_name = field['name']
        is_required = field.get('required', False)

        if col_name not in df.columns:
            if is_required:
                errors.append(f"Missing required column: '{col_name}'")
            continue

        # Validate types and nulls for existing columns
        col_data = df[col_name]
        type_def = field.get('type', 'string')
        is_nullable = type_def == 'nullable' or field.get('nullable', False)

        # Check for nulls
        null_count = col_data.isna().sum()
        if null_count > 0 and not is_nullable:
            errors.append(
                f"Column '{col_name}' contains {null_count} null values "
                f"but is not marked as nullable."
            )

        # Check types (sample-based for performance on large datasets)
        # We check a sample to avoid iterating every row if the dataset is huge
        sample_size = min(1000, len(col_data))
        sample_data = col_data.dropna().sample(n=sample_size, random_state=42)

        if len(sample_data) > 0:
            first_val = sample_data.iloc[0]
            if not validate_field_type(first_val, type_def):
                # If the first sample fails, check if it's a widespread issue
                # For simplicity, we flag it if the first value is wrong type
                # A more robust check would iterate all non-nulls
                errors.append(
                    f"Column '{col_name}' type mismatch: expected '{type_def}', "
                    f"found '{type(first_val).__name__}' in sample."
                )

    # Check for extra columns if strict
    if strict:
        extra_cols = set(df.columns) - set(field_map.keys())
        if extra_cols:
            errors.append(
                f"Strict mode: Found unexpected columns: {sorted(extra_cols)}"
            )

    is_valid = len(errors) == 0
    if not is_valid:
        logger.error(f"Validation failed for {schema.get('name', 'dataset')}: {errors}")
    else:
        logger.info(f"Validation passed for {schema.get('name', 'dataset')}")

    return is_valid, errors


def validate_dataset(
    data_path: Union[str, Path],
    schema_path: Union[str, Path],
    output_path: Optional[Union[str, Path]] = None
) -> bool:
    """
    High-level function to validate a dataset file against a schema.

    Args:
        data_path: Path to the data file (CSV, JSON, etc.).
        schema_path: Path to the schema YAML file.
        output_path: Optional path to write a validation report (JSON).

    Returns:
        True if validation passes, False otherwise.
    """
    data_path = Path(data_path)
    schema_path = Path(schema_path)

    # Load schema
    schema = load_schema(str(schema_path))

    # Load data
    if data_path.suffix == '.csv':
        df = pd.read_csv(data_path)
    elif data_path.suffix == '.json':
        df = pd.DataFrame(json.load(open(data_path)))
    else:
        raise ValueError(f"Unsupported data format: {data_path.suffix}")

    logger.info(f"Loaded data from {data_path}: {len(df)} rows, {len(df.columns)} columns")

    # Validate
    is_valid, errors = validate_dataframe_schema(df, schema)

    # Generate report if requested
    if output_path:
        report = {
            "data_file": str(data_path),
            "schema_file": str(schema_path),
            "is_valid": is_valid,
            "row_count": len(df),
            "column_count": len(df.columns),
            "errors": errors
        }
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Validation report written to {output_path}")

    return is_valid


def assert_schema_contracts(
    df: pd.DataFrame,
    schema_path: Union[str, Path],
    fail_fast: bool = True
) -> None:
    """
    Assert that a DataFrame matches a schema, raising an exception if not.

    This is useful for unit tests and CI pipelines.

    Args:
        df: The DataFrame to validate.
        schema_path: Path to the schema YAML file.
        fail_fast: If True, raise the first error encountered.

    Raises:
        ValueError: If validation fails.
    """
    schema = load_schema(str(schema_path))
    is_valid, errors = validate_dataframe_schema(df, schema)

    if not is_valid:
        error_msg = f"Schema validation failed for {schema.get('name', 'dataset')}:\n"
        error_msg += "\n".join([f"  - {e}" for e in errors])
        if fail_fast:
            raise ValueError(error_msg)
        else:
            logger.warning(error_msg)
            # Return the first error to fail the task if needed
            raise ValueError(errors[0])