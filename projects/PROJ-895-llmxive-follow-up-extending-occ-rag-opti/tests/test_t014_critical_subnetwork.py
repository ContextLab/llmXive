"""
Tests for T014: Critical Sub-network Identification.
"""

import os
import sys
import csv
import json
import tempfile
from pathlib import Path
import pytest

# Add code directory to path for imports
code_dir = Path(__file__).parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from code_01_sensitivity_analysis import identify_critical_subnetwork, load_sensitivity_results

@pytest.fixture
def mock_sensitivity_data():
    """Generates mock sensitivity data for testing."""
    data = []
    for i in range(100):
        data.append({
            'layer_id': i // 10,
            'param_id': f"layer_{i//10}.weight.{i}",
            'sensitivity_score': 0.5 + (i * 0.01),
            'delta_faithfulness': 0.1 + (i * 0.005), # Increasing delta
            'random_baseline_score': 0.8
        })
    return data

@pytest.fixture
def temp_sensitivity_csv(mock_sensitivity_data):
    """Creates a temporary CSV file with mock sensitivity data."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', newline='') as f:
        fieldnames = ['layer_id', 'param_id', 'sensitivity_score', 'delta_faithfulness', 'random_baseline_score']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in mock_sensitivity_data:
            writer.writerow(row)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

def test_identify_critical_subnetwork_retention(mock_sensitivity_data):
    """Test that the correct number of parameters are selected based on retention percentage."""
    retention_pct = 0.20 # 20%
    critical_params, stats = identify_critical_subnetwork(mock_sensitivity_data, retention_pct)

    expected_count = int(len(mock_sensitivity_data) * retention_pct)
    assert len(critical_params) == expected_count, f"Expected {expected_count} params, got {len(critical_params)}"
    assert stats['retained_count'] == expected_count

def test_identify_critical_subnetwork_sorting(mock_sensitivity_data):
    """Test that parameters are sorted by delta_faithfulness (descending)."""
    retention_pct = 0.50
    critical_params, _ = identify_critical_subnetwork(mock_sensitivity_data, retention_pct)

    # The last selected param should have a lower or equal delta than the first
    # Since our mock data has increasing delta, the last one in the top 50% should be the 50th item
    # and the first should be the 100th item.
    # Let's verify the list is sorted by delta descending
    deltas = [p['delta_faithfulness'] for p in critical_params]
    assert deltas == sorted(deltas, reverse=True), "Critical params must be sorted by delta_faithfulness descending"

def test_identify_critical_subnetwork_empty_input():
    """Test handling of empty input."""
    with pytest.raises(ValueError, match="Sensitivity results list is empty."):
        identify_critical_subnetwork([], 0.5)

def test_identify_critical_subnetwork_zero_retention(mock_sensitivity_data):
    """Test handling of 0% retention."""
    critical_params, stats = identify_critical_subnetwork(mock_sensitivity_data, 0.0)
    assert len(critical_params) == 0
    assert stats['retained_count'] == 0

def test_load_sensitivity_results(temp_sensitivity_csv):
    """Test loading sensitivity results from a real CSV file."""
    results = load_sensitivity_results(Path(temp_sensitivity_csv))
    assert len(results) == 100
    assert results[0]['layer_id'] == 0
    assert isinstance(results[0]['sensitivity_score'], float)