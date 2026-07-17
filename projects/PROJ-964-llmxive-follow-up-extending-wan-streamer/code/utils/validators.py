"""
Schema validation utilities for the llmXive pipeline.

This module provides functions to validate data structures (dicts, pandas DataFrames)
against defined schemas to ensure data integrity throughout the pipeline.
It is used by downstream tasks (e.g., T014, T018) to verify that extracted
latents and model outputs conform to expected formats.
"""

import os
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd
import numpy as np


# -----------------------------------------------------------------------------
# Schema Definitions
# -----------------------------------------------------------------------------

# Schema for the processed dataset (Output of T014/preprocess.py)
# Expected columns based on T013/T014 description:
# timestamp, semantic_feature, prosodic_feature, latent_delta_magnitude, turn_label
DATASET_SCHEMA = {
    "timestamp": {
        "type": "numeric",
        "nullable": False,
        "dtype": "float64",
    },
    "semantic_feature": {
        "type": "numeric",
        "nullable": False,
        "dtype": "float64",  # Or vector if handled differently, but scalar for now per description
    },
    "prosodic_feature": {
        "type": "numeric",
        "nullable": False,
        "dtype": "float64",
    },
    "latent_delta_magnitude": {
        "type": "numeric",
        "nullable": False,
        "dtype": "float64",
    },
    "turn_label": {
        "type": "categorical",
        "nullable": False,
        "allowed_values": ["interruption", "pause", "normal"],
        "dtype": "object",  # Pandas usually stores strings as object
    },
}

# Schema for Model Output (Output of T018/gru_estimator.py)
# Expected columns: predicted_delta_magnitude, uncertainty_score
MODEL_OUTPUT_SCHEMA = {
    "predicted_delta_magnitude": {
        "type": "numeric",
        "nullable": False,
        "dtype": "float64",
    },
    "uncertainty_score": {
        "type": "numeric",
        "nullable": False,
        "dtype": "float64",
        "constraints": {
            "min": 0.0,
            "max": 1.0,
        },
    },
}

# Schema for Power Analysis Output (Output of T029/power_analysis.py)
POWER_ANALYSIS_SCHEMA = {
    "expected_variance": {
        "type": "numeric",
        "nullable": False,
        "dtype": "float64",
    },
    "min_detectable_effect_size": {
        "type": "numeric",
        "nullable": False,
        "dtype": "float64",
    },
    "sample_size_required": {
        "type": "integer",
        "nullable": False,
        "dtype": "int64",
    },
    "power_level": {
        "type": "numeric",
        "nullable": False,
        "dtype": "float64",
    },
}


# -----------------------------------------------------------------------------
# Validation Logic
# -----------------------------------------------------------------------------

class ValidationError(Exception):
    """Custom exception for schema validation failures."""
    pass


def _check_column_types(df: pd.DataFrame, schema: Dict[str, Dict], errors: List[str]) -> None:
    """Check that columns exist and have correct types."""
    for col_name, col_spec in schema.items():
        if col_name not in df.columns:
            errors.append(f"Missing required column: '{col_name}'")
            continue

        actual_dtype = str(df[col_name].dtype)
        expected_dtype = col_spec.get("dtype")

        if expected_dtype and actual_dtype != expected_dtype:
            # Allow some flexibility for integer vs float if numeric
            if col_spec.get("type") == "numeric" and actual_dtype in ["int64", "int32", "float64", "float32"]:
                pass # Acceptable for numeric
            else:
                errors.append(f"Column '{col_name}' has dtype '{actual_dtype}', expected '{expected_dtype}'")


def _check_nulls(df: pd.DataFrame, schema: Dict[str, Dict], errors: List[str]) -> None:
    """Check for null values in non-nullable columns."""
    for col_name, col_spec in schema.items():
        if col_name not in df.columns:
            continue
        if not col_spec.get("nullable", True):
            null_count = df[col_name].isna().sum()
            if null_count > 0:
                errors.append(f"Column '{col_name}' contains {null_count} null values (not allowed)")


def _check_categorical_values(df: pd.DataFrame, schema: Dict[str, Dict], errors: List[str]) -> None:
    """Check that categorical columns only contain allowed values."""
    for col_name, col_spec in schema.items():
        if col_name not in df.columns:
            continue
        if col_spec.get("type") == "categorical":
            allowed = set(col_spec.get("allowed_values", []))
            if allowed:
                unique_vals = set(df[col_name].dropna().unique())
                invalid = unique_vals - allowed
                if invalid:
                    errors.append(f"Column '{col_name}' contains invalid values: {invalid}. Allowed: {allowed}")


def _check_constraints(df: pd.DataFrame, schema: Dict[str, Dict], errors: List[str]) -> None:
    """Check numeric constraints (min/max)."""
    for col_name, col_spec in schema.items():
        if col_name not in df.columns:
            continue
        constraints = col_spec.get("constraints", {})
        if constraints:
            col_data = df[col_name].dropna()
            if "min" in constraints:
                if col_data.min() < constraints["min"]:
                    errors.append(f"Column '{col_name}' has minimum value {col_data.min()}, expected >= {constraints['min']}")
            if "max" in constraints:
                if col_data.max() > constraints["max"]:
                    errors.append(f"Column '{col_name}' has maximum value {col_data.max()}, expected <= {constraints['max']}")


def validate_dataframe(df: pd.DataFrame, schema: Dict[str, Dict], schema_name: str = "Unknown") -> Tuple[bool, List[str]]:
    """
    Validate a pandas DataFrame against a given schema.

    Args:
        df: The DataFrame to validate.
        schema: The schema definition dictionary.
        schema_name: Name of the schema for error messages.

    Returns:
        Tuple of (is_valid, list_of_error_messages).
    """
    errors = []

    if df.empty:
        errors.append(f"DataFrame for '{schema_name}' is empty.")
        return False, errors

    _check_column_types(df, schema, errors)
    _check_nulls(df, schema, errors)
    _check_categorical_values(df, schema, errors)
    _check_constraints(df, schema, errors)

    is_valid = len(errors) == 0
    return is_valid, errors


def validate_dataset_schema(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Validates the processed dataset schema (T014 output).

    Args:
        df: DataFrame containing the processed dataset.

    Returns:
        Tuple of (is_valid, list_of_error_messages).
    """
    return validate_dataframe(df, DATASET_SCHEMA, "Dataset Schema")


def validate_model_output(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Validates the model output schema (T018/T019 output).

    Args:
        df: DataFrame containing model predictions.

    Returns:
        Tuple of (is_valid, list_of_error_messages).
    """
    return validate_dataframe(df, MODEL_OUTPUT_SCHEMA, "Model Output Schema")


def validate_power_analysis(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Validates the power analysis output schema (T029 output).

    Args:
        df: DataFrame containing power analysis results.

    Returns:
        Tuple of (is_valid, list_of_error_messages).
    """
    return validate_dataframe(df, POWER_ANALYSIS_SCHEMA, "Power Analysis Schema")


def validate_json_file(file_path: Union[str, Path], schema: Dict[str, Any], schema_name: str = "Unknown") -> Tuple[bool, List[str]]:
    """
    Validates a JSON file against a simple schema (keys and types).
    Note: This is for simple JSON structures, not nested complex ones unless extended.

    Args:
        file_path: Path to the JSON file.
        schema: Dictionary of expected keys and their expected Python types.
        schema_name: Name for error reporting.

    Returns:
        Tuple of (is_valid, list_of_error_messages).
    """
    errors = []
    path = Path(file_path)

    if not path.exists():
        return False, [f"File not found: {path}"]

    try:
        with open(path, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return False, [f"Invalid JSON in {path}: {e}"]

    if not isinstance(data, dict):
        return False, [f"Expected JSON object at root, got {type(data).__name__}"]

    for key, expected_type in schema.items():
        if key not in data:
            errors.append(f"Missing key: '{key}'")
            continue
        if not isinstance(data[key], expected_type):
            errors.append(f"Key '{key}' has type {type(data[key]).__name__}, expected {expected_type.__name__}")

    return len(errors) == 0, errors