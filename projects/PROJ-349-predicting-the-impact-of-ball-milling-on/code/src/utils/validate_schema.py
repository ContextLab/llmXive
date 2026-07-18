"""
Schema validation utilities for the ball milling dataset.

This module enforces the dataset schema defined in `contracts/dataset.schema.yaml`
and validates incoming DataFrames for structural integrity and minimum row counts.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import pandas as pd
import yaml

from src.exceptions import InsufficientDataError, SchemaValidationError

logger = logging.getLogger(__name__)

# Path to the schema definition file relative to project root
SCHEMA_PATH = Path("contracts/dataset.schema.yaml")

def load_schema(schema_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load the dataset schema from a YAML file.

    Args:
        schema_path: Optional path to the schema file. Defaults to SCHEMA_PATH.

    Returns:
        Dictionary containing the schema definition.

    Raises:
        FileNotFoundError: If the schema file cannot be found.
        yaml.YAMLError: If the schema file is not valid YAML.
    """
    if schema_path is None:
        schema_path = SCHEMA_PATH

    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found at {schema_path}")

    with open(schema_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def _get_required_fields(schema: Dict[str, Any]) -> Set[str]:
    """
    Extract the set of required field names from the schema.

    Args:
        schema: The loaded schema dictionary.

    Returns:
        Set of required field names.
    """
    properties = schema.get("properties", {})
    required_fields = set(schema.get("required", []))

    # Ensure all fields marked as required in the schema are captured
    # Some schemas might define required fields implicitly or via type definitions
    # We rely on the explicit 'required' list from the schema root or properties
    return required_fields

def _validate_column_types(df: pd.DataFrame, schema: Dict[str, Any]) -> List[str]:
    """
    Validate that DataFrame columns match the expected types defined in the schema.

    Args:
        df: The DataFrame to validate.
        schema: The loaded schema dictionary.

    Returns:
        List of type mismatch error messages.
    """
    errors = []
    properties = schema.get("properties", {})

    for col_name, col_schema in properties.items():
        if col_name in df.columns:
            expected_type = col_schema.get("type")
            actual_dtype = df[col_name].dtype

            # Simple type mapping for validation
            type_mapping = {
                "string": ["object", "string"],
                "integer": ["int64", "int32", "int16", "int8", "uint64", "uint32", "uint16", "uint8"],
                "number": ["float64", "float32", "float16"],
                "boolean": ["bool"],
            }

            if expected_type:
                allowed_dtypes = type_mapping.get(expected_type, [])
                if str(actual_dtype) not in allowed_dtypes and expected_type != "number":
                    # Allow number to match integers too
                    if expected_type == "number" and "int" in str(actual_dtype):
                        continue
                    if expected_type == "number" and "float" in str(actual_dtype):
                        continue
                    errors.append(
                        f"Column '{col_name}' has dtype '{actual_dtype}', "
                        f"expected '{expected_type}'"
                    )

    return errors

def _validate_nulls(df: pd.DataFrame, schema: Dict[str, Any]) -> List[str]:
    """
    Validate that required columns do not contain null values.

    Args:
        df: The DataFrame to validate.
        schema: The loaded schema dictionary.

    Returns:
        List of null violation error messages.
    """
    errors = []
    required_fields = _get_required_fields(schema)

    for field in required_fields:
        if field in df.columns:
            null_count = df[field].isna().sum()
            if null_count > 0:
                errors.append(
                    f"Column '{field}' contains {null_count} null values "
                    f"(required fields cannot be null)"
                )
        else:
            errors.append(f"Required column '{field}' is missing from DataFrame")

    return errors

def validate_schema(df: pd.DataFrame, schema_path: Optional[Path] = None) -> bool:
    """
    Validate a DataFrame against the dataset schema.

    This function performs the following checks:
    1. Minimum row count (>= 150)
    2. Presence of all required columns
    3. Null value checks for required columns
    4. Basic type compatibility

    Args:
        df: The pandas DataFrame to validate.
        schema_path: Optional path to the schema file.

    Returns:
        True if validation passes.

    Raises:
        InsufficientDataError: If the DataFrame has fewer than 150 rows.
        SchemaValidationError: If the DataFrame fails schema validation.
    """
    if not isinstance(df, pd.DataFrame):
        raise SchemaValidationError("Input must be a pandas DataFrame")

    # Load schema
    try:
        schema = load_schema(schema_path)
    except FileNotFoundError as e:
        raise SchemaValidationError(f"Failed to load schema: {e}")

    # Check minimum row count (Task T007b requirement)
    row_count = len(df)
    if row_count < 150:
        raise InsufficientDataError(
            f"Dataset has insufficient data: {row_count} rows. "
            f"Minimum required: 150 rows. "
            f"Please ingest more data sources or verify data pipeline."
        )

    logger.info(f"Validating schema for dataset with {row_count} rows...")

    validation_errors: List[str] = []

    # Check for required columns and nulls
    validation_errors.extend(_validate_nulls(df, schema))

    # Check column types
    validation_errors.extend(_validate_column_types(df, schema))

    if validation_errors:
        error_msg = "Schema validation failed with the following errors:\n"
        error_msg += "\n".join([f"  - {err}" for err in validation_errors])
        raise SchemaValidationError(error_msg)

    logger.info("Schema validation passed successfully.")
    return True

def validate_file(file_path: Path, schema_path: Optional[Path] = None) -> bool:
    """
    Validate a Parquet or CSV file against the schema.

    Args:
        file_path: Path to the file to validate.
        schema_path: Optional path to the schema file.

    Returns:
        True if validation passes.

    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the file format is unsupported.
        InsufficientDataError: If the file has fewer than 150 rows.
        SchemaValidationError: If the file data fails schema validation.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Input file not found: {file_path}")

    file_ext = file_path.suffix.lower()

    if file_ext == ".parquet":
        df = pd.read_parquet(file_path)
    elif file_ext == ".csv":
        df = pd.read_csv(file_path)
    else:
        raise ValueError(f"Unsupported file format: {file_ext}. Use .parquet or .csv")

    return validate_schema(df, schema_path)
