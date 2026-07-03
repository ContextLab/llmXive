"""
Contract test for data schema validation.

Validates that the merged dataset (repo_metrics.csv) produced by the pipeline
adheres to the expected schema defined in code/data/schemas.py.

This test ensures:
1. All required columns are present.
2. Column data types match the specification.
3. No null values exist in critical columns (kloc, cve_count, unique_authors).
"""
import os
import sys
import pytest
import pandas as pd
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.data.schemas import get_schema, validate_dataframe
from code.config import ensure_directories


@pytest.fixture
def expected_schema():
    """
    Returns the expected schema for the merged dataset (repo_metrics.csv).
    Matches the definition in code/data/schemas.py.
    """
    return get_schema("repo_metrics")


@pytest.fixture
def test_data_path():
    """
    Returns the path to the expected merged dataset file.
    """
    ensure_directories()
    return Path(PROJECT_ROOT) / "data" / "processed" / "repo_metrics.csv"


def test_schema_columns_present(test_data_path, expected_schema):
    """
    Contract Test: Asserts that all required columns defined in the schema
    are present in the actual dataset.
    """
    if not test_data_path.exists():
        pytest.fail(f"Dataset file not found at {test_data_path}. "
                    "Run the data pipeline (T009) to generate this file before running contract tests.")

    df = pd.read_csv(test_data_path)
    required_columns = set(expected_schema["columns"].keys())
    actual_columns = set(df.columns)

    missing_columns = required_columns - actual_columns
    extra_columns = actual_columns - required_columns

    assert missing_columns == set(), (
        f"Schema contract violation: Missing required columns: {missing_columns}. "
        f"Found extra columns: {extra_columns}."
    )


def test_schema_column_types(test_data_path, expected_schema):
    """
    Contract Test: Asserts that the data types of columns match the schema.
    """
    if not test_data_path.exists():
        pytest.skip(f"Dataset file not found at {test_data_path}. Skipping type validation.")

    df = pd.read_csv(test_data_path)
    schema_types = expected_schema["columns"]

    for col_name, col_spec in schema_types.items():
        if col_name not in df.columns:
            continue  # Already covered by column presence test

        expected_dtype = col_spec["type"]
        actual_dtype = str(df[col_name].dtype)

        # Map pandas dtypes to expected schema types
        # schema usually expects: 'int64', 'float64', 'object', 'bool'
        dtype_map = {
            'int': 'int64',
            'float': 'float64',
            'str': 'object',
            'object': 'object',
            'int64': 'int64',
            'float64': 'float64',
            'bool': 'bool'
        }

        # Normalize expected type
        expected_normalized = dtype_map.get(expected_dtype.lower(), expected_dtype.lower())
        actual_normalized = actual_dtype

        # Special handling for string columns which might be 'object' in pandas
        if expected_normalized == 'object' and actual_normalized == 'object':
            continue
        if expected_normalized == 'int64' and actual_normalized.startswith('int'):
            continue
        if expected_normalized == 'float64' and actual_normalized.startswith('float'):
            continue

        assert expected_normalized == actual_normalized, (
            f"Schema contract violation: Column '{col_name}' has type '{actual_normalized}', "
            f"expected '{expected_normalized}'."
        )


def test_schema_no_nulls_in_critical_fields(test_data_path, expected_schema):
    """
    Contract Test: Asserts that critical fields (kloc, cve_count, unique_authors)
    contain no null values.
    """
    if not test_data_path.exists():
        pytest.skip(f"Dataset file not found at {test_data_path}. Skipping null check.")

    df = pd.read_csv(test_data_path)
    critical_columns = [
        col for col, spec in expected_schema["columns"].items()
        if spec.get("nullable") is False
    ]

    for col in critical_columns:
        if col not in df.columns:
            continue

        null_count = df[col].isna().sum()
        assert null_count == 0, (
            f"Schema contract violation: Column '{col}' contains {null_count} null values. "
            f"Schema defines this column as non-nullable."
        )


def test_validate_dataframe_function(test_data_path, expected_schema):
    """
    Contract Test: Validates the helper function `validate_dataframe` from schemas.py
    against the actual data.
    """
    if not test_data_path.exists():
        pytest.skip(f"Dataset file not found at {test_data_path}. Skipping helper validation.")

    df = pd.read_csv(test_data_path)
    
    # This should raise ValueError if validation fails, or return True/None if it passes
    # depending on the implementation of validate_dataframe.
    # Based on typical contract test patterns, we expect it to either return True 
    # or raise an exception. Let's assume it returns True on success.
    
    try:
        result = validate_dataframe(df, expected_schema)
        # If the function returns a boolean, assert it is True
        if isinstance(result, bool):
            assert result is True, "validate_dataframe returned False for valid schema."
        # If it returns None on success, we are good.
    except ValueError as e:
        pytest.fail(f"validate_dataframe raised ValueError: {e}")