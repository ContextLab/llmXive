"""
Schema validation module for the ball milling dataset.
Enforces structure and types defined in contracts/dataset.schema.yaml.
"""
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import pandas as pd
import yaml

from src.utils.exceptions import InsufficientDataError, SchemaValidationError

logger = logging.getLogger(__name__)

def load_schema(schema_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load the dataset schema from a YAML file.

    Args:
        schema_path: Path to the schema file. Defaults to 'contracts/dataset.schema.yaml' relative to project root.

    Returns:
        Dictionary containing the schema definition.

    Raises:
        FileNotFoundError: If the schema file is not found.
        yaml.YAMLError: If the schema file is invalid YAML.
    """
    if schema_path is None:
        # Determine project root relative to this file
        current_file = Path(__file__).resolve()
        project_root = current_file.parent.parent.parent
        schema_path = project_root / "contracts" / "dataset.schema.yaml"
    else:
        schema_path = Path(schema_path)

    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found at {schema_path}")

    with open(schema_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def validate_schema(df: pd.DataFrame, schema: Optional[Dict[str, Any]] = None) -> bool:
    """
    Validate a DataFrame against the dataset schema.

    This function checks:
    1. Presence of all required fields.
    2. Type compatibility for each field (string, number, or null).

    It does NOT check row count (handled by T015a and T017c).

    Args:
        df: The DataFrame to validate.
        schema: Optional pre-loaded schema. If None, loads from default path.

    Returns:
        True if validation passes.

    Raises:
        InsufficientDataError: If required fields are missing or data types are invalid.
        SchemaValidationError: If the schema itself is malformed.
    """
    if schema is None:
        schema = load_schema()

    required_fields = schema.get("required", [])
    properties = schema.get("properties", {})

    # 1. Check for presence of required columns
    missing_columns = set(required_fields) - set(df.columns)
    if missing_columns:
        msg = f"Schema validation failed: Missing required columns: {sorted(missing_columns)}"
        logger.error(msg)
        raise InsufficientDataError(msg)

    # 2. Check data types for each column
    type_errors = []
    for col_name in required_fields:
        col_schema = properties.get(col_name, {})
        allowed_types = col_schema.get("type", [])

        # Normalize allowed_types to a list if it's a single string
        if isinstance(allowed_types, str):
            allowed_types = [allowed_types]

        # Determine pandas dtype compatibility
        # JSON schema 'number' maps to float/int, 'string' to object/str
        # We allow 'null' in JSON schema, which in pandas is represented by NaN or None in object columns
        # or float columns.

        series = df[col_name]

        # If the column is entirely empty or non-existent (already checked), skip
        if series.empty:
            continue

        # Check for type mismatches
        # We perform a lenient check: if the column is numeric (int/float), it satisfies 'number'
        # If it's object, it might contain strings or nulls.
        # We raise an error only if we can definitively say the type is wrong (e.g., bool in a number column)
        # or if the schema explicitly forbids the inferred type.

        is_numeric = pd.api.types.is_numeric_dtype(series)
        is_string_like = pd.api.types.is_string_dtype(series) or series.apply(lambda x: isinstance(x, str) or pd.isna(x)).all()

        valid_for_col = False

        if "number" in allowed_types:
            if is_numeric:
                valid_for_col = True
            # Allow object columns if they only contain numbers or NaN
            elif not is_numeric and series.dtype == object:
                # Check if all non-null values are numbers
                non_null = series.dropna()
                if len(non_null) > 0 and non_null.apply(lambda x: isinstance(x, (int, float)) and not isinstance(x, bool)).all():
                    valid_for_col = True

        if "string" in allowed_types:
            if is_string_like:
                valid_for_col = True

        # If 'null' is allowed, we don't need to check for NaN specifically as it's always allowed in pandas
        # unless the column is strictly typed as non-nullable in a stricter validator,
        # but here we just check the type of non-null values.

        if not valid_for_col:
            type_errors.append(f"Column '{col_name}' has invalid type. Expected: {allowed_types}, Found: {series.dtype}")

    if type_errors:
        msg = f"Schema validation failed: Type mismatches found.\n" + "\n".join(type_errors)
        logger.error(msg)
        raise InsufficientDataError(msg)

    logger.info("Schema validation passed.")
    return True

def validate_file(file_path: str, schema: Optional[Dict[str, Any]] = None) -> bool:
    """
    Validate a Parquet or CSV file against the schema.

    Args:
        file_path: Path to the data file.
        schema: Optional pre-loaded schema.

    Returns:
        True if validation passes.

    Raises:
        FileNotFoundError: If the data file is not found.
        ValueError: If the file format is unsupported.
        InsufficientDataError: If validation fails.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Data file not found at {file_path}")

    if path.suffix == ".parquet":
        df = pd.read_parquet(path)
    elif path.suffix == ".csv":
        df = pd.read_csv(path)
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}. Use .parquet or .csv.")

    return validate_schema(df, schema)