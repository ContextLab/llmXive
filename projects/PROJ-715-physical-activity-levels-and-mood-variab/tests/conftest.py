"""
Base test utilities for schema validation and fixture data.

This module provides pytest fixtures and helper functions used across
the test suite for the Physical Activity and Mood Variability project.
"""

import json
import os
import tempfile
from pathlib import Path

import pytest
import pandas as pd
import yaml

# Import project configuration
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from config import get_path


@pytest.fixture(scope="session")
def project_root():
    """Return the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def data_dir(project_root):
    """Return the data directory."""
    return project_root / "data"


@pytest.fixture(scope="session")
def processed_dir(data_dir):
    """Return the processed data directory."""
    return data_dir / "processed"


@pytest.fixture(scope="session")
def raw_dir(data_dir):
    """Return the raw data directory."""
    return data_dir / "raw"


@pytest.fixture(scope="session")
def schema_dir(project_root):
    """Return the schema definitions directory."""
    return project_root / "specs" / "001-physical-activity-mood-variability" / "contracts"

# ---------------------------------------------------------------------
# Schema Validation Helpers
# ---------------------------------------------------------------------

def load_schema(schema_name):
    """
    Load a YAML schema definition from the contracts directory.
    
    Args:
        schema_name (str): Name of the schema file (e.g., 'daily_aggregates.schema.yaml')
    
    Returns:
        dict: The loaded schema definition.
    """
    schema_path = get_path("contracts") / schema_name
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_dataframe_against_schema(df, schema):
    """
    Validate a pandas DataFrame against a YAML schema definition.
    
    Args:
        df (pd.DataFrame): The DataFrame to validate.
        schema (dict): The schema definition loaded from YAML.
    
    Returns:
        tuple: (is_valid, errors) where errors is a list of error messages.
    """
    errors = []
    
    if "required_columns" in schema:
        required_cols = set(schema["required_columns"])
        actual_cols = set(df.columns)
        missing = required_cols - actual_cols
        if missing:
            errors.append(f"Missing required columns: {missing}")
    
    if "column_types" in schema:
        for col_name, expected_type in schema["column_types"].items():
            if col_name in df.columns:
                actual_dtype = df[col_name].dtype
                # Simple type mapping for validation
                type_map = {
                    "integer": ["int64", "int32"],
                    "float": ["float64", "float32"],
                    "string": ["object", "string"],
                    "datetime": ["datetime64[ns]"]
                }
                if expected_type in type_map:
                    if actual_dtype not in type_map[expected_type]:
                        errors.append(
                            f"Column '{col_name}' has type {actual_dtype}, "
                            f"expected {expected_type}"
                        )
    
    if "constraints" in schema:
        for constraint in schema["constraints"]:
            if constraint.get("type") == "not_null":
                for col in constraint.get("columns", []):
                    if col in df.columns:
                        if df[col].isnull().any():
                            errors.append(f"Column '{col}' contains null values")
            elif constraint.get("type") == "positive":
                for col in constraint.get("columns", []):
                    if col in df.columns:
                        if (df[col] <= 0).any():
                            errors.append(f"Column '{col}' contains non-positive values")
    
    return len(errors) == 0, errors

# ---------------------------------------------------------------------
# Fixtures for Test Data
# ---------------------------------------------------------------------

@pytest.fixture
def sample_daily_aggregates():
    """
    Create a sample DataFrame matching the daily_aggregates schema.
    
    Returns:
        pd.DataFrame: A sample dataset for testing.
    """
    data = {
        "participant_id": ["P001", "P001", "P002", "P002"],
        "date": ["2013-01-01", "2013-01-02", "2013-01-01", "2013-01-02"],
        "total_steps": [8500, 7200, 10200, 9500],
        "mean_mood": [3.5, 4.0, 2.8, 3.2],
        "mood_std": [0.5, 0.3, 0.8, 0.4],
        "log_mood_std": [-0.693, -1.204, -0.223, -0.916],
        "sleep_duration": [7.2, 6.8, 8.1, 7.5],
        "baseline_affect": [3.0, 3.0, 2.5, 2.5],
        "day_of_week": [2, 3, 2, 3]
    }
    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["date"])
    return df

@pytest.fixture
def sample_model_results():
    """
    Create a sample dictionary matching the model_results schema.
    
    Returns:
        dict: A sample results dictionary for testing.
    """
    return {
        "model_type": "LinearMixedEffects",
        "outcome": "log_mood_std",
        "predictor": "total_steps",
        "fixed_effects": {
            "total_steps": {
                "estimate": -0.00012,
                "std_err": 0.00004,
                "p_value": 0.003,
                "ci_95_lower": -0.00020,
                "ci_95_upper": -0.00004
            },
            "sleep_duration": {
                "estimate": 0.05,
                "std_err": 0.02,
                "p_value": 0.012,
                "ci_95_lower": 0.01,
                "ci_95_upper": 0.09
            }
        },
        "random_effects": {
            "participant_id": {
                "variance": 0.15
            }
        },
        "convergence": True,
        "n_observations": 500,
        "n_groups": 48
    }

# ---------------------------------------------------------------------
# Helper Functions for Tests
# ---------------------------------------------------------------------

def get_schema_path(schema_name):
    """
    Get the full path to a schema file.
    
    Args:
        schema_name (str): Name of the schema file.
    
    Returns:
        Path: Full path to the schema file.
    """
    return get_path("contracts") / schema_name

def validate_csv_schema(csv_path, schema_name):
    """
    Load a CSV and validate it against a named schema.
    
    Args:
        csv_path (str or Path): Path to the CSV file.
        schema_name (str): Name of the schema to validate against.
    
    Returns:
        tuple: (is_valid, errors, df)
    """
    df = pd.read_csv(csv_path)
    schema = load_schema(schema_name)
    is_valid, errors = validate_dataframe_against_schema(df, schema)
    return is_valid, errors, df

def validate_json_schema(json_path, schema_name):
    """
    Load a JSON file and validate it against a named schema.
    
    Args:
        json_path (str or Path): Path to the JSON file.
        schema_name (str): Name of the schema to validate against.
    
    Returns:
        tuple: (is_valid, errors, data)
    """
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    # Basic JSON structure validation (schema for JSON is usually simpler)
    schema = load_schema(schema_name)
    errors = []
    
    if "required_keys" in schema:
        missing = set(schema["required_keys"]) - set(data.keys())
        if missing:
            errors.append(f"Missing required keys: {missing}")
    
    return len(errors) == 0, errors, data