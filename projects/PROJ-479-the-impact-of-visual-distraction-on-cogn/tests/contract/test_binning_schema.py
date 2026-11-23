"""
Contract tests for the binning results schema (results/sensitivity/binning_results.csv).
"""
import os
import csv
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_PATH = PROJECT_ROOT / "results" / "sensitivity" / "binning_results.csv"

REQUIRED_COLUMNS = [
    "binning_strategy",
    "predictor",
    "outcome",
    "pearson_r",
    "p_value"
]

def test_binning_results_exists():
    """Test that the binning results file exists."""
    assert DATA_PATH.exists(), f"Binning results file not found: {DATA_PATH}"

def test_binning_results_headers():
    """Test that the binning results file has the required columns."""
    if not DATA_PATH.exists():
        pytest.skip("Binning results file not found.")
    
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        headers = next(reader)
    
    missing_columns = set(REQUIRED_COLUMNS) - set(headers)
    assert not missing_columns, f"Missing required columns in binning_results.csv: {missing_columns}"

def test_binning_results_data_types():
    """Test that data types in binning results are correct."""
    if not DATA_PATH.exists():
        pytest.skip("Binning results file not found.")
    
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Check numeric fields
            try:
                float(row["pearson_r"])
                float(row["p_value"])
            except ValueError:
                pytest.fail(f"Invalid numeric value in row: {row}")
            
            # Check string fields
            assert row["binning_strategy"], "binning_strategy cannot be empty"
            assert row["predictor"], "predictor cannot be empty"
            assert row["outcome"], "outcome cannot be empty"
