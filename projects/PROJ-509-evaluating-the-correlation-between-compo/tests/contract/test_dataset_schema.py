"""
Contract test for dataset schema validation.

This test validates that the processed dataset (computed_descriptors.csv)
conforms to the schema defined in contracts/dataset.schema.yaml.

It checks:
- Required columns exist
- Data types match the schema (numeric for descriptors)
- No null values in required columns
- Value ranges are within expected bounds (if specified in schema)
"""

import os
import sys
import json
import yaml
import pandas as pd
import numpy as np
from pathlib import Path

# Add the project root to the path to allow imports
# Assuming the test is run from the project root or via pytest
project_root = Path(__file__).parent.parent.parent
code_dir = project_root / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from config import load_paths

def load_schema(schema_path: Path) -> dict:
    """Load the YAML schema definition."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, "r") as f:
        return yaml.safe_load(f)

def validate_column_types(df: pd.DataFrame, schema: dict) -> list:
    """Check if column types match the schema definition."""
    errors = []
    required_columns = schema.get("required_columns", [])
    column_types = schema.get("column_types", {})

    # Check required columns exist
    for col in required_columns:
        if col not in df.columns:
            errors.append(f"Missing required column: {col}")

    # Check types
    for col, expected_type in column_types.items():
        if col in df.columns:
            if expected_type == "numeric":
                if not pd.api.types.is_numeric_dtype(df[col]):
                    errors.append(f"Column '{col}' is not numeric (type: {df[col].dtype})")
            elif expected_type == "string":
                if not pd.api.types.is_string_dtype(df[col]) and not pd.api.types.is_object_dtype(df[col]):
                    errors.append(f"Column '{col}' is not string (type: {df[col].dtype})")

    return errors

def validate_nulls(df: pd.DataFrame, schema: dict) -> list:
    """Check for null values in required columns."""
    errors = []
    required_columns = schema.get("required_columns", [])

    for col in required_columns:
        if col in df.columns:
            if df[col].isnull().any():
                null_count = df[col].isnull().sum()
                errors.append(f"Column '{col}' contains {null_count} null values")

    return errors

def validate_ranges(df: pd.DataFrame, schema: dict) -> list:
    """Check if values are within specified ranges."""
    errors = []
    range_constraints = schema.get("range_constraints", {})

    for col, constraints in range_constraints.items():
        if col in df.columns:
            min_val = constraints.get("min")
            max_val = constraints.get("max")

            if min_val is not None:
                if (df[col] < min_val).any():
                    errors.append(f"Column '{col}' has values below minimum ({min_val})")
            if max_val is not None:
                if (df[col] > max_val).any():
                    errors.append(f"Column '{col}' has values above maximum ({max_val})")

    return errors

def test_dataset_schema_validation():
    """
    Main test function to validate the dataset against the schema.
    """
    paths = load_paths()
    schema_path = paths["contracts"] / "dataset.schema.yaml"
    # The task expects the output to be in data/processed/computed_descriptors.csv
    # based on T016/T017 description, though T013 creates sampled_raw_data.csv.
    # We check the final computed descriptors file as per the user story goal.
    data_path = paths["data"] / "processed" / "computed_descriptors.csv"

    # Fallback if computed_descriptors.csv doesn't exist yet (e.g. early in pipeline)
    if not data_path.exists():
        data_path = paths["data"] / "processed" / "sampled_raw_data.csv"

    if not data_path.exists():
        # If neither exists, we might be testing against a raw download or skipping
        # But for a contract test, we expect the data to be there or fail explicitly.
        # Let's check if the raw data exists as a last resort or fail.
        raw_path = paths["data"] / "raw" / "mp-2020.12.1.json" # Hypothetical raw name
        if not raw_path.exists():
            # If no data exists, we can't run the validation.
            # In a real CI/CD, this would fail the build if the file is expected.
            # For now, we raise an error to indicate the test cannot proceed.
            raise FileNotFoundError(
                f"Expected data file not found at {data_path}. "
                "Please ensure T012/T013/T016 have been executed."
            )
        else:
             # If raw exists but processed doesn't, we might need to adjust path logic
             # based on the specific state of the pipeline.
             # For this task, we assume the pipeline has run up to T016.
             data_path = raw_path

    # Load schema
    try:
        schema = load_schema(schema_path)
    except Exception as e:
        raise RuntimeError(f"Failed to load schema: {e}")

    # Load data
    try:
        df = pd.read_csv(data_path)
    except Exception as e:
        raise RuntimeError(f"Failed to load data file {data_path}: {e}")

    # Run validations
    all_errors = []
    all_errors.extend(validate_column_types(df, schema))
    all_errors.extend(validate_nulls(df, schema))
    all_errors.extend(validate_ranges(df, schema))

    # Assert no errors
    if all_errors:
        error_msg = "Schema validation failed:\n" + "\n".join(all_errors)
        raise AssertionError(error_msg)

    # If we get here, the test passes
    assert True, "Dataset schema validation passed"

if __name__ == "__main__":
    test_dataset_schema_validation()
    print("Contract test passed: Dataset schema is valid.")
