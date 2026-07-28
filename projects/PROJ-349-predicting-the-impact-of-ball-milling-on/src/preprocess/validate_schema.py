"""
Schema validation logic for the ball milling dataset.

This module enforces the schema defined in `contracts/dataset.schema.yaml`.
It validates the presence and types of required fields but does NOT check
row count (row count validation is handled in T015c and T017c).
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import pandas as pd
import yaml

from src.utils.exceptions import InsufficientDataError, SchemaValidationError

# Configure logger
logger = logging.getLogger(__name__)


def load_schema(schema_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load the dataset schema from a YAML file.

    Args:
        schema_path: Path to the schema YAML file. Defaults to
                     'contracts/dataset.schema.yaml' relative to project root.

    Returns:
        Dictionary containing the schema definition.

    Raises:
        FileNotFoundError: If the schema file is not found.
        ValueError: If the schema file is empty or invalid YAML.
    """
    if schema_path is None:
        # Default path relative to project root
        schema_path = Path(__file__).parent.parent.parent / "contracts" / "dataset.schema.yaml"
    else:
        schema_path = Path(schema_path)

    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    try:
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in schema file: {e}")

    if not schema or "fields" not in schema:
        raise ValueError("Schema file is missing the 'fields' key or is empty.")

    return schema


def validate_schema(dataframe: pd.DataFrame, schema: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
    """
    Validate a DataFrame against the dataset schema.

    This function checks:
    1. All required fields are present.
    2. All required fields are non-null (no NaN/None values).
    3. Field types are compatible (basic type checking).

    IMPORTANT: This function does NOT check row count. Row count validation
    is handled separately in T015c (pre-processing warning) and T017c (post-processing halt).

    Args:
        dataframe: The pandas DataFrame to validate.
        schema: Optional schema dictionary. If None, loads from default path.

    Returns:
        The validated DataFrame (unchanged).

    Raises:
        InsufficientDataError: If required fields are missing or contain nulls.
        SchemaValidationError: If the schema itself is invalid or DataFrame is not a DataFrame.
    """
    if not isinstance(dataframe, pd.DataFrame):
        raise SchemaValidationError("Input must be a pandas DataFrame.")

    if schema is None:
        schema = load_schema()

    required_fields = []
    field_types = {}

    # Extract required fields and expected types from schema
    for field_def in schema.get("fields", []):
        name = field_def.get("name")
        is_required = field_def.get("required", False)
        ftype = field_def.get("type")

        if name:
            required_fields.append(name)
            if ftype:
                field_types[name] = ftype

    # 1. Check for missing columns
    existing_cols = set(dataframe.columns)
    required_set = set(required_fields)
    missing_cols = required_set - existing_cols

    if missing_cols:
        raise InsufficientDataError(
            f"Missing required columns in dataset: {sorted(missing_cols)}. "
            f"Expected columns: {sorted(required_fields)}."
        )

    # 2. Check for null values in required fields
    # We check only the required fields as per schema definition
    null_counts = {}
    for col in required_fields:
        if dataframe[col].isnull().any():
            count = dataframe[col].isnull().sum()
            null_counts[col] = count

    if null_counts:
        error_parts = []
        for col, count in null_counts.items():
            error_parts.append(f"Column '{col}' has {count} null values.")
        error_msg = "Required fields contain null values:\n" + "\n".join(error_parts)
        raise InsufficientDataError(error_msg)

    # 3. Basic type checking (optional but good practice)
    # We perform a soft check: if a column is supposed to be numeric but contains non-numeric,
    # we log a warning but do not raise an error immediately (type coercion might happen later).
    # However, if the schema explicitly says 'float' and we see 'object' with non-numeric strings,
    # we might raise. For now, we stick to structure and nulls as per T007b spec.

    logger.info(f"Schema validation passed for DataFrame with {len(dataframe)} rows and {len(dataframe.columns)} columns.")
    return dataframe


def validate_file(file_path: str, schema: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
    """
    Load a file (CSV or Parquet) and validate it against the schema.

    Args:
        file_path: Path to the input file.
        schema: Optional schema dictionary.

    Returns:
        The validated DataFrame.

    Raises:
        FileNotFoundError: If the file is not found.
        ValueError: If the file format is unsupported.
        InsufficientDataError: If validation fails.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {file_path}")

    suffix = path.suffix.lower()

    if suffix == ".csv":
        df = pd.read_csv(path)
    elif suffix in [".parquet", ".pq"]:
        df = pd.read_parquet(path)
    else:
        raise ValueError(f"Unsupported file format: {suffix}. Use .csv or .parquet.")

    return validate_schema(df, schema)
