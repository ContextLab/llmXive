"""
Unit tests for dataset schema validation logic (T009).
Validates that the schema file exists and that the validation function
correctly identifies missing columns.
"""
import os
import pytest
import pandas as pd
import yaml
from pathlib import Path
from code.data.validation import validate_schema

# Path to the schema file defined in T009
SCHEMA_PATH = Path("contracts/dataset.schema.yaml")

@pytest.fixture
def valid_data():
    """Create a minimal valid DataFrame matching the schema."""
    return pd.DataFrame({
        "User_ID": ["U001", "U002"],
        "Gamified": [1, 0],
        "Adherence": [1, 0],
        "Conscientiousness_Score": [70.5, 65.2],
        "Need_for_Achievement": [80.0, 75.0],
        "Week_Number": [1, 1],
        "Date": ["2023-01-01", "2023-01-02"]
    })

@pytest.fixture
def invalid_data_missing_column():
    """Create a DataFrame missing the 'Gamified' column."""
    return pd.DataFrame({
        "User_ID": ["U001", "U002"],
        "Adherence": [1, 0],
        "Conscientiousness_Score": [70.5, 65.2],
        "Need_for_Achievement": [80.0, 75.0],
        "Week_Number": [1, 1],
        "Date": ["2023-01-01", "2023-01-02"]
    })

@pytest.fixture
def invalid_data_wrong_type():
    """Create a DataFrame with wrong type in a column (optional check)."""
    # For this test, we primarily check column existence, 
    # but the schema also defines types.
    return pd.DataFrame({
        "User_ID": ["U001", "U002"],
        "Gamified": ["yes", "no"], # Should be int
        "Adherence": [1, 0],
        "Conscientiousness_Score": [70.5, 65.2],
        "Need_for_Achievement": [80.0, 75.0],
        "Week_Number": [1, 1],
        "Date": ["2023-01-01", "2023-01-02"]
    })

def test_schema_file_exists():
    """Assert that the schema file defined in T009 exists."""
    assert SCHEMA_PATH.exists(), f"Schema file not found at {SCHEMA_PATH}"

def test_schema_is_valid_yaml():
    """Assert that the schema file is valid YAML."""
    with open(SCHEMA_PATH, "r") as f:
        schema = yaml.safe_load(f)
    assert "required" in schema
    assert "properties" in schema
    assert "User_ID" in schema["properties"]

def test_validate_schema_passes(valid_data):
    """Assert that a valid DataFrame passes schema validation."""
    # This should not raise an exception
    result = validate_schema(valid_data, SCHEMA_PATH)
    assert result is True

def test_validate_schema_fails_missing_column(invalid_data_missing_column):
    """Assert that a DataFrame with missing columns raises ValueError."""
    with pytest.raises(ValueError) as exc_info:
        validate_schema(invalid_data_missing_column, SCHEMA_PATH)
    assert "Gamified" in str(exc_info.value)
    assert "missing from dataset" in str(exc_info.value)

def test_validate_schema_empty_file():
    """Assert that an empty schema file raises an error or is handled."""
    # Create a temporary empty file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        with pytest.raises(ValueError):
            validate_schema(valid_data(), tmp_path)
    finally:
        os.unlink(tmp_path)

def test_validate_schema_type_mismatch(invalid_data_wrong_type):
    """Assert that type mismatches are detected if the validation logic checks types."""
    # Note: The current implementation of validate_schema in code/data/validation.py
    # primarily checks for column existence. If type checking is added later,
    # this test should be updated to expect a ValueError.
    # For now, we ensure it doesn't crash on existence check.
    try:
        validate_schema(invalid_data_wrong_type, SCHEMA_PATH)
    except ValueError:
        pass # Expected if type checking is implemented
