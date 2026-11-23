"""
Schema validation helpers for contract testing.
Provides functions to validate dataframes, JSON structures, and file schemas.
"""
import pandas as pd
import json
from typing import Dict, List, Any, Optional, Set
from pathlib import Path


def validate_dataframe_schema(
    df: pd.DataFrame,
    required_columns: List[str],
    optional_columns: Optional[List[str]] = None,
    column_types: Optional[Dict[str, str]] = None,
    min_rows: int = 0
) -> Dict[str, Any]:
    """
    Validate a DataFrame against a schema definition.

    Args:
        df: The DataFrame to validate.
        required_columns: List of column names that must be present.
        optional_columns: List of optional column names.
        column_types: Dict mapping column names to expected types (as strings).
        min_rows: Minimum number of rows required.

    Returns:
        Dict with 'valid' (bool), 'errors' (list), and 'warnings' (list).
    """
    errors = []
    warnings = []

    # Check row count
    if len(df) < min_rows:
        errors.append(f"DataFrame has {len(df)} rows, minimum required is {min_rows}")

    # Check required columns
    existing_columns = set(df.columns)
    missing_required = set(required_columns) - existing_columns
    if missing_required:
        errors.append(f"Missing required columns: {sorted(missing_required)}")

    # Check for unexpected columns if optional_columns is provided
    if optional_columns is not None:
        allowed_columns = set(required_columns) | set(optional_columns)
        unexpected = existing_columns - allowed_columns
        if unexpected:
            warnings.append(f"Unexpected columns found: {sorted(unexpected)}")

    # Check column types
    if column_types:
        for col, expected_type in column_types.items():
            if col in existing_columns:
                actual_type = str(df[col].dtype)
                if expected_type not in actual_type:
                    errors.append(f"Column '{col}' has type {actual_type}, expected {expected_type}")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "row_count": len(df),
        "column_count": len(df.columns)
    }


def validate_json_schema(
    data: Dict[str, Any],
    required_keys: List[str],
    optional_keys: Optional[List[str]] = None,
    type_constraints: Optional[Dict[str, type]] = None
) -> Dict[str, Any]:
    """
    Validate a JSON/Dict structure against a schema.

    Args:
        data: The dictionary to validate.
        required_keys: List of keys that must be present.
        optional_keys: List of optional keys.
        type_constraints: Dict mapping keys to expected Python types.

    Returns:
        Dict with 'valid' (bool), 'errors' (list), and 'warnings' (list).
    """
    errors = []
    warnings = []

    # Check required keys
    existing_keys = set(data.keys())
    missing_required = set(required_keys) - existing_keys
    if missing_required:
        errors.append(f"Missing required keys: {sorted(missing_required)}")

    # Check for unexpected keys
    if optional_keys is not None:
        allowed_keys = set(required_keys) | set(optional_keys)
        unexpected = existing_keys - allowed_keys
        if unexpected:
            warnings.append(f"Unexpected keys found: {sorted(unexpected)}")

    # Check types
    if type_constraints:
        for key, expected_type in type_constraints.items():
            if key in existing_keys:
                actual_type = type(data[key])
                if not isinstance(data[key], expected_type):
                    errors.append(f"Key '{key}' has type {actual_type.__name__}, expected {expected_type.__name__}")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "key_count": len(data)
    }


def validate_file_exists(path: str, description: str) -> bool:
    """
    Validate that a file exists at the given path.

    Args:
        path: Path to the file.
        description: Human-readable description for error messages.

    Returns:
        True if file exists, False otherwise.
    """
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Contract validation failed: {description} not found at {path}")
    return True


def validate_json_file(path: str, schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Load and validate a JSON file against a schema.

    Args:
        path: Path to the JSON file.
        schema: Schema definition (same format as validate_json_schema).

    Returns:
        Validation result dict.
    """
    validate_file_exists(path, "JSON file")

    with open(path, 'r') as f:
        data = json.load(f)

    return validate_json_schema(
        data,
        required_keys=schema.get("required_keys", []),
        optional_keys=schema.get("optional_keys"),
        type_constraints=schema.get("type_constraints")
    )


def validate_csv_file(
    path: str,
    schema: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Load and validate a CSV file against a schema.

    Args:
        path: Path to the CSV file.
        schema: Schema definition with 'required_columns', 'optional_columns',
               'column_types', and 'min_rows'.

    Returns:
        Validation result dict.
    """
    validate_file_exists(path, "CSV file")

    df = pd.read_csv(path)

    return validate_dataframe_schema(
        df,
        required_columns=schema.get("required_columns", []),
        optional_columns=schema.get("optional_columns"),
        column_types=schema.get("column_types"),
        min_rows=schema.get("min_rows", 0)
    )
