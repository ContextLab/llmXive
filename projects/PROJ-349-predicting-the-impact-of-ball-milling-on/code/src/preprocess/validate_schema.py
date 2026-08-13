"""
Schema validation module for the ball milling dataset.

This module enforces the dataset schema defined in `contracts/dataset.schema.yaml`.
It validates field presence, types, and structure but does NOT check row count
(handled by T015a and T017c).
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import pandas as pd
import yaml

# Import exceptions from the established location in the API surface
from src.utils.exceptions import InsufficientDataError, SchemaValidationError

# Configure logger
logger = logging.getLogger(__name__)

# Default path to the schema file relative to project root
# Note: The project structure places contracts at the root or under src/
# Based on tasks.md: "contracts/dataset.schema.yaml"
DEFAULT_SCHEMA_PATH = "contracts/dataset.schema.yaml"


def load_schema(schema_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load the dataset schema from a YAML file.

    Args:
        schema_path: Path to the schema YAML file. Defaults to DEFAULT_SCHEMA_PATH.

    Returns:
        Dict containing the loaded schema.

    Raises:
        SchemaValidationError: If the schema file cannot be found or parsed.
    """
    path = Path(schema_path) if schema_path else Path(DEFAULT_SCHEMA_PATH)

    if not path.exists():
        # Try resolving relative to project root if absolute path not provided
        # Assuming the script runs from project root or the path is relative to it
        if not path.is_absolute():
            # Check common locations
            possible_paths = [
                Path.cwd() / "contracts" / "dataset.schema.yaml",
                Path.cwd() / "code" / "contracts" / "dataset.schema.yaml",
                path
            ]
            found = False
            for p in possible_paths:
                if p.exists():
                    path = p
                    found = True
                    break
            if not found:
                raise SchemaValidationError(f"Schema file not found at: {schema_path or DEFAULT_SCHEMA_PATH}")
        else:
            raise SchemaValidationError(f"Schema file not found at: {path}")

    try:
        with open(path, 'r', encoding='utf-8') as f:
            schema = yaml.safe_load(f)
        if not isinstance(schema, dict):
            raise SchemaValidationError("Schema file must contain a valid YAML dictionary.")
        return schema
    except yaml.YAMLError as e:
        raise SchemaValidationError(f"Failed to parse schema YAML: {e}")
    except Exception as e:
        raise SchemaValidationError(f"Error loading schema file: {e}")


def _validate_field_types(df: pd.DataFrame, schema: Dict[str, Any]) -> List[str]:
    """
    Validates that columns exist and have compatible types based on the schema.

    Args:
        df: The dataframe to validate.
        schema: The loaded schema dictionary.

    Returns:
        A list of error messages. Empty if validation passes.
    """
    errors = []
    properties = schema.get("properties", {})
    required_fields = schema.get("required", [])

    # Check for required fields
    missing_fields = set(required_fields) - set(df.columns)
    if missing_fields:
        errors.append(f"Missing required fields: {', '.join(sorted(missing_fields))}")

    # Check types for present fields
    for col_name, col_schema in properties.items():
        if col_name not in df.columns:
            continue  # Already handled by required check if applicable

        expected_type = col_schema.get("type")
        if not expected_type:
            continue  # No type constraint specified

        dtype = df[col_name].dtype

        # Map YAML/JSON types to pandas dtypes
        type_map = {
            "string": ["object", "string"],
            "integer": ["int64", "int32", "uint64", "uint32"],
            "number": ["float64", "float32"],
            "boolean": ["bool"]
        }

        valid_dtypes = type_map.get(expected_type, [])

        # Special handling for numeric columns that might be object (mixed) or nullable
        if expected_type in ["integer", "number"]:
            # Allow numeric types, or object if it contains numeric-like strings (though strict check prefers numeric)
            # For strict schema validation, we expect numeric dtypes for numbers
            if not pd.api.types.is_numeric_dtype(dtype):
                # Allow object if it's actually numeric (e.g. read as object but convertible)
                # But strict schema usually implies the data type in the file
                # Let's be strict: if it says number, it should be numeric
                errors.append(f"Field '{col_name}' expected type '{expected_type}' but found dtype '{dtype}'")

        elif expected_type == "string":
            # Object is the standard string type in pandas
            if dtype not in valid_dtypes:
                errors.append(f"Field '{col_name}' expected type '{expected_type}' but found dtype '{dtype}'")

        elif expected_type == "boolean":
            if dtype not in valid_dtypes:
                errors.append(f"Field '{col_name}' expected type '{expected_type}' but found dtype '{dtype}'")

    return errors


def validate_schema(df: pd.DataFrame, schema_path: Optional[str] = None) -> bool:
    """
    Validates a dataframe against the dataset schema.

    This function enforces field presence and type constraints as defined in
    `contracts/dataset.schema.yaml`. It raises `InsufficientDataError` if
    the schema structure (field types, presence) fails.

    Constraint: This function does NOT check row count.

    Args:
        df: The pandas DataFrame to validate.
        schema_path: Optional path to the schema file.

    Raises:
        InsufficientDataError: If the dataframe fails schema validation (missing fields, wrong types).
        SchemaValidationError: If the schema file itself is invalid.

    Returns:
        True if validation passes.
    """
    if not isinstance(df, pd.DataFrame):
        raise InsufficientDataError("Input must be a pandas DataFrame.")

    if df.empty:
        # Empty dataframe fails schema if required fields are expected
        # Though strictly, an empty dataframe has the right columns.
        # The spec says "enforce schema structure". If columns are missing, it fails.
        # If columns exist but rows are 0, that's a row count issue (T015a/T017c).
        # We proceed to check column presence.
        pass

    try:
        schema = load_schema(schema_path)
    except SchemaValidationError:
        # Re-raise if schema loading fails
        raise

    errors = []

    # 1. Check required fields
    required_fields = schema.get("required", [])
    missing_fields = set(required_fields) - set(df.columns)
    if missing_fields:
        errors.append(f"Missing required fields: {', '.join(sorted(missing_fields))}")

    # 2. Check types
    type_errors = _validate_field_types(df, schema)
    errors.extend(type_errors)

    if errors:
        error_msg = "Schema validation failed:\n- " + "\n- ".join(errors)
        # The task specifically requires raising InsufficientDataError for schema failure
        # per the task description: "raises InsufficientDataError ... ONLY if schema structure ... fails"
        raise InsufficientDataError(error_msg)

    logger.info("Schema validation passed.")
    return True


def validate_file(file_path: str, schema_path: Optional[str] = None) -> bool:
    """
    Validates a parquet or CSV file against the dataset schema.

    Args:
        file_path: Path to the input file (parquet or csv).
        schema_path: Optional path to the schema file.

    Raises:
        InsufficientDataError: If the file data fails schema validation.
        FileNotFoundError: If the input file does not exist.
        ValueError: If the file format is unsupported.

    Returns:
        True if validation passes.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {file_path}")

    suffix = path.suffix.lower()
    try:
        if suffix == '.parquet':
            df = pd.read_parquet(path)
        elif suffix == '.csv':
            df = pd.read_csv(path)
        else:
            raise ValueError(f"Unsupported file format: {suffix}. Use .parquet or .csv.")
    except Exception as e:
        raise SchemaValidationError(f"Failed to read input file: {e}")

    return validate_schema(df, schema_path)