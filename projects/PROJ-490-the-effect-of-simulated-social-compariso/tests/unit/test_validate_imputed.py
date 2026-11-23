"""
Unit tests for Post-Imputation Validation (T013b).
"""
import os
import json
import tempfile
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np
import pytest

from code.data.validate_imputed import validate_imputed_data, REQUIRED_COLUMNS
from code.utils.logger import configure_root_logger

# Configure logger for tests
configure_root_logger()

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)

@pytest.fixture
def valid_imputed_csv(temp_dir):
    """Creates a valid imputed CSV file."""
    data = {
        'participant_id': ['P1', 'P2', 'P3'],
        'pre_self_esteem': [20.0, 25.0, 22.0],
        'post_self_esteem': [22.0, 28.0, 24.0],
        'comparison_tendency': [10.0, 12.0, 11.0],
        'avatar_condition': [0, 1, 0]
    }
    df = pd.DataFrame(data)
    path = temp_dir / "imputed_data.csv"
    df.to_csv(path, index=False)
    return path

@pytest.fixture
def missing_cols_csv(temp_dir):
    """Creates a CSV missing a required column."""
    data = {
        'participant_id': ['P1', 'P2'],
        'pre_self_esteem': [20.0, 25.0],
        # Missing post_self_esteem
        'avatar_condition': [0, 1]
    }
    df = pd.DataFrame(data)
    path = temp_dir / "imputed_data.csv"
    df.to_csv(path, index=False)
    return path

@pytest.fixture
def nan_imputed_csv(temp_dir):
    """Creates a CSV with NaN values in required columns."""
    data = {
        'participant_id': ['P1', 'P2', 'P3'],
        'pre_self_esteem': [20.0, np.nan, 22.0],
        'post_self_esteem': [22.0, 28.0, 24.0],
        'comparison_tendency': [10.0, 12.0, 11.0],
        'avatar_condition': [0, 1, 0]
    }
    df = pd.DataFrame(data)
    path = temp_dir / "imputed_data.csv"
    df.to_csv(path, index=False)
    return path

def test_validation_passes_on_clean_data(valid_imputed_csv, temp_dir):
    """Test that validation passes when data is clean."""
    output_path = temp_dir / "validation.json"
    result = validate_imputed_data(valid_imputed_csv, output_path)

    assert result["status"] == "pass"
    assert result["imputation_success"] is True
    assert "error" not in result.get("details", {})

    # Verify file was written
    assert output_path.exists()
    with open(output_path) as f:
        saved = json.load(f)
    assert saved["status"] == "pass"

def test_validation_fails_on_missing_columns(missing_cols_csv, temp_dir):
    """Test that validation fails if required columns are missing."""
    output_path = temp_dir / "validation.json"
    result = validate_imputed_data(missing_cols_csv, output_path)

    assert result["status"] == "fail"
    assert result["imputation_success"] is False
    assert "missing_columns" in result["details"]
    assert "post_self_esteem" in result["details"]["missing_columns"]

def test_validation_fails_on_nan_values(nan_imputed_csv, temp_dir):
    """Test that validation fails if NaNs remain in required columns."""
    output_path = temp_dir / "validation.json"
    result = validate_imputed_data(nan_imputed_csv, output_path)

    assert result["status"] == "fail"
    assert result["imputation_success"] is False
    assert "nan_counts" in result["details"]
    assert result["details"]["nan_counts"]["pre_self_esteem"] == 1

def test_validation_fails_on_missing_file(temp_dir):
    """Test that validation fails if the input file does not exist."""
    fake_path = temp_dir / "non_existent.csv"
    output_path = temp_dir / "validation.json"
    
    result = validate_imputed_data(fake_path, output_path)

    assert result["status"] == "fail"
    assert result["imputation_success"] is False
    assert "error" in result["details"]
    assert "not found" in result["details"]["error"].lower()

def test_validation_handles_empty_dataframe(temp_dir):
    """Test validation on an empty CSV (headers only)."""
    path = temp_dir / "empty.csv"
    pd.DataFrame(columns=REQUIRED_COLUMNS).to_csv(path, index=False)
    output_path = temp_dir / "validation.json"

    result = validate_imputed_data(path, output_path)

    assert result["status"] == "fail"
    assert result["imputation_success"] is False