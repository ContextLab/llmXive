import os
import tempfile
import pandas as pd
import pytest
from analysis.schema_validator import validate_schema, REQUIRED_COLUMNS

def test_validate_schema_valid_file():
    """Test that a valid CSV with all required columns passes validation."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        # Create a minimal valid dataset
        data = {col: [1.0 if col in ["beta", "beta_value", "ate", "bias", "rmse", "coverage_rate", "ground_truth_ate"] else "test" 
                      for col in REQUIRED_COLUMNS] for _ in range(1)}
        # Fix specific columns to be numeric where needed
        data["beta"] = [0.5]
        data["beta_value"] = [0.5]
        data["ate"] = [1.0]
        data["bias"] = [0.1]
        data["rmse"] = [0.2]
        data["coverage_rate"] = [0.95]
        data["ground_truth_ate"] = [1.0]
        data["seed"] = [42]
        data["run_id"] = ["hash123"]
        data["status"] = ["ok"]
        
        df = pd.DataFrame(data)
        df.to_csv(f.name, index=False)
        temp_path = f.name

    try:
        result = validate_schema(temp_path)
        assert result is True
    finally:
        os.unlink(temp_path)

def test_validate_schema_missing_columns():
    """Test that a CSV with missing columns raises ValueError."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        # Create a dataset missing a required column
        data = {col: [1.0] for col in REQUIRED_COLUMNS - {"beta"}}
        df = pd.DataFrame(data)
        df.to_csv(f.name, index=False)
        temp_path = f.name

    try:
        with pytest.raises(ValueError) as exc_info:
            validate_schema(temp_path)
        assert "Missing required columns" in str(exc_info.value)
    finally:
        os.unlink(temp_path)

def test_validate_schema_file_not_found():
    """Test that a non-existent file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        validate_schema("/non/existent/path.csv")

def test_validate_schema_null_critical_values():
    """Test that a CSV with null values in critical columns raises ValueError."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        data = {col: [1.0 if col in ["beta", "beta_value", "bias", "rmse", "coverage_rate", "ground_truth_ate"] else "test" 
                      for col in REQUIRED_COLUMNS]}
        data["ate"] = [None]  # Null in critical column
        df = pd.DataFrame(data)
        df.to_csv(f.name, index=False)
        temp_path = f.name

    try:
        with pytest.raises(ValueError) as exc_info:
            validate_schema(temp_path)
        assert "contains null values" in str(exc_info.value)
    finally:
        os.unlink(temp_path)