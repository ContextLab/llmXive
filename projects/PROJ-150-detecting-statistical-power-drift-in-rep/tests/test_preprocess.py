import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from preprocess import load_raw_data, filter_missing_rows, compute_power_estimates, DataFetchError

def test_filter_missing_rows_removes_nan():
    """Test that filter_missing_rows removes rows with NaN in critical columns."""
    data = {
        'year': [2000, 2001, np.nan, 2003],
        'effect_size': [0.5, np.nan, 0.3, 0.4],
        'sample_size': [100, 100, 100, 100],
        'study_id': ['A', 'B', 'C', 'D']
    }
    df = pd.DataFrame(data)
    
    filtered = filter_missing_rows(df)
    
    assert len(filtered) == 2
    assert 'year' not in filtered.columns or not filtered['year'].isna().any()
    assert not filtered['effect_size'].isna().any()
    assert not filtered['sample_size'].isna().any()

def test_compute_power_estimates():
    """Test that power estimates are calculated correctly."""
    data = {
        'effect_size': [0.5, 0.8, 0.2],
        'sample_size': [100, 200, 50]
    }
    df = pd.DataFrame(data)
    
    result = compute_power_estimates(df)
    
    assert 'power_estimate' in result.columns
    assert len(result) == 3
    assert not result['power_estimate'].isna().any()
    # Power should be between 0 and 1
    assert (result['power_estimate'] >= 0).all()
    assert (result['power_estimate'] <= 1).all()

def test_load_raw_data_missing_file():
    """Test that DataFetchError is raised if file is missing."""
    with pytest.raises(DataFetchError):
        load_raw_data("non_existent_file.csv")

def test_filter_missing_rows_logs_warnings(caplog):
    """Test that warnings are logged for skipped rows."""
    data = {
        'year': [2000, np.nan],
        'effect_size': [0.5, 0.3],
        'sample_size': [100, 100]
    }
    df = pd.DataFrame(data)
    
    with caplog.at_level("WARNING"):
        filter_missing_rows(df)
    
    assert "WARNING: Skipping row" in caplog.text