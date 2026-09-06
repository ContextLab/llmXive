import pandas as pd
import pytest
import numpy as np
import os
import tempfile
from pathlib import Path

# Import the function to test
from sensitivity import compute_pass_rates, load_fit_summary, CHI2_THRESHOLDS

@pytest.fixture
def sample_fit_data():
    """Create a sample DataFrame mimicking the output of T025."""
    data = {
        'galaxy_id': ['G1', 'G1', 'G2', 'G2', 'G3', 'G3'],
        'model': ['Mond', 'NFW', 'Mond', 'NFW', 'Mond', 'NFW'],
        'reduced_chi2': [1.1, 1.6, 0.9, 1.8, 1.3, 1.2]
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_fit_csv(sample_fit_data):
    """Create a temporary CSV file for load_fit_summary tests."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        sample_fit_data.to_csv(f, index=False)
        return f.name

def test_compute_pass_rates_mond_threshold_1_0(sample_fit_data):
    """Test pass rate calculation for Mond model at threshold 1.0."""
    # Mond values: 1.1 (fail), 0.9 (pass), 1.3 (fail) -> 1/3 pass
    results = compute_pass_rates(sample_fit_data, [1.0])
    
    mond_row = results[results['model'] == 'Mond'].iloc[0]
    assert mond_row['chi2_threshold'] == 1.0
    assert mond_row['passes'] == 1
    assert mond_row['total_galaxies'] == 3
    assert np.isclose(mond_row['pass_rate'], 1/3)

def test_compute_pass_rates_nfw_threshold_1_5(sample_fit_data):
    """Test pass rate calculation for NFW model at threshold 1.5."""
    # NFW values: 1.6 (fail), 1.8 (fail), 1.2 (pass) -> 1/3 pass
    results = compute_pass_rates(sample_fit_data, [1.5])
    
    nfw_row = results[results['model'] == 'NFW'].iloc[0]
    assert nfw_row['chi2_threshold'] == 1.5
    assert nfw_row['passes'] == 1
    assert nfw_row['total_galaxies'] == 3
    assert np.isclose(nfw_row['pass_rate'], 1/3)

def test_compute_pass_rates_multiple_thresholds(sample_fit_data):
    """Test that multiple thresholds are processed correctly."""
    results = compute_pass_rates(sample_fit_data, [1.0, 1.5])
    
    assert len(results) == 4 # 2 models * 2 thresholds
    
    # Check Mond at 1.5: 1.1 (pass), 0.9 (pass), 1.3 (pass) -> 3/3
    mond_15 = results[(results['model'] == 'Mond') & (results['chi2_threshold'] == 1.5)].iloc[0]
    assert mond_15['passes'] == 3
    assert mond_15['pass_rate'] == 1.0

def test_load_fit_summary_missing_file():
    """Test that load_fit_summary raises FileNotFoundError for missing files."""
    with pytest.raises(FileNotFoundError):
        load_fit_summary("/nonexistent/path/file.csv")

def test_load_fit_summary_missing_columns(temp_fit_csv):
    """Test that load_fit_summary raises ValueError if columns are missing."""
    # Create a CSV with wrong columns
    wrong_data = pd.DataFrame({'id': [1], 'val': [2]})
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        wrong_data.to_csv(f, index=False)
        wrong_path = f.name
    
    try:
        with pytest.raises(ValueError):
            load_fit_summary(wrong_path)
    finally:
        os.unlink(wrong_path)

def test_chi2_thresholds_defined():
    """Verify that the required thresholds from SC-006 are present."""
    expected = [1.0, 1.25, 1.5, 1.75]
    assert CHI2_THRESHOLDS == expected, f"CHI2_THRESHOLDS must be {expected}"
