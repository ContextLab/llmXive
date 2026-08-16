"""
Contract test for metadata schema validation.

This test validates that the metadata DataFrame produced by the download pipeline
adheres to the strict schema requirements defined in the project specification.
It checks for required columns, data types, and value constraints.

Dependencies:
    - T011b: Requires the parse_spectrum_metadata function to have been implemented
      to generate the DataFrame being tested.
"""

import pandas as pd
import numpy as np
import pytest
from typing import Any, Dict, List, Optional

# Import the data models to ensure schema consistency
# The data_models module defines the expected Enum values and structures
try:
    from code.data_models import PlanetCategory, CensorshipStatus
except ImportError:
    # Fallback for direct execution in test runner if path setup differs
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))
    from data_models import PlanetCategory, CensorshipStatus


# Define the strict schema contract
METADATA_SCHEMA = {
    "planet_name": {
        "type": "string",
        "nullable": False,
        "description": "Unique identifier for the exoplanet"
    },
    "temperature": {
        "type": "float",
        "nullable": False,
        "min_value": 0.0,
        "description": "Equilibrium temperature in Kelvin"
    },
    "metallicity": {
        "type": "float",
        "nullable": True,
        "description": "Host star metallicity [Fe/H] in dex"
    },
    "snr": {
        "type": "float",
        "nullable": False,
        "min_value": 0.0,
        "description": "Signal-to-noise ratio"
    },
    "resolution": {
        "type": "float",
        "nullable": False,
        "min_value": 0.0,
        "description": "Spectral resolution (R)"
    },
    "planet_category": {
        "type": "string",
        "nullable": False,
        "allowed_values": ["Hot Jupiter", "Temperate Super-Earth", "Other"],
        "description": "Classification based on radius and temperature"
    },
    "instrument": {
        "type": "string",
        "nullable": False,
        "description": "Name of the instrument used for observation"
    },
    "wavelength_range": {
        "type": "string",
        "nullable": False,
        "description": "Wavelength range covered (e.g., '0.5-5.0 um')"
    }
}

REQUIRED_COLUMNS = list(METADATA_SCHEMA.keys())


def validate_metadata_schema(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validates a DataFrame against the strict metadata schema contract.

    This function performs the following checks:
    1. All required columns are present.
    2. Data types match the schema (string vs numeric).
    3. No null values exist in non-nullable fields.
    4. Numeric values satisfy min/max constraints.
    5. Categorical fields contain only allowed values.

    Args:
        df (pd.DataFrame): The metadata DataFrame to validate.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - 'valid': bool (True if schema is respected)
            - 'errors': List[str] (List of specific validation failure messages)
            - 'stats': Dict (Summary statistics of the validation run)
    """
    errors: List[str] = []
    stats: Dict[str, Any] = {
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "missing_columns": [],
        "type_mismatches": [],
        "null_violations": [],
        "value_violations": []
    }

    if df.empty:
        return {
            "valid": False,
            "errors": ["DataFrame is empty. Cannot validate schema on empty data."],
            "stats": stats
        }

    # 1. Check for required columns
    missing_cols = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing_cols:
        stats["missing_columns"] = list(missing_cols)
        errors.append(f"Missing required columns: {', '.join(missing_cols)}")
        # If columns are missing, we cannot proceed with row-level validation safely
        return {
            "valid": False,
            "errors": errors,
            "stats": stats
        }

    # 2. Validate types and constraints per column
    for col_name, rules in METADATA_SCHEMA.items():
        if col_name not in df.columns:
            continue  # Already caught above

        col_data = df[col_name]

        # Type Check
        if rules["type"] == "string":
            if not pd.api.types.is_string_dtype(col_data):
                # Allow object dtype which often holds strings
                if not col_data.apply(lambda x: isinstance(x, str) or pd.isna(x)).all():
                    stats["type_mismatches"].append(col_name)
                    errors.append(f"Column '{col_name}' must be string type.")
                    continue

        elif rules["type"] == "float":
            if not pd.api.types.is_numeric_dtype(col_data):
                stats["type_mismatches"].append(col_name)
                errors.append(f"Column '{col_name}' must be numeric type.")
                continue

        # Null Check
        if not rules["nullable"]:
            null_count = col_data.isnull().sum()
            if null_count > 0:
                stats["null_violations"].append(col_name)
                errors.append(f"Column '{col_name}' contains {null_count} null values but is marked non-nullable.")

        # Value Constraints (Min/Max)
        if rules["type"] == "float" and "min_value" in rules:
            min_val = rules["min_value"]
            # Filter out nulls for comparison
            valid_vals = col_data.dropna()
            if len(valid_vals) > 0:
                violations = valid_vals[valid_vals < min_val]
                if len(violations) > 0:
                    stats["value_violations"].append(col_name)
                    errors.append(f"Column '{col_name}' has {len(violations)} values below min {min_val}.")

        # Allowed Values Check (Categorical)
        if "allowed_values" in rules:
            if rules["type"] == "string":
                unique_vals = set(col_data.dropna().unique())
                allowed_set = set(rules["allowed_values"])
                invalid_vals = unique_vals - allowed_set
                if invalid_vals:
                    stats["value_violations"].append(col_name)
                    errors.append(f"Column '{col_name}' contains invalid values: {invalid_vals}. Allowed: {rules['allowed_values']}")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "stats": stats
    }


# --- Contract Tests ---

def test_schema_has_required_columns():
    """Test that the schema definition includes all required fields."""
    assert "planet_name" in METADATA_SCHEMA
    assert "temperature" in METADATA_SCHEMA
    assert "metallicity" in METADATA_SCHEMA
    assert "snr" in METADATA_SCHEMA
    assert "resolution" in METADATA_SCHEMA
    assert "planet_category" in METADATA_SCHEMA
    assert "instrument" in METADATA_SCHEMA
    assert "wavelength_range" in METADATA_SCHEMA


def test_validate_metadata_schema_empty_dataframe():
    """Test that validation fails gracefully on empty data."""
    empty_df = pd.DataFrame()
    result = validate_metadata_schema(empty_df)
    assert result["valid"] is False
    assert "empty" in result["errors"][0].lower()


def test_validate_metadata_schema_missing_columns():
    """Test detection of missing required columns."""
    partial_df = pd.DataFrame({
        "planet_name": ["Kepler-1b"],
        "temperature": [1500.0]
        # Missing others
    })
    result = validate_metadata_schema(partial_df)
    assert result["valid"] is False
    assert "Missing required columns" in result["errors"][0]


def test_validate_metadata_schema_null_violation():
    """Test detection of nulls in non-nullable fields."""
    df = pd.DataFrame({
        "planet_name": ["Kepler-1b"],
        "temperature": [np.nan],  # Non-nullable
        "metallicity": [0.1],     # Nullable
        "snr": [10.0],
        "resolution": [50.0],
        "planet_category": ["Hot Jupiter"],
        "instrument": ["HST"],
        "wavelength_range": ["0.5-5.0"]
    })
    result = validate_metadata_schema(df)
    assert result["valid"] is False
    assert any("temperature" in err for err in result["errors"])


def test_validate_metadata_schema_invalid_category():
    """Test detection of invalid planet categories."""
    df = pd.DataFrame({
        "planet_name": ["Kepler-1b"],
        "temperature": [1500.0],
        "metallicity": [0.1],
        "snr": [10.0],
        "resolution": [50.0],
        "planet_category": ["Gas Giant"],  # Invalid
        "instrument": ["HST"],
        "wavelength_range": ["0.5-5.0"]
    })
    result = validate_metadata_schema(df)
    assert result["valid"] is False
    assert any("planet_category" in err for err in result["errors"])


def test_validate_metadata_schema_success():
    """Test validation on a correctly formed DataFrame."""
    df = pd.DataFrame({
        "planet_name": ["Kepler-1b", "WASP-12b"],
        "temperature": [1500.0, 2500.0],
        "metallicity": [0.1, -0.2],
        "snr": [10.0, 15.0],
        "resolution": [50.0, 100.0],
        "planet_category": ["Hot Jupiter", "Hot Jupiter"],
        "instrument": ["HST", "JWST"],
        "wavelength_range": ["0.5-5.0", "0.6-5.0"]
    })
    result = validate_metadata_schema(df)
    assert result["valid"] is True
    assert len(result["errors"]) == 0
    assert result["stats"]["total_rows"] == 2


def test_validate_metadata_schema_negative_temperature():
    """Test detection of physically impossible negative temperatures."""
    df = pd.DataFrame({
        "planet_name": ["Kepler-1b"],
        "temperature": [-100.0],  # Invalid
        "metallicity": [0.1],
        "snr": [10.0],
        "resolution": [50.0],
        "planet_category": ["Hot Jupiter"],
        "instrument": ["HST"],
        "wavelength_range": ["0.5-5.0"]
    })
    result = validate_metadata_schema(df)
    assert result["valid"] is False
    assert any("temperature" in err for err in result["errors"])