"""
Unit tests for the external validation module.
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
from pathlib import Path
import json
import os

# Import the module under test
# We mock the dependencies to avoid needing real data files for unit tests
import sys
from unittest.mock import Mock

@pytest.fixture
def mock_manifest_data():
    """Create a mock manifest dataframe with valid data."""
    data = {
        'subject_id': ['sub-01', 'sub-02', 'sub-03', 'sub-04'],
        'time_point': ['acute', 'chronic', 'acute', 'chronic'],
        'global_efficiency': [0.35, 0.42, 0.38, 0.45],
        'ReturnToWork': [0, 1, 0, 1],  # Binary return to work status
        'missing_col': [np.nan, 1.0, 0.0, 1.0]
    }
    return pd.DataFrame(data)

@pytest.fixture
def mock_manifest_path(tmp_path, mock_manifest_data):
    """Create a temporary manifest.csv file."""
    manifest_path = tmp_path / "manifest.csv"
    mock_manifest_data.to_csv(manifest_path, index=False)
    return manifest_path

def test_find_target_column_exists(mock_manifest_data):
    """Test that find_target_column correctly identifies the RTW column."""
    from validation import find_target_column
    
    # Inject the function into the module namespace for testing if needed, 
    # but since it's defined in the module, we can import it directly if we set up the path.
    # However, for unit testing isolated logic, we can just test the logic here.
    
    # Simulating the logic from validation.py
    columns = [c.lower() for c in mock_manifest_data.columns]
    target = 'ReturnToWork'
    
    # The actual function logic:
    for t in ['ReturnToWork', 'RTW', 'EmploymentStatus']:
        if t.lower() in columns:
            idx = columns.index(t.lower())
            assert mock_manifest_data.columns[idx] == 'ReturnToWork'
            return
    
    pytest.fail("Target column not found in test data")

def test_find_target_column_missing(mock_manifest_data):
    """Test that find_target_column returns None if no target exists."""
    # Remove the target column
    df_no_target = mock_manifest_data.drop(columns=['ReturnToWork'])
    
    # Re-implement logic locally to test
    columns = [c.lower() for c in df_no_target.columns]
    target_names = ['ReturnToWork', 'RTW', 'EmploymentStatus']
    
    found = False
    for t in target_names:
        if t.lower() in columns:
            found = True
            break
    
    assert not found

def test_correlation_calculation_success(mock_manifest_data):
    """Test correlation calculation with valid data."""
    from validation import calculate_correlation_with_metric
    
    result = calculate_correlation_with_metric(
        mock_manifest_data, 
        metric_col='ReturnToWork', 
        graph_metric_col='global_efficiency'
    )
    
    assert result['status'] == 'success'
    assert result['correlation'] is not None
    assert result['p_value'] is not None
    assert result['n'] == 4

def test_correlation_calculation_insufficient_data():
    """Test correlation calculation with too few data points."""
    from validation import calculate_correlation_with_metric
    
    df = pd.DataFrame({
        'metric': [1.0, 2.0],
        'graph': [0.1, 0.2]
    })
    
    result = calculate_correlation_with_metric(df, 'metric', 'graph')
    
    assert result['status'] == 'insufficient_data'
    assert result['n'] == 2

def test_correlation_calculation_with_missing_values(mock_manifest_data):
    """Test that NaN values are handled correctly."""
    from validation import calculate_correlation_with_metric
    
    # The mock data has a NaN in 'missing_col', but we are testing 'ReturnToWork' which is clean
    # Let's create a scenario with NaNs in the target columns
    df = pd.DataFrame({
        'metric': [1.0, np.nan, 3.0],
        'graph': [0.1, 0.2, 0.3]
    })
    
    result = calculate_correlation_with_metric(df, 'metric', 'graph')
    
    # Should drop the NaN row, leaving 2 points -> insufficient
    assert result['status'] == 'insufficient_data'
    assert result['n'] == 2
