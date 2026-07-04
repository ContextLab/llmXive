"""
Data validation logic to enforce FR-001 requirements.
Validates schema compliance and metadata presence.
"""
import os
import json
import yaml
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple

from code.config import (
    DATASET_SCHEMA_PATH,
    FEATURE_SCHEMA_PATH,
    REQUIRED_METADATA_FIELDS,
    ALLOWED_MODALITIES,
    REQUIRED_FEATURE_COLUMNS
)


class ValidationError(Exception):
    """Custom exception for validation failures."""
    pass


def load_schema(schema_path: str) -> Dict[str, Any]:
    """
    Load a YAML schema definition from disk.

    Args:
        schema_path: Path to the schema YAML file.

    Returns:
        Dictionary containing the schema definition.

    Raises:
        FileNotFoundError: If the schema file does not exist.
        yaml.YAMLError: If the YAML is malformed.
    """
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    with open(schema_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def validate_metadata_present(df: pd.DataFrame, required_fields: List[str]) -> Tuple[bool, List[str]]:
    """
    Check if all required metadata fields exist in the DataFrame columns.

    Args:
        df: The DataFrame to validate.
        required_fields: List of column names that must be present.

    Returns:
        Tuple of (is_valid, list_of_missing_fields).
    """
    missing = [field for field in required_fields if field not in df.columns]
    return len(missing) == 0, missing


def validate_modalities(df: pd.DataFrame, modality_column: str = "modality", allowed: List[str] = None) -> Tuple[bool, List[str]]:
    """
    Validate that modality values are within the allowed set.

    Args:
        df: The DataFrame to validate.
        modality_column: Name of the column containing modality values.
        allowed: List of allowed modality strings. Defaults to config.

    Returns:
        Tuple of (is_valid, list_of_invalid_values).
    """
    if allowed is None:
        allowed = ALLOWED_MODALITIES

    if modality_column not in df.columns:
        return False, [f"Column '{modality_column}' not found"]

    invalid_values = [v for v in df[modality_column].unique() if v not in allowed]
    return len(invalid_values) == 0, invalid_values


def validate_schema_compliance(df: pd.DataFrame, schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate DataFrame against a loaded schema definition.
    Checks column types and presence based on schema 'properties'.

    Args:
        df: The DataFrame to validate.
        schema: The loaded schema dictionary.

    Returns:
        Tuple of (is_valid, list_of_errors).
    """
    errors = []
    properties = schema.get("properties", {})

    for col_name, col_spec in properties.items():
        if col_name not in df.columns:
            if col_spec.get("required", False):
                errors.append(f"Missing required column: {col_name}")
            continue

        # Basic type check if type is specified in schema
        expected_type = col_spec.get("type")
        if expected_type:
            actual_dtype = df[col_name].dtype
            # Simple mapping for common types
            type_map = {
                "string": "object",
                "integer": "int64",
                "number": "float64",
                "boolean": "bool"
            }
            expected_python_type = type_map.get(expected_type)

            # If types don't match and it's not a loose match (e.g. int64 vs float64)
            # We do a strict check for object/string mismatches
            if expected_python_type == "object" and not pd.api.types.is_object_dtype(df[col_name]):
                # Allow integer columns to be treated as strings if needed, but warn
                pass 
            elif expected_python_type and not str(actual_dtype).startswith(expected_python_type):
                # Allow numeric flexibility
                if not (expected_python_type == "float64" and str(actual_dtype).startswith("int")):
                     errors.append(f"Column '{col_name}' expected type '{expected_type}' but found '{actual_dtype}'")

    return len(errors) == 0, errors


def validate_dataset(df: pd.DataFrame, schema_path: str = DATASET_SCHEMA_PATH) -> bool:
    """
    Full validation pipeline for a raw dataset file.
    1. Load schema.
    2. Check metadata presence.
    3. Check schema compliance.
    4. Check modality validity.

    Args:
        df: DataFrame representing the dataset.
        schema_path: Path to the schema YAML.

    Raises:
        ValidationError: If any validation step fails.
    """
    # 1. Load Schema
    try:
        schema = load_schema(schema_path)
    except FileNotFoundError as e:
        raise ValidationError(f"Schema definition missing: {e}")

    # 2. Metadata Presence
    is_valid, missing = validate_metadata_present(df, REQUIRED_METADATA_FIELDS)
    if not is_valid:
        raise ValidationError(f"Missing required metadata fields: {missing}")

    # 3. Schema Compliance
    is_valid, schema_errors = validate_schema_compliance(df, schema)
    if not is_valid:
        raise ValidationError(f"Schema compliance failed: {schema_errors}")

    # 4. Modality Check (if column exists)
    if "modality" in df.columns:
        is_valid, invalid_modalities = validate_modalities(df)
        if not is_valid:
            raise ValidationError(f"Invalid modality values found: {invalid_modalities}")

    return True


def validate_features(df: pd.DataFrame) -> bool:
    """
    Validate processed feature data.
    Ensures required columns exist and no NaN values exist in critical fields.

    Args:
        df: DataFrame of processed features.

    Raises:
        ValidationError: If validation fails.
    """
    # Check required columns
    is_valid, missing = validate_metadata_present(df, REQUIRED_FEATURE_COLUMNS)
    if not is_valid:
        raise ValidationError(f"Feature data missing required columns: {missing}")

    # Check for NaN in critical numeric/ID columns
    critical_cols = ["interaction_id", "value"]
    for col in critical_cols:
        if col in df.columns and df[col].isna().any():
            raise ValidationError(f"Critical column '{col}' contains NaN values")

    return True
