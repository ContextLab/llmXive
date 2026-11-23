"""
Tests for the sensitivity analysis script (T027c).
"""

import os
import json
import tempfile
import csv
import pytest
from pathlib import Path

# Add parent directory to path for imports
sys_path = str(Path(__file__).parent.parent)
if sys_path not in os.sys.path:
    os.sys.path.insert(0, sys_path)

from sensitivity_analysis import (
    load_simulation_results,
    calculate_correlation_for_threshold,
    run_sensitivity_analysis
)

# Test fixtures
@pytest.fixture
def sample_csv_data():
    """Generate a temporary CSV file with valid simulation data."""
    data = [
        {'topology_id': '1', 'p': '0.00', 'kc_binary': '1.50', 'kc_linear': '1.51', 'status': 'success'},
        {'topology_id': '2', 'p': '0.02', 'kc_binary': '1.48', 'kc_linear': '1.49', 'status': 'success'},
        {'topology_id': '3', 'p': '0.05', 'kc_binary': '1.45', 'kc_linear': '1.46', 'status': 'success'},
        {'topology_id': '4', 'p': '0.10', 'kc_binary': '1.40', 'kc_linear': '1.41', 'status': 'success'},
        {'topology_id': '5', 'p': '0.20', 'kc_binary': '1.30', 'kc_linear': '1.31', 'status': 'success'},
        {'topology_id': '6', 'p': '0.30', 'kc_binary': '1.20', 'kc_linear': '1.21', 'status': 'success'},
        {'topology_id': '7', 'p': '0.40', 'kc_binary': '1.10', 'kc_linear': '1.11', 'status': 'success'},
        {'topology_id': '8', 'p': '0.50', 'kc_binary': '1.00', 'kc_linear': '1.01', 'status': 'success'},
        {'topology_id': '9', 'p': '0.60', 'kc_binary': '0.90', 'kc_linear': '0.91', 'status': 'success'},
        {'topology_id': '10', 'p': '0.80', 'kc_binary': '0.70', 'kc_linear': '0.71', 'status': 'success'},
    ]
    return data

@pytest.fixture
def temp_csv_file(sample_csv_data):
    """Create a temporary CSV file with sample data."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=sample_csv_data[0].keys())
        writer.writeheader()
        writer.writerows(sample_csv_data)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

@pytest.fixture
def temp_output_file():
    """Create a temporary path for output."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as f:
        temp_path = f.name
    yield temp_path
    if os.path.exists(temp_path):
        os.unlink(temp_path)

def test_load_simulation_results(temp_csv_file):
    """Test loading simulation results from CSV."""
    results = load_simulation_results(temp_csv_file)
    assert len(results) == 10
    assert results[0]['topology_id'] == '1'
    assert results[0]['p'] == 0.00
    assert results[0]['kc_binary'] == 1.50
    assert results[0]['status'] == 'success'

def test_load_simulation_results_missing_file():
    """Test loading from a non-existent file."""
    with pytest.raises(FileNotFoundError):
        load_simulation_results("non_existent_file.csv")

def test_calculate_correlation_for_threshold(temp_csv_file):
    """Test correlation calculation for a single threshold."""
    results = load_simulation_results(temp_csv_file)
    result = calculate_correlation_for_threshold(results, 0.5)

    assert 'threshold' in result
    assert 'correlation_coef' in result
    assert 'p_value' in result
    assert result['threshold'] == 0.5
    assert isinstance(result['correlation_coef'], float)
    assert isinstance(result['p_value'], float)
    # With the synthetic data (p increasing, Kc decreasing), we expect a negative correlation
    assert result['correlation_coef'] < 0

def test_run_sensitivity_analysis(temp_csv_file, temp_output_file):
    """Test the full sensitivity analysis sweep."""
    run_sensitivity_analysis(temp_csv_file, temp_output_file)

    assert os.path.exists(temp_output_file)
    with open(temp_output_file, 'r') as f:
        data = json.load(f)

    assert isinstance(data, list)
    assert len(data) == 3  # 0.4, 0.5, 0.6
    thresholds = {row['threshold'] for row in data}
    assert thresholds == {0.4, 0.5, 0.6}
    for row in data:
        assert 'correlation_coef' in row
        assert 'p_value' in row

def test_run_sensitivity_analysis_empty_results(temp_output_file):
    """Test handling of insufficient data."""
    # Create a CSV with only 2 rows (insufficient for correlation)
    data = [
        {'topology_id': '1', 'p': '0.00', 'kc_binary': '1.50', 'kc_linear': '1.51', 'status': 'success'},
        {'topology_id': '2', 'p': '0.02', 'kc_binary': '1.48', 'kc_linear': '1.49', 'status': 'success'},
    ]
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
        temp_path = f.name

    try:
        run_sensitivity_analysis(temp_path, temp_output_file)
        with open(temp_output_file, 'r') as f:
            results = json.load(f)
        # Should return 0.0 correlation and 1.0 p-value for insufficient data
        for row in results:
            assert row['correlation_coef'] == 0.0
            assert row['p_value'] == 1.0
    finally:
        os.unlink(temp_path)