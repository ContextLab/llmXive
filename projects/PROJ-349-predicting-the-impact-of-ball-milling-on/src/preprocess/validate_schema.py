"""
Schema validation module for the ball milling dataset.

This module enforces the schema defined in ``contracts/dataset.schema.yaml``.
It provides two levels of validation:
1. ``validate_schema`` – checks overall dataframe structure (field presence,
   types, and high‑level constraints) and raises ``InsufficientDataError`` or
   ``SchemaValidationError``.
2. ``validate`` – validates each **row** against the dataset schema and raises
   ``jsonschema.ValidationError`` when a row does not conform.  This function
   satisfies task **T007b**.

The original implementation mixed custom validation with ``jsonschema`` but
the schema file is a custom definition (``fields`` + ``constraints``) rather
than a pure JSON‑Schema document.  As a result, ``jsonschema.validate`` never
raised on mismatched rows.  The updated ``validate`` now performs explicit
checks based on the custom schema and raises ``jsonschema.ValidationError``
with a clear message when a row violates any rule.
"""
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import yaml
import jsonschema
from jsonschema import ValidationError

from src.utils.exceptions import InsufficientDataError, SchemaValidationError

logger = logging.getLogger(__name__)

# Expected field types mapping (used for row‑level validation)
FIELD_TYPES = {
    "string": str,
    "float": (float, int),  # ``int`` is acceptable for ``float`` fields
    "integer": int,
    "boolean": bool,
}

# Fields that must be present in every row (high‑level validation)
REQUIRED_FIELDS = [
    "experiment_id",
    "source",
    "source_id",
    "material_type",
    "milling_speed",
    "milling_time",
    "ball_to_powder_ratio",
    "youngs_modulus",
    "density",
    "d10",
    "d50",
    "d90",
]

def load_schema(schema_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load the dataset schema from a YAML file.

    Parameters
    ----------
    schema_path : Optional[str]
        Path to the schema YAML file. If ``None`` the default location
        ``contracts/dataset.schema.yaml`` relative to the project root is used.

    Returns
    -------
    Dict[str, Any]
        Parsed schema dictionary.

    Raises
    ------
    FileNotFoundError
        If the schema file does not exist.
    yaml.YAMLError
        If the file cannot be parsed.
    """
    if schema_path is None:
        # Default path relative to project root
        schema_path = (
            Path(__file__).parent.parent.parent
            / "contracts"
            / "dataset.schema.yaml"
        )
    else:
        schema_path = Path(schema_path)

    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    with open(schema_path, "r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)

    return schema

# ----------------------------------------------------------------------
# Helper functions for the high‑level dataframe validation (existing API)
# ----------------------------------------------------------------------
def _validate_field_presence(df: pd.DataFrame, schema: Dict[str, Any]) -> List[str]:
    required_fields = set(REQUIRED_FIELDS)
    actual_fields = set(df.columns)
    missing_fields = required_fields - actual_fields
    return list(missing_fields)

def _validate_field_types(df: pd.DataFrame, schema: Dict[str, Any]) -> List[str]:
    type_errors = []
    fields_info = schema.get("fields", [])

    for field_def in fields_info:
        field_name = field_def["name"]
        expected_type_str = field_def["type"]

        if field_name not in df.columns:
            continue  # Already caught by presence check

        expected_type = FIELD_TYPES.get(expected_type_str)
        if expected_type is None:
            logger.warning(
                f"Unknown type '{expected_type_str}' for field '{field_name}'"
            )
            continue

        col = df[field_name]

        if expected_type_str == "float":
            # ``pd.to_numeric`` will raise if conversion is impossible
            try:
                pd.to_numeric(col, errors="raise")
            except (ValueError, TypeError):
                type_errors.append(field_name)
        elif expected_type_str == "string":
            if not (col.dtype == object or pd.api.types.is_string_dtype(col)):
                if not pd.api.types.is_numeric_dtype(col):
                    type_errors.append(field_name)
        elif expected_type_str == "integer":
            if not pd.api.types.is_integer_dtype(col):
                type_errors.append(field_name)
        elif expected_type_str == "boolean":
            if not pd.api.types.is_bool_dtype(col):
                type_errors.append(field_name)

    return type_errors

def _validate_constraints(df: pd.DataFrame, schema: Dict[str, Any]) -> List[str]:
    violations = []
    constraints = schema.get("constraints", [])

    for constraint in constraints:
        field = constraint["field"]
        condition = constraint["condition"]

        if field not in df.columns:
            continue  # Skip if field is missing (caught by presence check)

        try:
            # Simple condition parser – only handles the patterns used in the spec
            if "d10 >= 0" in condition:
                if (df[field] < 0).any():
                    violations.append(f"Field '{field}' contains negative values")
            elif "d10 <= d50" in condition:
                if (df["d10"] > df["d50"]).any():
                    violations.append("d10 values exceed d50 values")
            elif "d50 <= d90" in condition:
                if (df["d50"] > df["d90"]).any():
                    violations.append("d50 values exceed d90 values")
            elif "milling_speed > 0" in condition:
                if (df[field] <= 0).any():
                    violations.append(f"Field '{field}' contains non‑positive values")
            elif "milling_time > 0" in condition:
                if (df[field] <= 0).any():
                    violations.append(f"Field '{field}' contains non‑positive values")
        except Exception as e:
            logger.warning(f"Could not evaluate constraint '{condition}': {e}")

    return violations

def validate_schema(
    dataframe: pd.DataFrame, schema_path: Optional[str] = None
) -> None:
    """
    High‑level validation of a whole dataframe.

    This function checks:
    1. Presence of all required fields.
    2. Data‑type compatibility.
    3. High‑level constraints (e.g., ``d10 <= d50 <= d90``).

    It raises ``InsufficientDataError`` for structural problems and
    ``SchemaValidationError`` for constraint violations.
    """
    if not isinstance(dataframe, pd.DataFrame):
        raise InsufficientDataError(
            f"Input must be a pandas DataFrame, got {type(dataframe)}"
        )

    if dataframe.empty:
        raise InsufficientDataError("Input dataframe is empty; required fields are missing")

    schema = load_schema(schema_path)

    missing_fields = _validate_field_presence(dataframe, schema)
    if missing_fields:
        raise InsufficientDataError(
            f"Missing required fields: {', '.join(missing_fields)}. "
            f"Schema requires: {', '.join(REQUIRED_FIELDS)}"
        )

    type_errors = _validate_field_types(dataframe, schema)
    if type_errors:
        raise InsufficientDataError(
            f"Data type mismatches for fields: {', '.join(type_errors)}. "
            "Please ensure field types match the schema definition."
        )

    constraint_violations = _validate_constraints(dataframe, schema)
    if constraint_violations:
        raise SchemaValidationError(
            f"Data constraint violations: {'; '.join(constraint_violations)}"
        )

    logger.info("Schema validation passed successfully")

# ----------------------------------------------------------------------
# Row‑level validation required by task T007b
# ----------------------------------------------------------------------
def _row_violates_schema(row: Dict[str, Any], schema: Dict[str, Any]) -> Optional[str]:
    """
    Check a single row against the custom schema.

    Returns ``None`` if the row is valid, otherwise returns an error message.
    """
    # 1. Required fields must be present and non‑missing
    for field in REQUIRED_FIELDS:
        if field not in row or pd.isna(row[field]):
            return f"Missing required field or NaN value: '{field}'"

    # 2. Type checks based on the ``fields`` section
    for field_def in schema.get("fields", []):
        name = field_def["name"]
        expected_type_str = field_def["type"]
        expected_type = FIELD_TYPES.get(expected_type_str)

        # Skip if the field is not part of the row (already handled above)
        if name not in row:
            continue

        value = row[name]

        # Allow NaN for optional fields – they are already caught if required
        if pd.isna(value):
            continue

        # Type validation
        if expected_type_str == "float":
            if not isinstance(value, (float, int)):
                return f"Field '{name}' expects a numeric (float) value, got {type(value)}"
        elif expected_type_str == "integer":
            if not isinstance(value, int):
                return f"Field '{name}' expects an integer value, got {type(value)}"
        elif expected_type_str == "string":
            if not isinstance(value, str):
                return f"Field '{name}' expects a string value, got {type(value)}"
        elif expected_type_str == "boolean":
            if not isinstance(value, bool):
                return f"Field '{name}' expects a boolean value, got {type(value)}"

        # Enum validation (if present)
        if "enum" in field_def:
            if value not in field_def["enum"]:
                return f"Field '{name}' has invalid enum value '{value}'"

    # 3. Simple constraints (mirroring ``_validate_constraints``)
    for constraint in schema.get("constraints", []):
        field = constraint["field"]
        condition = constraint["condition"]
        try:
            if "d10 >= 0" in condition:
                if row.get(field, 0) < 0:
                    return f"Constraint violation: {field} must be >= 0"
            elif "d10 <= d50" in condition:
                if row.get("d10", 0) > row.get("d50", 0):
                    return "Constraint violation: d10 > d50"
            elif "d50 <= d90" in condition:
                if row.get("d50", 0) > row.get("d90", 0):
                    return "Constraint violation: d50 > d90"
            elif "milling_speed > 0" in condition:
                if row.get(field, 0) <= 0:
                    return f"Constraint violation: {field} must be > 0"
            elif "milling_time > 0" in condition:
                if row.get(field, 0) <= 0:
                    return f"Constraint violation: {field} must be > 0"
        except Exception as e:
            logger.warning(f"Error evaluating constraint '{condition}': {e}")

    return None  # No violation

def validate(df: pd.DataFrame, schema_path: Optional[str] = None) -> None:
    """
    Validate each row of a DataFrame against the dataset schema.

    This function loads the schema (defaulting to
    ``contracts/dataset.schema.yaml``) and checks every row individually.
    If any row does not conform, a ``jsonschema.ValidationError`` is raised
    with a descriptive message.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame to validate.
    schema_path : Optional[str]
        Path to a custom schema file; if omitted the default schema is used.

    Raises
    ------
    jsonschema.ValidationError
        If a row violates the schema (missing required field, wrong type,
        enum mismatch, or constraint violation).
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("Input must be a pandas DataFrame")

    # Load the custom schema definition
    schema = load_schema(schema_path)

    # Iterate over rows and validate
    for idx, row_series in df.iterrows():
        row_dict = row_series.to_dict()
        violation_msg = _row_violates_schema(row_dict, schema)
        if violation_msg is not None:
            # Raise a jsonschema.ValidationError to satisfy the contract
            raise ValidationError(message=violation_msg, instance=row_dict, schema=schema)

    logger.info("Row‑level schema validation passed for all %d rows", len(df))