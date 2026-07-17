"""
Contract tests for the multiplicity table schema (results/statistics/multiplicity_table.csv).
"""
import os
import csv
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_PATH = PROJECT_ROOT / "results" / "statistics" / "multiplicity_table.csv"

REQUIRED_COLUMNS = [
    "test_name",
    "raw_p",
    "adjusted_p",
    "metric_pair"
]

def test_multiplicity_table_exists():
    """Test that the multiplicity table file exists."""
    assert DATA_PATH.exists(), f"Multiplicity table file not found: {DATA_PATH}"

def test_multiplicity_table_headers():
    """Test that the multiplicity table file has the required columns."""
    if not DATA_PATH.exists():
        pytest.skip("Multiplicity table file not found.")
    
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        headers = next(reader)
    
    missing_columns = set(REQUIRED_COLUMNS) - set(headers)
    assert not missing_columns, f"Missing required columns in multiplicity_table.csv: {missing_columns}"

def test_multiplicity_table_data_types():
    """Test that data types in multiplicity table are correct."""
    if not DATA_PATH.exists():
        pytest.skip("Multiplicity table file not found.")
    
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Check numeric fields
            try:
                float(row["raw_p"])
                float(row["adjusted_p"])
            except ValueError:
                pytest.fail(f"Invalid numeric value in row: {row}")
            
            # Check string fields
            assert row["test_name"], "test_name cannot be empty"
            assert row["metric_pair"], "metric_pair cannot be empty"