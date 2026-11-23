"""
Schema validation utilities for the llmXive pipeline.

Provides strict validation functions for DataFrames, JSON files, and model outputs
to ensure data integrity and schema compliance throughout the research pipeline.

Validates against:
- Dataset schemas (columns, types, null checks)
- Model output schemas (shapes, value ranges)
- Power analysis JSON structures
"""

import os
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd
import numpy as np


class ValidationError(Exception):
    """Custom exception for schema validation failures."""
    pass


def validate_dataframe(
    df: pd.DataFrame,
    required_columns: List[str],
    column_types: Optional[Dict[str, type]] = None,
    allow_nulls: Optional[Dict[str, bool]] = None,
    min_rows: Optional[int] = None,
    name: str = "DataFrame"
) -> Tuple[bool, List[str]]:
    """
    Validate a DataFrame against a schema definition.

    Args:
        df: The DataFrame to validate.
        required_columns: List of column names that must exist.
        column_types: Dict mapping column names to expected types (e.g., np.float64).
        allow_nulls: Dict mapping column names to whether nulls are allowed.
        min_rows: Minimum number of rows required.
        name: Human-readable name for error messages.

    Returns:
        Tuple of (is_valid, list_of_error_messages).

    Raises:
        ValidationError: If validation fails.
    """
    errors = []

    # Check for empty DataFrame
    if df.empty:
        errors.append(f"{name} is empty.")
        if min_rows and min_rows > 0:
            errors.append(f"{name} must have at least {min_rows} rows.")
        if errors:
            raise ValidationError("\n".join(errors))

    # Check min_rows
    if min_rows is not None and len(df) < min_rows:
        errors.append(f"{name} has {len(df)} rows, but requires at least {min_rows}.")

    # Check required columns
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        errors.append(f"{name} is missing required columns: {missing_cols}")

    # Check column types
    if column_types:
        for col, expected_type in column_types.items():
            if col in df.columns:
                # Handle numpy types vs python types
                actual_dtype = df[col].dtype
                if not np.issubdtype(actual_dtype, np.dtype(expected_type).type):
                    # Special handling for object vs string
                    if expected_type == str and actual_dtype == object:
                        # Check if all values are actually strings
                        if not df[col].apply(lambda x: isinstance(x, str) or pd.isna(x)).all():
                            errors.append(
                                f"Column '{col}' in {name} has dtype {actual_dtype}, "
                                f"expected string-compatible type."
                            )
                    else:
                        errors.append(
                            f"Column '{col}' in {name} has dtype {actual_dtype}, "
                            f"expected {expected_type}."
                        )

    # Check null constraints
    if allow_nulls:
        for col, allow_null in allow_nulls.items():
            if col in df.columns:
                null_count = df[col].isna().sum()
                if not allow_null and null_count > 0:
                    errors.append(
                        f"Column '{col}' in {name} contains {null_count} null values, "
                        f"but nulls are not allowed."
                    )

    if errors:
        raise ValidationError("\n".join(errors))

    return True, []


def validate_dataset_schema(
    df: pd.DataFrame,
    schema_type: str = "latent_extraction"
) -> Tuple[bool, List[str]]:
    """
    Validate a DataFrame against a known dataset schema.

    Args:
        df: The DataFrame to validate.
        schema_type: The type of schema to validate against.
            Supported: 'latent_extraction', 'model_output', 'power_analysis'

    Returns:
        Tuple of (is_valid, list_of_error_messages).

    Raises:
        ValidationError: If validation fails.
    """
    errors = []

    if schema_type == "latent_extraction":
        # Schema for extracted latents (T013 output)
        required_cols = [
            "timestamp", "semantic_feature", "prosodic_feature",
            "latent_delta_magnitude", "turn_label"
        ]
        type_map = {
            "timestamp": np.float64,
            "semantic_feature": np.float64,
            "prosodic_feature": np.float64,
            "latent_delta_magnitude": np.float64,
            "turn_label": object  # Categorical/str
        }
        no_nulls = {col: False for col in required_cols}

        try:
            validate_dataframe(
                df,
                required_columns=required_cols,
                column_types=type_map,
                allow_nulls=no_nulls,
                min_rows=100,
                name="Latent Extraction Dataset"
            )
            return True, []
        except ValidationError as e:
            errors.append(str(e))

    elif schema_type == "interrupted_events":
        # Schema for filtered interruption/pause events
        required_cols = [
            "timestamp", "event_type", "latent_delta_magnitude",
            "turn_label", "priority_label"
        ]
        type_map = {
            "timestamp": np.float64,
            "event_type": object,
            "latent_delta_magnitude": np.float64,
            "turn_label": object,
            "priority_label": object
        }
        no_nulls = {col: False for col in required_cols}

        try:
            validate_dataframe(
                df,
                required_columns=required_cols,
                column_types=type_map,
                allow_nulls=no_nulls,
                min_rows=100,
                name="Interrupted Events Dataset"
            )
            return True, []
        except ValidationError as e:
            errors.append(str(e))

    else:
        errors.append(f"Unknown schema type: {schema_type}")

    if errors:
        raise ValidationError("\n".join(errors))

    return True, []


def validate_model_output(
    predictions: np.ndarray,
    expected_shape: Tuple[int, int] = (None, 2),
    delta_col_idx: int = 0,
    uncertainty_col_idx: int = 1,
    uncertainty_range: Tuple[float, float] = (0.0, 1.0)
) -> Tuple[bool, List[str]]:
    """
    Validate model output tensor/array from GRU estimator.

    Args:
        predictions: The output array/tensor from the model.
        expected_shape: Expected shape tuple (rows, cols). Use None for flexible dimension.
        delta_col_idx: Index of the delta magnitude column.
        uncertainty_col_idx: Index of the uncertainty score column.
        uncertainty_range: Valid range for uncertainty scores (min, max).

    Returns:
        Tuple of (is_valid, list_of_error_messages).

    Raises:
        ValidationError: If validation fails.
    """
    errors = []
    arr = np.asarray(predictions)

    # Check dimensionality
    if arr.ndim != 2:
        errors.append(f"Model output must be 2D, got {arr.ndim}D.")
        raise ValidationError("\n".join(errors))

    rows, cols = arr.shape

    # Check column count
    if expected_shape[1] is not None and cols != expected_shape[1]:
        errors.append(
            f"Model output must have {expected_shape[1]} columns, got {cols}."
        )

    # Check uncertainty range
    if uncertainty_col_idx < cols:
        unc_vals = arr[:, uncertainty_col_idx]
        min_unc, max_unc = uncertainty_range
        if not np.all((unc_vals >= min_unc) & (unc_vals <= max_unc)):
            errors.append(
                f"Uncertainty scores must be in range [{min_unc}, {max_unc}], "
                f"got min={unc_vals.min():.4f}, max={unc_vals.max():.4f}."
            )

    # Check for NaNs in critical columns
    if np.any(np.isnan(arr)):
        errors.append("Model output contains NaN values.")

    # Check for Inf in delta magnitude
    if delta_col_idx < cols:
        delta_vals = arr[:, delta_col_idx]
        if np.any(np.isinf(delta_vals)):
            errors.append("Delta magnitude column contains infinite values.")

    if errors:
        raise ValidationError("\n".join(errors))

    return True, []


def validate_power_analysis(
    json_path: Union[str, Path],
    required_keys: Optional[List[str]] = None
) -> Tuple[bool, List[str]]:
    """
    Validate a power analysis JSON file structure.

    Args:
        json_path: Path to the JSON file.
        required_keys: List of keys that must be present.

    Returns:
        Tuple of (is_valid, list_of_error_messages).

    Raises:
        ValidationError: If validation fails.
    """
    errors = []
    path = Path(json_path)

    if not path.exists():
        raise ValidationError(f"Power analysis file not found: {path}")

    try:
        with open(path, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValidationError(f"Invalid JSON in power analysis file: {e}")

    if not isinstance(data, dict):
        raise ValidationError("Power analysis file must contain a JSON object.")

    default_required = [
        "variance", "effect_size", "sample_size", "power", "alpha"
    ]
    keys_to_check = required_keys if required_keys else default_required

    missing_keys = [k for k in keys_to_check if k not in data]
    if missing_keys:
        errors.append(f"Missing required keys in power analysis: {missing_keys}")

    # Validate numeric types for specific keys
    numeric_keys = ["variance", "effect_size", "sample_size", "power", "alpha"]
    for key in numeric_keys:
        if key in data:
            if not isinstance(data[key], (int, float)):
                errors.append(f"Key '{key}' must be numeric, got {type(data[key]).__name__}")
            elif key in ["variance", "effect_size", "power", "alpha"] and data[key] < 0:
                errors.append(f"Key '{key}' must be non-negative, got {data[key]}")
            elif key == "alpha" and not (0 < data[key] < 1):
                errors.append(f"Key 'alpha' must be between 0 and 1, got {data[key]}")

    if errors:
        raise ValidationError("\n".join(errors))

    return True, []


def validate_json_file(
    json_path: Union[str, Path],
    schema_type: Optional[str] = None
) -> Tuple[bool, List[str]]:
    """
    Generic JSON file validation.

    Args:
        json_path: Path to the JSON file.
        schema_type: Optional schema type for specific validation logic.

    Returns:
        Tuple of (is_valid, list_of_error_messages).

    Raises:
        ValidationError: If validation fails.
    """
    errors = []
    path = Path(json_path)

    if not path.exists():
        raise ValidationError(f"JSON file not found: {path}")

    try:
        with open(path, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValidationError(f"Invalid JSON format: {e}")

    if schema_type == "baseline_comparison":
        required_keys = ["zero_delta_mse", "gru_mse", "p_value", "improvement_percent"]
        missing = [k for k in required_keys if k not in data]
        if missing:
            errors.append(f"Missing keys in baseline comparison: {missing}")
        if "gru_mse" in data and data["gru_mse"] >= data.get("zero_delta_mse", float('inf')):
            errors.append("GRU MSE must be lower than zero-delta MSE.")

    elif schema_type == "tost_results":
        required_keys = ["parameter", "equivalence_margin", "p_value_lower", "p_value_upper", "equivalent"]
        missing = [k for k in required_keys if k not in data]
        if missing:
            errors.append(f"Missing keys in TOST results: {missing}")

    if errors:
        raise ValidationError("\n".join(errors))

    return True, []