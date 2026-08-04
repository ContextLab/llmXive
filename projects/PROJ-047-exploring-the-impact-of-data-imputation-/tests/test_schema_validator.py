"""
Tests for code/analysis/schema_validator.py
"""
import os
import tempfile
import pandas as pd
import pytest
from unittest.mock import patch
import sys
import io

# Import the module to test
# We assume the package structure is set up correctly (code/ is in sys.path or we run from code/)
# For the test runner, we assume 'analysis' is importable.
from analysis.schema_validator import validate_schema, REQUIRED_COLUMNS

class TestSchemaValidation:
    """Tests for schema validation logic."""

    def test_validate_schema_missing_file(self):
        """Test that a non-existent file raises ValueError."""
        with pytest.raises(ValueError, match="File not found"):
            validate_schema("data/results/non_existent_file.csv")

    def test_validate_schema_empty_csv(self):
        """Test that an empty CSV file raises ValueError."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("") # Empty file
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="empty"):
                validate_schema(temp_path)
        finally:
            os.unlink(temp_path)

    def test_validate_schema_header_only(self):
        """Test that a CSV with headers but no data raises ValueError."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(",".join(REQUIRED_COLUMNS) + "\n")
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="empty"):
                validate_schema(temp_path)
        finally:
            os.unlink(temp_path)

    def test_validate_schema_missing_columns(self):
        """Test that a CSV with missing columns raises ValueError."""
        # Create a subset of required columns
        partial_columns = REQUIRED_COLUMNS[:-1] 
        missing_col = REQUIRED_COLUMNS[-1]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(",".join(partial_columns) + "\n")
            f.write("0.0,mean,ipw,1.0,0.0,0.0,0.95,42,hash123,0.5,0.0,success\n")
            temp_path = f.name

        try:
            with pytest.raises(ValueError) as exc_info:
                validate_schema(temp_path)
            assert missing_col in str(exc_info.value)
        finally:
            os.unlink(temp_path)

    def test_validate_schema_success(self):
        """Test that a valid CSV passes validation."""
        # Create a valid CSV with all columns and at least one row
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(",".join(REQUIRED_COLUMNS) + "\n")
            # Write a dummy row
            row_data = [
                "0.0",       # beta
                "mean",      # method
                "ipw",       # estimator
                "1.0",       # ate
                "0.0",       # bias
                "0.0",       # rmse
                "0.95",      # coverage_rate
                "42",        # seed
                "hash123",   # run_id
                "0.5",       # ground_truth_ate
                "0.0",       # beta_value
                "success"    # status
            ]
            f.write(",".join(row_data) + "\n")
            temp_path = f.name

        try:
            # Should not raise
            result = validate_schema(temp_path)
            assert result is True
        finally:
            os.unlink(temp_path)

    def test_validate_schema_extra_columns(self):
        """Test that a CSV with extra columns passes validation."""
        extra_columns = REQUIRED_COLUMNS + ["extra_col", "another_col"]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(",".join(extra_columns) + "\n")
            row_data = ["0.0", "mean", "ipw", "1.0", "0.0", "0.0", "0.95", "42", "hash123", "0.5", "0.0", "success", "val1", "val2"]
            f.write(",".join(row_data) + "\n")
            temp_path = f.name

        try:
            result = validate_schema(temp_path)
            assert result is True
        finally:
            os.unlink(temp_path)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])