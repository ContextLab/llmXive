"""
Unit tests for schema_utils.py.

Verifies that the schema contract is correctly defined, saved, and validated.
"""
import os
import sys
import pytest
import pandas as pd
import json
from pathlib import Path

# Add code directory to path for imports
code_dir = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

from utils.schema_utils import (
    validate_per_sample_errors,
    save_schema_contract,
    create_empty_schema_example,
    REQUIRED_COLUMNS,
    PER_SAMPLE_ERRORS_SCHEMA
)

class TestSchemaValidation:
    def test_validate_valid_dataframe(self):
        """Test that a valid DataFrame passes validation."""
        df = create_empty_schema_example()
        # Add one valid row
        new_row = {
            "sample_id": "123",
            "method": "GPR",
            "prediction": 1.5,
            "lower_bound": 1.0,
            "upper_bound": 2.0,
            "ground_truth": 1.6,
            "dataset": "OQMD"
        }
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        
        assert validate_per_sample_errors(df) is True

    def test_validate_missing_columns(self):
        """Test that a DataFrame with missing columns fails validation."""
        df = pd.DataFrame({
            "sample_id": ["1"],
            "method": ["GPR"],
            "prediction": [1.5],
            # Missing other columns
        })
        
        assert validate_per_sample_errors(df) is False

    def test_validate_invalid_types(self):
        """Test that a DataFrame with invalid types fails validation."""
        df = pd.DataFrame({
            "sample_id": ["1"],
            "method": ["GPR"],
            "prediction": ["not_a_number"],  # Should be float
            "lower_bound": [1.0],
            "upper_bound": [2.0],
            "ground_truth": [1.6],
            "dataset": ["OQMD"]
        })
        
        # This should fail because prediction is string and cannot be converted
        assert validate_per_sample_errors(df) is False

class TestSchemaContract:
    def test_save_schema_contract(self, tmp_path):
        """Test that the schema contract is saved correctly."""
        output_path = tmp_path / "test_schema.json"
        result_path = save_schema_contract(str(output_path))
        
        assert os.path.exists(result_path)
        
        with open(result_path, 'r') as f:
            data = json.load(f)
        
        assert data["name"] == "per_sample_errors"
        assert len(data["columns"]) == len(REQUIRED_COLUMNS)
        assert data["required_columns"] == REQUIRED_COLUMNS

    def test_schema_columns_match(self):
        """Test that the defined schema matches the required columns."""
        schema_cols = list(PER_SAMPLE_ERRORS_SCHEMA.keys())
        assert schema_cols == REQUIRED_COLUMNS

class TestEmptySchemaExample:
    def test_create_empty_schema_example(self):
        """Test that an empty DataFrame is created with correct columns."""
        df = create_empty_schema_example()
        
        assert list(df.columns) == REQUIRED_COLUMNS
        assert len(df) == 0
        
        # Check dtypes
        assert df["prediction"].dtype == 'float64'
        assert df["lower_bound"].dtype == 'float64'
        assert df["upper_bound"].dtype == 'float64'
        assert df["ground_truth"].dtype == 'float64'
        assert df["sample_id"].dtype == 'object'
        assert df["method"].dtype == 'object'
        assert df["dataset"].dtype == 'object'