import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

# Import the functions to test
from sensitivity import load_fit_summary, compute_pass_rates, CHI2_THRESHOLDS

def test_load_fit_summary_valid():
    """Test loading a valid fit summary CSV."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("galaxy_id,model,reduced_chi2\n")
        f.write("NGC1001,mond,0.8\n")
        f.write("NGC1001,nfw,1.2\n")
        f.write("NGC1002,mond,1.1\n")
        temp_path = f.name

    try:
        df = load_fit_summary(temp_path)
        assert len(df) == 3
        assert set(df['model'].unique()) == {'mond', 'nfw'}
        assert 'reduced_chi2' in df.columns
    finally:
        os.unlink(temp_path)

def test_load_fit_summary_missing_file():
    """Test that loading a missing file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_fit_summary("/nonexistent/path/file.csv")

def test_load_fit_summary_missing_columns():
    """Test that loading a file with missing required columns raises ValueError."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("galaxy_id,model\n") # Missing reduced_chi2
        f.write("NGC1001,mond\n")
        temp_path = f.name

    try:
        with pytest.raises(ValueError) as excinfo:
            load_fit_summary(temp_path)
        assert "missing required columns" in str(excinfo.value)
    finally:
        os.unlink(temp_path)

def test_compute_pass_rates():
    """Test pass rate calculation logic."""
    # Create a mock dataframe
    data = {
        'galaxy_id': ['G1', 'G1', 'G2', 'G2', 'G3', 'G3'],
        'model': ['mond', 'nfw', 'mond', 'nfw', 'mond', 'nfw'],
        'reduced_chi2': [0.5, 1.5, 1.2, 0.9, 1.6, 2.0]
    }
    df = pd.DataFrame(data)
    
    thresholds = [1.0, 1.5]
    results = compute_pass_rates(df, thresholds)
    
    assert len(results) == 4 # 2 models * 2 thresholds
    
    # Check MOND at 1.0 threshold
    mond_10 = results[(results['model'] == 'mond') & (results['chi2_threshold'] == 1.0)]
    assert len(mond_10) == 1
    # G1 (0.5) passes, G2 (1.2) fails, G3 (1.6) fails -> 1/3
    assert mond_10.iloc[0]['passes'] == 1
    assert np.isclose(mond_10.iloc[0]['pass_rate'], 1/3)
    
    # Check MOND at 1.5 threshold
    mond_15 = results[(results['model'] == 'mond') & (results['chi2_threshold'] == 1.5)]
    # G1 (0.5) passes, G2 (1.2) passes, G3 (1.6) fails -> 2/3
    assert mond_15.iloc[0]['passes'] == 2
    assert np.isclose(mond_15.iloc[0]['pass_rate'], 2/3)
    
    # Check NFW at 1.0 threshold
    nfw_10 = results[(results['model'] == 'nfw') & (results['chi2_threshold'] == 1.0)]
    # G1 (1.5) fails, G2 (0.9) passes, G3 (2.0) fails -> 1/3
    assert nfw_10.iloc[0]['passes'] == 1
    assert np.isclose(nfw_10.iloc[0]['pass_rate'], 1/3)

def test_chi2_thresholds_definition():
    """Verify the thresholds match SC-006 specification."""
    expected = [1.0, 1.25, 1.5, 1.75]
    assert CHI2_THRESHOLDS == expected