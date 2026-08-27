"""
Unit tests for the Sensitivity Analysis module (Task T031).
"""
import pytest
import pandas as pd
import numpy as np
import os
import tempfile
from pathlib import Path

# Import the functions to test
# Note: Adjust import path if running from project root vs code dir
try:
    from sensitivity_analysis import (
        load_power_results,
        find_inflection_point,
        get_factor_for_resolution,
        get_nearest_valid_resolution,
        run_sensitivity_sweep,
        write_sensitivity_report,
        VALID_FACTORS
    )
except ImportError:
    # Fallback for different execution contexts
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))
    from sensitivity_analysis import (
        load_power_results,
        find_inflection_point,
        get_factor_for_resolution,
        get_nearest_valid_resolution,
        run_sensitivity_sweep,
        write_sensitivity_report,
        VALID_FACTORS
    )

@pytest.fixture
def sample_power_data():
    """Create a mock power results DataFrame."""
    data = {
        'resolution': ['30m', '60m', '120m', '240m', '480m'],
        'factor': [1, 2, 4, 8, 16],
        'moran_i': [0.85, 0.82, 0.78, 0.65, 0.50],
        'p_value': [0.001, 0.002, 0.01, 0.04, 0.10],
        'power': [0.99, 0.95, 0.85, 0.70, 0.40] # Inflection at 240m (factor 8)
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_csv_file(sample_power_data):
    """Create a temporary CSV file with sample data."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        sample_power_data.to_csv(f, index=False)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

def test_load_power_results(temp_csv_file):
    """Test loading power results from CSV."""
    df = load_power_results(temp_csv_file)
    assert df is not None
    assert 'power' in df.columns
    assert 'factor' in df.columns
    assert len(df) == 5

def test_find_inflection_point(sample_power_data):
    """Test identifying the inflection point (power < 0.80)."""
    # In sample data, 120m (factor 4) has power 0.85, 240m (factor 8) has 0.70
    # First below 0.80 is factor 8
    factor = find_inflection_point(sample_power_data)
    assert factor == 8

def test_get_factor_for_resolution():
    """Test conversion of resolution string to factor."""
    assert get_factor_for_resolution("30m") == 1
    assert get_factor_for_resolution("120m") == 4
    assert get_factor_for_resolution("480m") == 16
    assert get_factor_for_resolution("invalid") == -1

def test_get_nearest_valid_resolution():
    """Test mapping arbitrary factors to nearest valid geometric step."""
    # 1.0 -> 1
    assert get_nearest_valid_resolution(1.0) == 1
    # 1.1 -> 1 (closer to 1 than 2)
    assert get_nearest_valid_resolution(1.1) == 1
    # 1.5 -> 2 (closer to 2 than 1)
    assert get_nearest_valid_resolution(1.5) == 2
    # 3.0 -> 4 (closer to 4 than 2)
    assert get_nearest_valid_resolution(3.0) == 4
    # 10.0 -> 8 (closer to 8 than 16)
    assert get_nearest_valid_resolution(10.0) == 8

def test_run_sensitivity_sweep(temp_csv_file):
    """Test the full sensitivity sweep logic."""
    results = run_sensitivity_sweep(temp_csv_file)
    
    assert results['status'] in ['success', 'unstable']
    assert 'inflection_factor' in results
    assert 'max_shift_steps' in results
    assert 'is_stable' in results
    assert 'details' in results
    
    # With our sample data (inflection at 8), a +/- 10% sweep (7.2 to 8.8)
    # should map to factors 8 (7.2->8, 8.8->8) or potentially 4/16 if edges are hit.
    # Given 8 is the inflection, and 4 is above threshold, 16 is below.
    # If the sweep stays near 8, the threshold (first below 0.8) should remain 8.
    # Max shift should be 0 or 1.
    assert results['max_shift_steps'] <= 1

def test_write_sensitivity_report(temp_csv_file):
    """Test writing the sensitivity report to disk."""
    results = run_sensitivity_sweep(temp_csv_file)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test_report.txt")
        written_path = write_sensitivity_report(results, output_path)
        
        assert os.path.exists(written_path)
        with open(written_path, 'r') as f:
            content = f.read()
            assert "Sensitivity Analysis Report" in content
            assert "Stability Check" in content
            assert "CONCLUSION" in content