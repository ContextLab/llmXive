import os
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Import the schema utilities
# Assuming the test runs from project root, code/ is in path
import sys
sys.path.insert(0, 'code')
from utils.schema_utils import (
    PER_SAMPLE_ERRORS_SCHEMA,
    validate_per_sample_errors,
    save_schema_contract,
    create_empty_schema_example
)

def test_schema_columns_defined():
    """Verify that the schema defines the required columns."""
    expected_cols = {"sample_id", "method", "prediction", "lower_bound", "upper_bound", "ground_truth", "dataset"}
    assert set(PER_SAMPLE_ERRORS_SCHEMA["columns"]) == expected_cols

def test_validate_valid_dataframe():
    """Test validation with a correctly formatted DataFrame."""
    data = {
        "sample_id": ["s1", "s2"],
        "method": ["gpr", "mc_dropout"],
        "prediction": [1.5, 2.0],
        "lower_bound": [1.0, 1.8],
        "upper_bound": [2.0, 2.2],
        "ground_truth": [1.6, 2.1],
        "dataset": ["oqmd_bg", "oqmd_fe"]
    }
    df = pd.DataFrame(data)
    # Ensure dtypes match expectations
    df["prediction"] = df["prediction"].astype("float64")
    df["lower_bound"] = df["lower_bound"].astype("float64")
    df["upper_bound"] = df["upper_bound"].astype("float64")
    df["ground_truth"] = df["ground_truth"].astype("float64")
    
    assert validate_per_sample_errors(df) is True

def test_validate_missing_columns():
    """Test validation fails when columns are missing."""
    data = {
        "sample_id": ["s1"],
        "method": ["gpr"],
        "prediction": [1.5],
        # Missing lower_bound, upper_bound, ground_truth, dataset
    }
    df = pd.DataFrame(data)
    with pytest.raises(ValueError, match="Missing columns"):
        validate_per_sample_errors(df)

def test_validate_nan_values():
    """Test validation fails when critical numeric columns have NaN."""
    data = {
        "sample_id": ["s1"],
        "method": ["gpr"],
        "prediction": [np.nan],
        "lower_bound": [1.0],
        "upper_bound": [2.0],
        "ground_truth": [1.6],
        "dataset": ["oqmd_bg"]
    }
    df = pd.DataFrame(data)
    with pytest.raises(ValueError, match="contains NaN values"):
        validate_per_sample_errors(df)

def test_save_schema_contract_creates_file(tmp_path):
    """Test that save_schema_contract creates the JSON file."""
    output_dir = str(tmp_path)
    path = save_schema_contract(output_dir)
    assert os.path.exists(path)
    assert path.endswith("per_sample_errors_schema.json")

def test_create_empty_schema_example_creates_file(tmp_path):
    """Test that create_empty_schema_example creates the CSV file."""
    output_dir = str(tmp_path)
    path = create_empty_schema_example(output_dir)
    assert os.path.exists(path)
    assert path.endswith("per_sample_errors_schema_example.csv")
    
    # Verify headers
    df = pd.read_csv(path)
    assert set(df.columns) == set(PER_SAMPLE_ERRORS_SCHEMA["columns"])
    assert len(df) == 0
