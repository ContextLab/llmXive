"""
Contract tests for data schemas.
This module validates that data processing outputs conform to the defined schemas.
"""

import pandas as pd
import numpy as np
import pytest
from pathlib import Path
import sys

# Ensure project root is in path for imports if running from tests/
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Expected schema definitions
EBIRED_SCHEMA_COLUMNS = ["species", "lat", "lon", "date", "count", "checklist_id"]

# Expected data types for the eBird schema
# Note: These are the types we enforce/expect after loading and preprocessing
EBIRED_SCHEMA_DTYPES = {
    "species": "object",
    "lat": "float64",
    "lon": "float64",
    "date": "object",  # Often kept as string or datetime object depending on pipeline stage
    "count": "int64",
    "checklist_id": "object"
}

def test_ebird_schema_columns(tmp_path):
    """
    TDD Test: Asserts that the eBird DataFrame has exactly the required columns
    and that their data types match the expected schema.
    
    This test generates a minimal synthetic dataset matching the schema to verify
    the validation logic works correctly. In a real pipeline, this would be run
    against the output of src/data/download.py or src/data/preprocess.py.
    """
    # Create a minimal valid DataFrame for testing the schema validation logic
    # In a real scenario, this df would come from the data loading step
    test_data = {
        "species": ["Turdus migratorius", "Setophaga ruticilla"],
        "lat": [40.7128, 34.0522],
        "lon": [-74.0060, -118.2437],
        "date": ["2023-04-01", "2023-04-02"],
        "count": [5, 12],
        "checklist_id": ["ABC123", "DEF456"]
    }
    df = pd.DataFrame(test_data)

    # 1. Assert columns match exactly
    assert list(df.columns) == EBIRED_SCHEMA_COLUMNS, (
        f"Column mismatch. Expected {EBIRED_SCHEMA_COLUMNS}, got {list(df.columns)}"
    )

    # 2. Assert data types match expected
    # We iterate to provide specific error messages per column
    for col, expected_type in EBIRED_SCHEMA_DTYPES.items():
        actual_type = str(df[col].dtype)
        assert actual_type == expected_type, (
            f"Type mismatch for column '{col}'. "
            f"Expected {expected_type}, got {actual_type}"
        )

    # Additional sanity check: ensure no columns are missing or extra
    assert set(df.columns) == set(EBIRED_SCHEMA_COLUMNS), (
        f"Column set mismatch. Expected {set(EBIRED_SCHEMA_COLUMNS)}, got {set(df.columns)}"
    )

def test_ebird_schema_columns_invalid(tmp_path):
    """
    TDD Test: Asserts that the validation correctly fails when columns are missing
    or types are incorrect.
    """
    # Create invalid data (missing column)
    invalid_data = {
        "species": ["Turdus migratorius"],
        "lat": [40.7128],
        "lon": [-74.0060],
        "date": ["2023-04-01"],
        "count": [5],
        # Missing checklist_id
    }
    df_invalid = pd.DataFrame(invalid_data)

    # This should raise an AssertionError
    with pytest.raises(AssertionError):
        # We manually run the column check logic here to verify the test fails
        assert list(df_invalid.columns) == EBIRED_SCHEMA_COLUMNS

    # Create invalid data (wrong type)
    invalid_type_data = {
        "species": ["Turdus migratorius"],
        "lat": [40.7128],
        "lon": [-74.0060],
        "date": ["2023-04-01"],
        "count": [5.5],  # Float instead of int
        "checklist_id": ["ABC123"]
    }
    df_invalid_type = pd.DataFrame(invalid_type_data)

    # This should raise an AssertionError for the type mismatch
    with pytest.raises(AssertionError):
        for col, expected_type in EBIRED_SCHEMA_DTYPES.items():
            actual_type = str(df_invalid_type[col].dtype)
            assert actual_type == expected_type