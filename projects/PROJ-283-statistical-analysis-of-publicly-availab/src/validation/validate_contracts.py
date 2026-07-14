import os
import re
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, field
import pandas as pd
import yaml
import logging

from src.config import get_contract_path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Container for validation results."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    schema_name: Optional[str] = None

    def add_error(self, message: str) -> None:
        self.errors.append(message)
        self.is_valid = False

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)

    def __bool__(self) -> bool:
        return self.is_valid

    def __str__(self) -> str:
        status = "VALID" if self.is_valid else "INVALID"
        error_count = len(self.errors)
        warning_count = len(self.warnings)
        return (f"Validation Result [{status}] for {self.schema_name or 'Unknown'}: "
                f"{error_count} errors, {warning_count} warnings")


def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load a YAML schema file."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = yaml.safe_load(f)

    if not isinstance(schema, dict):
        raise ValueError(f"Schema at {schema_path} must be a YAML dictionary")

    return schema


def validate_dataframe(
    df: pd.DataFrame,
    schema_name: str,
    required_columns: List[str],
    column_types: Optional[Dict[str, type]] = None
) -> ValidationResult:
    """
    Validate a pandas DataFrame against a schema definition.

    Args:
        df: The DataFrame to validate.
        schema_name: Name of the schema for reporting.
        required_columns: List of column names that must exist.
        column_types: Optional dict mapping column names to expected Python types.

    Returns:
        ValidationResult object.
    """
    result = ValidationResult(is_valid=True, schema_name=schema_name)

    if df.empty:
        result.add_warning("DataFrame is empty.")

    # Check required columns
    existing_cols = set(df.columns)
    missing_cols = set(required_columns) - existing_cols
    if missing_cols:
        result.add_error(f"Missing required columns: {sorted(missing_cols)}")

    # Check column types if provided
    if column_types:
        for col_name, expected_type in column_types.items():
            if col_name in existing_cols:
                # Check if the dtype is compatible (e.g., int64 vs int)
                actual_dtype = df[col_name].dtype
                # Simple check: ensure the values can be cast or are of compatible kind
                try:
                    if expected_type == int:
                        if not pd.api.types.is_integer_dtype(actual_dtype) and not pd.api.types.is_float_dtype(actual_dtype):
                            result.add_error(f"Column '{col_name}' expected integer type, got {actual_dtype}")
                    elif expected_type == float:
                        if not pd.api.types.is_numeric_dtype(actual_dtype):
                            result.add_error(f"Column '{col_name}' expected numeric type, got {actual_dtype}")
                    elif expected_type == str:
                        if not pd.api.types.is_string_dtype(actual_dtype):
                            # Allow object dtype for strings in older pandas
                            if actual_dtype != 'object' and actual_dtype.name != 'string':
                                result.add_error(f"Column '{col_name}' expected string type, got {actual_dtype}")
                    elif expected_type == bool:
                        if not pd.api.types.is_bool_dtype(actual_dtype):
                            result.add_error(f"Column '{col_name}' expected boolean type, got {actual_dtype}")
                except Exception as e:
                    result.add_warning(f"Could not fully validate type for '{col_name}': {e}")

    # Check for null values in required columns
    for col in required_columns:
        if col in existing_cols:
            null_count = df[col].isnull().sum()
            if null_count > 0:
                result.add_error(f"Column '{col}' contains {null_count} null values.")

    return result


def validate_game_records(df: pd.DataFrame) -> ValidationResult:
    """
    Validate a DataFrame against the game_record.schema.yaml.
    Loads the schema from specs/contracts/ dynamically.
    """
    schema_path = get_contract_path("game_record.schema.yaml")
    try:
        schema = load_schema(schema_path)
    except FileNotFoundError:
        # Fallback to hardcoded definition if schema file is missing during early dev
        logger.warning(f"Schema file {schema_path} not found. Using fallback definition.")
        schema = {
            "columns": [
                "game_id", "white_rating", "black_rating", "eco_code",
                "avg_move_time_white", "avg_move_time_black",
                "material_imbalance_move5", "outcome",
                "elo_expected_prob", "outcome_deviation"
            ],
            "types": {
                "game_id": str,
                "white_rating": (int, float),
                "black_rating": (int, float),
                "eco_code": str,
                "avg_move_time_white": (int, float),
                "avg_move_time_black": (int, float),
                "material_imbalance_move5": (int, float),
                "outcome": str,
                "elo_expected_prob": float,
                "outcome_deviation": float
            }
        }

    required_cols = schema.get("columns", [])
    type_map = schema.get("types", {})

    return validate_dataframe(
        df,
        schema_name="game_record",
        required_columns=required_cols,
        column_types=type_map
    )


def validate_model_output(df: pd.DataFrame) -> ValidationResult:
    """
    Validate a DataFrame against the model_output.schema.yaml.
    Loads the schema from specs/contracts/ dynamically.
    """
    schema_path = get_contract_path("model_output.schema.yaml")
    try:
        schema = load_schema(schema_path)
    except FileNotFoundError:
        logger.warning(f"Schema file {schema_path} not found. Using fallback definition.")
        schema = {
            "columns": [
                "model_type", "coefficients", "p_values",
                "r_squared", "aic", "cross_validation_scores"
            ],
            "types": {
                "model_type": str,
                "coefficients": dict,
                "p_values": dict,
                "r_squared": float,
                "aic": float,
                "cross_validation_scores": list
            }
        }

    required_cols = schema.get("columns", [])
    type_map = schema.get("types", {})

    return validate_dataframe(
        df,
        schema_name="model_output",
        required_columns=required_cols,
        column_types=type_map
    )


def assert_valid(result: ValidationResult) -> None:
    """Raise an AssertionError if validation failed."""
    if not result.is_valid:
        error_msg = f"Validation failed for {result.schema_name}:\n" + "\n".join(result.errors)
        raise AssertionError(error_msg)


def assert_game_records_valid(df: pd.DataFrame) -> ValidationResult:
    """Validate game records and raise if invalid, returning the result."""
    result = validate_game_records(df)
    assert_valid(result)
    return result


def assert_model_output_valid(df: pd.DataFrame) -> ValidationResult:
    """Validate model output and raise if invalid, returning the result."""
    result = validate_model_output(df)
    assert_valid(result)
    return result
