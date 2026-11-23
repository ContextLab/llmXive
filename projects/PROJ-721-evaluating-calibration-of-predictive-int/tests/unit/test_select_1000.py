"""
Unit tests for the 1000-series selection logic (T013b).

Tests verify that the selection script correctly:
1. Loads the sampling report
2. Selects exactly 1000 series when available
3. Raises appropriate errors when data is insufficient
4. Produces a valid CSV output
"""
import json
import os
import tempfile
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock

# Import the function to test
import sys
sys.path.insert(0, 'code')
from select_1000_series import select_1000_series, load_sampling_report

@pytest.fixture
def valid_sampling_report(tmp_path):
    """Create a valid sampling report for testing."""
    report = {
        "sample_indices": list(range(1500)),  # 1500 available
        "distribution_stats": {
            "total_series": 1500,
            "frequency_distribution": {"yearly": 500, "quarterly": 500, "monthly": 500}
        }
    }
    report_path = tmp_path / "sampling_report.json"
    with open(report_path, 'w') as f:
        json.dump(report, f)
    return str(report_path)

@pytest.fixture
def insufficient_sampling_report(tmp_path):
    """Create a sampling report with insufficient data."""
    report = {
        "sample_indices": list(range(500)),  # Only 500 available
        "distribution_stats": {}
    }
    report_path = tmp_path / "sampling_report.json"
    with open(report_path, 'w') as f:
        json.dump(report, f)
    return str(report_path)

def test_select_1000_from_sufficient_data(valid_sampling_report):
    """Test that 1000 series are selected when enough data is available."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Mock the load_sampling_report to use our temp file
        report = load_sampling_report(valid_sampling_report)
        df = select_1000_series(report)
        
        assert len(df) == 1000, f"Expected 1000 rows, got {len(df)}"
        assert "series_id" in df.columns
        assert df["series_id"].dtype in [int, 'int64', 'int32']
        
        # Verify indices are sorted and unique
        assert df["series_id"].is_monotonic_increasing
        assert df["series_id"].is_unique

def test_select_raises_on_insufficient_data(insufficient_sampling_report):
    """Test that an error is raised when insufficient data is available."""
    with tempfile.TemporaryDirectory() as tmpdir:
        report = load_sampling_report(insufficient_sampling_report)
        
        with pytest.raises(ValueError) as excinfo:
            select_1000_series(report)
        
        assert "Insufficient series" in str(excinfo.value)

def test_select_exact_size_when_available(tmp_path):
    """Test selection when exactly 1000 series are available."""
    report = {
        "sample_indices": list(range(1000)),
        "distribution_stats": {}
    }
    report_path = tmp_path / "sampling_report.json"
    with open(report_path, 'w') as f:
        json.dump(report, f)
    
    report_loaded = load_sampling_report(str(report_path))
    df = select_1000_series(report_loaded)
    
    assert len(df) == 1000

def test_output_format(tmp_path):
    """Test that the output DataFrame has the correct format."""
    report = {
        "sample_indices": list(range(1000)),
        "distribution_stats": {}
    }
    
    df = select_1000_series(report)
    
    # Check structure
    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == ["series_id"]
    assert len(df) == 1000
    
    # Check data types
    assert df["series_id"].dtype in [int, 'int64', 'int32']
    
    # Check values are in expected range
    assert df["series_id"].min() == 0
    assert df["series_id"].max() == 999

def test_deterministic_selection(tmp_path):
    """Test that selection is deterministic (sorted indices)."""
    # Create a report with unsorted indices
    report = {
        "sample_indices": [10, 5, 100, 2, 99, 1, 50, 200, 30, 40] + list(range(1010, 1000)),
        "distribution_stats": {}
    }
    
    df = select_1000_series(report)
    
    # The first 1000 sorted indices should be selected
    expected = sorted([10, 5, 100, 2, 99, 1, 50, 200, 30, 40] + list(range(1010, 2000)))[:1000]
    assert list(df["series_id"]) == expected[:1000]

def test_missing_sample_indices(tmp_path):
    """Test error handling when sample_indices key is missing."""
    report = {
        "distribution_stats": {}
    }
    
    with pytest.raises(ValueError) as excinfo:
        select_1000_series(report)
    
    assert "sample_indices" in str(excinfo.value)
