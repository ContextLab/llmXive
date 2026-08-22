"""
Unit tests for threshold_sweep_aggregator module.
"""
import csv
import json
import os
import tempfile
from pathlib import Path
import pytest

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from analysis.threshold_sweep_aggregator import (
    load_threshold_identification_raw,
    aggregate_sweep_results_to_csv
)

@pytest.fixture
def sample_raw_data():
    """Sample threshold identification raw data for testing."""
    return [
        {
            'N': 1000,
            'theta': 1.5,
            'outlier_probability': 0.0,
            'mean_max_eigenvalue': 2.01,
            'std_max_eigenvalue': 0.05,
            'num_runs': 10
        },
        {
            'N': 1000,
            'theta': 2.5,
            'outlier_probability': 1.0,
            'mean_max_eigenvalue': 2.85,
            'std_max_eigenvalue': 0.12,
            'num_runs': 10
        },
        {
            'N': 2000,
            'theta': 2.0,
            'outlier_probability': 0.5,
            'mean_max_eigenvalue': 2.35,
            'std_max_eigenvalue': 0.08,
            'num_runs': 20
        }
    ]

@pytest.fixture
def temp_json_file(sample_raw_data):
    """Create a temporary JSON file with sample data."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_raw_data, f)
        temp_path = Path(f.name)
    yield temp_path
    temp_path.unlink()

@pytest.fixture
def temp_csv_file():
    """Create a temporary CSV file path."""
    with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
        temp_path = Path(f.name)
    yield temp_path
    if temp_path.exists():
        temp_path.unlink()

def test_load_threshold_identification_raw(temp_json_file):
    """Test loading raw threshold identification data."""
    data = load_threshold_identification_raw(temp_json_file)
    assert len(data) == 3
    assert data[0]['N'] == 1000
    assert data[0]['theta'] == 1.5
    assert data[1]['outlier_probability'] == 1.0

def test_aggregate_sweep_results_to_csv(temp_json_file, temp_csv_file):
    """Test aggregation of results to CSV."""
    output_path = aggregate_sweep_results_to_csv(temp_json_file, temp_csv_file)

    assert output_path.exists()
    assert output_path == temp_csv_file

    # Read and verify CSV content
    with open(output_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 3
    assert rows[0]['N'] == '1000'
    assert rows[0]['theta'] == '1.5'
    assert rows[0]['outlier_probability'] == '0.0'
    assert rows[1]['outlier_probability'] == '1.0'
    assert rows[2]['N'] == '2000'

def test_aggregate_empty_results(temp_csv_file):
    """Test aggregation with empty results list."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump([], f)
        temp_json_path = Path(f.name)

    try:
        output_path = aggregate_sweep_results_to_csv(temp_json_path, temp_csv_file)
        assert output_path.exists()

        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 0
    finally:
        temp_json_path.unlink()

def test_file_not_found(temp_csv_file):
    """Test handling of missing input file."""
    non_existent = Path("/nonexistent/path/file.json")
    with pytest.raises(FileNotFoundError):
        load_threshold_identification_raw(non_existent)