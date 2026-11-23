"""
Unit test for T049c: write_scaling_results.
Verifies that the scaling_law.csv is created with correct columns and valid data.
"""
import pytest
import os
import csv
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.experiments.scaling import ScalingResult, write_scaling_results, DATA_RESULTS_DIR

@pytest.fixture
def mock_results():
    """Create mock ScalingResult objects."""
    return [
        ScalingResult(
            config_name="scaling_1x",
            column_count=1,
            total_params=1000,
            mae=0.05,
            time_sec=10.5,
            success=True
        ),
        ScalingResult(
            config_name="scaling_2x",
            column_count=2,
            total_params=2000,
            mae=0.04,
            time_sec=21.0,
            success=True
        ),
        ScalingResult(
            config_name="scaling_4x",
            column_count=4,
            total_params=4000,
            mae=0.03,
            time_sec=42.5,
            success=True
        ),
        ScalingResult(
            config_name="scaling_fail",
            column_count=8,
            total_params=0,
            mae=-1.0,
            time_sec=0.0,
            success=False
        )
    ]

@pytest.fixture
def temp_output_path(tmp_path):
    return str(tmp_path / "test_scaling_law.csv")

def test_write_scaling_results_creates_file(mock_results, temp_output_path):
    """Test that the function creates the CSV file."""
    result = write_scaling_results(mock_results, output_path=temp_output_path)
    assert result is True
    assert os.path.exists(temp_output_path)

def test_write_scaling_results_columns(mock_results, temp_output_path):
    """Test that the CSV has the correct columns."""
    write_scaling_results(mock_results, output_path=temp_output_path)
    with open(temp_output_path, 'r') as f:
        reader = csv.reader(f)
        header = next(reader)
        assert header == ['columns', 'params', 'mae', 'time_sec']

def test_write_scaling_results_data(mock_results, temp_output_path):
    """Test that the CSV contains the correct data rows."""
    write_scaling_results(mock_results, output_path=temp_output_path)
    with open(temp_output_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        # Should have 3 rows (one failed result is excluded)
        assert len(rows) == 3
        # Check first row
        assert int(rows[0]['columns']) == 1
        assert int(rows[0]['params']) == 1000
        assert float(rows[0]['mae']) == 0.05
        # Check last row
        assert int(rows[2]['columns']) == 4
        assert int(rows[2]['params']) == 4000

def test_write_scaling_results_filters_failures(mock_results, temp_output_path):
    """Test that failed results are not included in the CSV."""
    write_scaling_results(mock_results, output_path=temp_output_path)
    with open(temp_output_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        for row in rows:
            assert int(row['columns']) != 8  # The failed config
            assert float(row['mae']) > 0.0   # No negative MAEs

def test_write_scaling_results_empty_list(tmp_path):
    """Test behavior when no successful results are provided."""
    empty_results = []
    output_path = str(tmp_path / "empty.csv")
    result = write_scaling_results(empty_results, output_path=output_path)
    assert result is False
    # File might not be created or might be empty, but function returns False
    assert not os.path.exists(output_path) or os.path.getsize(output_path) == 0
