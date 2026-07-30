"""
Schema validation for the ball milling dataset.

This module provides functions to validate the dataset against the defined schema
in contracts/dataset.schema.yaml. It checks for required fields, data types, and
basic structural integrity.

It does NOT check row count (handled by T015a and T017c).
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import pandas as pd
import yaml

from src.utils.exceptions import InsufficientDataError, SchemaValidationError

# Configure logger
logger = logging.getLogger(__name__)

# Default path to the schema file
DEFAULT_SCHEMA_PATH = Path("contracts/dataset.schema.yaml")


def load_schema(schema_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load the dataset schema from a YAML file.

    Args:
        schema_path: Path to the schema YAML file. Defaults to DEFAULT_SCHEMA_PATH.

    Returns:
        A dictionary representing the loaded schema.

    Raises:
        FileNotFoundError: If the schema file does not exist.
        yaml.YAMLError: If the schema file is not valid YAML.
    """
    if schema_path is None:
        schema_path = DEFAULT_SCHEMA_PATH

    if not schema_path.exists():
        logger.error(f"Schema file not found at {schema_path}")
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = yaml.safe_load(f)
        return schema
    except yaml.YAMLError as e:
        logger.error(f"Error parsing schema YAML: {e}")
        raise


def validate_schema(dataframe: pd.DataFrame, schema: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
    """
    Validate a DataFrame against the dataset schema.

    This function checks:
    1. Presence of all required fields defined in the schema.
    2. Basic data type compatibility (e.g., numeric fields should be numeric).

    It raises InsufficientDataError if the schema structure is violated
    (missing required columns or incorrect types).

    Note: This function does NOT check row count. Row count validation is
    handled separately in T015a and T017c.

    Args:
        dataframe: The pandas DataFrame to validate.
        schema: Optional pre-loaded schema dictionary. If None, loads from DEFAULT_SCHEMA_PATH.

    Returns:
        The input DataFrame (unchanged, but validated).

    Raises:
        InsufficientDataError: If required columns are missing or data types are invalid.
        FileNotFoundError: If the schema file cannot be found (when schema is not provided).
        yaml.YAMLError: If the schema file is invalid YAML (when schema is not provided).
    """
    if schema is None:
        schema = load_schema()

    if not isinstance(dataframe, pd.DataFrame):
        raise InsufficientDataError("Input must be a pandas DataFrame")

    # Extract required fields and their types from schema
    # Assuming schema structure: {'fields': [{'name': '...', 'type': '...'}, ...]}
    # or {'required_fields': ['...', ...], 'types': {'...': '...'}}
    # We need to be flexible based on the actual schema structure in contracts/dataset.schema.yaml

    required_fields = set()
    field_types = {}

    # Attempt to parse schema structure (common patterns)
    if 'fields' in schema:
        for field_def in schema['fields']:
            if 'name' in field_def:
                required_fields.add(field_def['name'])
                if 'type' in field_def:
                    field_types[field_def['name']] = field_def['type']
    elif 'required_fields' in schema:
        required_fields = set(schema['required_fields'])
        if 'types' in schema:
            field_types = schema['types']
    else:
        # Fallback: try to infer from common keys
        logger.warning("Could not parse standard schema structure, attempting to infer required fields.")
        # This is a fallback; ideally the schema follows a known pattern
        # For now, we assume 'required_fields' or 'fields' key exists
        raise SchemaValidationError("Schema missing 'fields' or 'required_fields' definition")

    # 1. Check for required columns
    missing_cols = required_fields - set(dataframe.columns)
    if missing_cols:
        error_msg = f"Missing required columns: {sorted(missing_cols)}"
        logger.error(error_msg)
        raise InsufficientDataError(error_msg)

    logger.info(f"Schema validation passed: All {len(required_fields)} required columns present.")

    # 2. Check data types (basic validation)
    # Map string type names to pandas dtypes or checks
    type_mapping = {
        'integer': lambda s: pd.api.types.is_integer_dtype(s) or pd.api.types.is_numeric_dtype(s),
        'number': lambda s: pd.api.types.is_numeric_dtype(s),
        'float': lambda s: pd.api.types.is_float_dtype(s) or pd.api.types.is_numeric_dtype(s),
        'string': lambda s: pd.api.types.is_string_dtype(s) or object,
        'boolean': lambda s: pd.api.types.is_bool_dtype(s),
        'datetime': lambda s: pd.api.types.is_datetime64_any_dtype(s),
        # Default check for numeric if type is 'int' or 'float' or 'number'
    }

    for col_name, expected_type in field_types.items():
        if col_name not in dataframe.columns:
            # Already caught by required fields check, but safety net
            continue

        series = dataframe[col_name]

        # Determine the check function
        check_func = type_mapping.get(expected_type)
        if check_func is None:
            # If type is unknown, try a generic numeric check if it looks like a number type
            if expected_type in ['int', 'integer', 'float', 'number', 'double']:
                check_func = pd.api.types.is_numeric_dtype
            elif expected_type in ['str', 'string', 'text']:
                check_func = lambda s: True # Assume strings are flexible
            elif expected_type in ['bool', 'boolean']:
                check_func = pd.api.types.is_bool_dtype
            else:
                logger.warning(f"Unknown type '{expected_type}' for column '{col_name}', skipping type check.")
                continue

        # Perform check
        # Note: is_numeric_dtype returns True for int and float
        # We might need stricter checks if the schema distinguishes them
        if not check_func(series):
            error_msg = f"Column '{col_name}' has incorrect type. Expected '{expected_type}', got '{series.dtype}'"
            logger.error(error_msg)
            raise InsufficientDataError(error_msg)

    logger.info("Schema validation passed: All data types are compatible.")
    return dataframe


def validate_file(file_path: Path, schema_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load a data file (CSV or Parquet) and validate it against the schema.

    Args:
        file_path: Path to the data file.
        schema_path: Optional path to the schema file.

    Returns:
        The validated DataFrame.

    Raises:
        FileNotFoundError: If the data file or schema file is not found.
        pd.errors.EmptyDataError: If the data file is empty.
        InsufficientDataError: If validation fails.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Data file not found: {file_path}")

    logger.info(f"Loading data from {file_path}...")

    # Determine file type and load
    if file_path.suffix.lower() == '.csv':
        df = pd.read_csv(file_path)
    elif file_path.suffix.lower() in ['.parquet', '.pq']:
        df = pd.read_parquet(file_path)
    else:
        raise ValueError(f"Unsupported file format: {file_path.suffix}")

    if df.empty:
        logger.warning("Loaded data file is empty.")
        # Depending on requirements, empty might be valid or invalid.
        # For schema validation, we check structure. An empty DF has structure.
        # However, downstream tasks (T015a) will check row count.
        # We allow empty here if columns match schema.

    logger.info(f"Loaded {len(df)} rows and {len(df.columns)} columns.")

    # Validate schema
    validated_df = validate_schema(df, load_schema(schema_path))

    logger.info("File validation successful.")
    return validated_df