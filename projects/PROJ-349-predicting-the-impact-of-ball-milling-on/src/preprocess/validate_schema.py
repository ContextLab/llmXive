"""
Schema validation for the ball milling dataset.
Validates dataframe against contracts/dataset.schema.yaml.
"""
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import pandas as pd
import yaml

from src.utils.exceptions import InsufficientDataError, SchemaValidationError

logger = logging.getLogger(__name__)

# Mapping of YAML schema types to pandas/numpy types
TYPE_MAPPING = {
    "string": object,
    "number": (int, float),
    "integer": int,
    "boolean": bool,
}

def load_schema(schema_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load the dataset schema from a YAML file.

    Args:
        schema_path: Path to the schema file. Defaults to contracts/dataset.schema.yaml.

    Returns:
        Dictionary containing the schema definition.

    Raises:
        FileNotFoundError: If the schema file does not exist.
        yaml.YAMLError: If the schema file is invalid YAML.
    """
    if schema_path is None:
        schema_path = Path(__file__).parent.parent.parent / "contracts" / "dataset.schema.yaml"
    else:
        schema_path = Path(schema_path)

    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    with open(schema_path, "r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)

    return schema

def _validate_column_types(df: pd.DataFrame, schema: Dict[str, Any]) -> List[str]:
    """
    Validate that columns match the expected types defined in the schema.

    Args:
        df: The dataframe to validate.
        schema: The schema definition.

    Returns:
        List of error messages for type mismatches.
    """
    errors = []
    properties = schema.get("properties", {})

    for col_name, col_schema in properties.items():
        if col_name in df.columns:
            expected_type = col_schema.get("type")
            if expected_type and expected_type in TYPE_MAPPING:
                expected_python_type = TYPE_MAPPING[expected_type]
                actual_dtype = df[col_name].dtype

                # Check if the column values are compatible with the expected type
                # For 'number', we accept int or float
                # For 'string', we accept object (string)
                # For 'integer', we accept int
                # For 'boolean', we accept bool

                if expected_type == "number":
                    # Check if dtype is numeric
                    if not pd.api.types.is_numeric_dtype(actual_dtype):
                        # Allow conversion if possible
                        try:
                            pd.to_numeric(df[col_name], errors="raise")
                        except (ValueError, TypeError):
                            errors.append(
                                f"Column '{col_name}' has dtype '{actual_dtype}' "
                                f"but expected type '{expected_type}' (numeric)."
                            )
                elif expected_type == "string":
                    # String columns should be object or string dtype
                    if not (pd.api.types.is_object_dtype(actual_dtype) or
                            pd.api.types.is_string_dtype(actual_dtype)):
                        errors.append(
                            f"Column '{col_name}' has dtype '{actual_dtype}' "
                            f"but expected type '{expected_type}' (string)."
                        )
                elif expected_type == "integer":
                    if not pd.api.types.is_integer_dtype(actual_dtype):
                        # Allow float if it represents integers (e.g., 1.0)
                        if pd.api.types.is_float_dtype(actual_dtype):
                            # Check if all values are integers
                            if not df[col_name].dropna().apply(lambda x: float(x).is_integer()).all():
                                errors.append(
                                    f"Column '{col_name}' has dtype '{actual_dtype}' "
                                    f"but expected type '{expected_type}' (integer)."
                                )
                        else:
                            errors.append(
                                f"Column '{col_name}' has dtype '{actual_dtype}' "
                                f"but expected type '{expected_type}' (integer)."
                            )
                elif expected_type == "boolean":
                    if not pd.api.types.is_bool_dtype(actual_dtype):
                        errors.append(
                            f"Column '{col_name}' has dtype '{actual_dtype}' "
                            f"but expected type '{expected_type}' (boolean)."
                        )

    return errors

def _validate_required_columns(df: pd.DataFrame, schema: Dict[str, Any]) -> List[str]:
    """
    Validate that all required columns are present.

    Args:
        df: The dataframe to validate.
        schema: The schema definition.

    Returns:
        List of error messages for missing required columns.
    """
    errors = []
    required_columns = schema.get("required", [])

    present_columns = set(df.columns)
    required_set = set(required_columns)

    missing_columns = required_set - present_columns

    for col in missing_columns:
        errors.append(f"Missing required column: '{col}'")

    return errors

def validate_schema(df: pd.DataFrame, schema_path: Optional[str] = None) -> None:
    """
    Validate a dataframe against the dataset schema.

    This function checks:
    1. Presence of all required columns.
    2. Type compatibility of columns with schema definitions.

    It raises InsufficientDataError if validation fails.

    Note: This function does NOT check row count. Row count validation is
    handled separately in T015a and T017c.

    Args:
        df: The dataframe to validate.
        schema_path: Optional path to the schema file. Defaults to contracts/dataset.schema.yaml.

    Raises:
        InsufficientDataError: If the dataframe fails schema validation.
        FileNotFoundError: If the schema file is not found.
        yaml.YAMLError: If the schema file is invalid YAML.
    """
    if not isinstance(df, pd.DataFrame):
        raise InsufficientDataError(
            "Input must be a pandas DataFrame, "
            f"got {type(df).__name__}"
        )

    schema = load_schema(schema_path)

    # Validate required columns
    column_errors = _validate_required_columns(df, schema)

    # Validate column types
    type_errors = _validate_column_types(df, schema)

    all_errors = column_errors + type_errors

    if all_errors:
        error_msg = "Schema validation failed:\n" + "\n".join(f"  - {err}" for err in all_errors)
        logger.error(error_msg)
        raise InsufficientDataError(error_msg)

    logger.info("Schema validation passed successfully.")

def validate_file(file_path: str, schema_path: Optional[str] = None) -> pd.DataFrame:
    """
    Load a file (CSV or Parquet) and validate it against the schema.

    Args:
        file_path: Path to the data file.
        schema_path: Optional path to the schema file.

    Returns:
        The validated dataframe.

    Raises:
        FileNotFoundError: If the data file or schema file is not found.
        InsufficientDataError: If the data fails schema validation.
        ValueError: If the file format is not supported.
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {file_path}")

    # Determine file format and load
    if path.suffix.lower() == ".csv":
        df = pd.read_csv(path)
    elif path.suffix.lower() in [".parquet", ".pq"]:
        df = pd.read_parquet(path)
    elif path.suffix.lower() == ".json":
        df = pd.read_json(path)
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}")

    # Validate against schema
    validate_schema(df, schema_path)

    return df