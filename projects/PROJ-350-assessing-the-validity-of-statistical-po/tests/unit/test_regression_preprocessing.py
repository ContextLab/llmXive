"""
Unit tests for the regression preprocessing logic (T031).
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module functions
from code.regression import (
    load_power_gap_data,
    enforce_minimum_sample_size,
    preprocess_for_regression,
    RegressionPreprocessingError
)

@pytest.fixture
def mock_power_data():
    """Create a mock DataFrame that mimics the power_analysis.csv structure."""
    data = {
        'study_id': [1, 2, 3, 4, 5],
        'field': ['Psychology', 'Psychology', 'Neuroscience', 'Neuroscience', 'Psychology'],
        'effect_size_domain': ['Small', 'Medium', 'Small', 'Medium', 'Small'],
        'sample_size_category': ['Small', 'Medium', 'Small', 'Medium', 'Small'],
        'planned_power': [0.8, 0.8, 0.8, 0.8, 0.8],
        'sensitivity_power': [0.6, 0.7, 0.5, 0.6, 0.7],
        'power_gap': [0.2, 0.1, 0.3, 0.2, 0.1]
    }
    return pd.DataFrame(data)

@pytest.fixture
def small_sample_data():
    """Create a mock DataFrame with fewer than 30 records."""
    data = {
        'study_id': [1, 2, 3],
        'field': ['Psychology', 'Psychology', 'Neuroscience'],
        'effect_size_domain': ['Small', 'Medium', 'Small'],
        'sample_size_category': ['Small', 'Medium', 'Small'],
        'planned_power': [0.8, 0.8, 0.8],
        'sensitivity_power': [0.6, 0.7, 0.5],
        'power_gap': [0.2, 0.1, 0.3]
    }
    return pd.DataFrame(data)

def test_enforce_minimum_sample_size_success(mock_power_data):
    """Test that a dataset with >= 30 records passes the check."""
    # Expand the mock data to 30 records for the test
    large_data = pd.concat([mock_power_data] * 10, ignore_index=True)
    
    # Should not raise
    result = enforce_minimum_sample_size(large_data, threshold=30)
    assert len(result) == 30

def test_enforce_minimum_sample_size_failure(small_sample_data, tmp_path):
    """Test that a dataset with < 30 records raises RuntimeError and writes error artifact."""
    # Mock write_error_artifact to avoid file system dependency in unit test
    with patch('code.regression.write_error_artifact') as mock_write:
        with pytest.raises(RuntimeError, match="Dataset size.*below the minimum threshold"):
            enforce_minimum_sample_size(small_sample_data, threshold=30)
        
        mock_write.assert_called_once()

def test_preprocess_for_regression_excludes_coupling(mock_power_data):
    """Test that sample_size_category is NOT in the output columns."""
    result = preprocess_for_regression(mock_power_data)
    
    assert 'sample_size_category' not in result.columns, \
        "sample_size_category must be excluded to avoid mathematical coupling."
    
    # Check that dummy variables for 'field' and 'effect_size_domain' were created
    assert 'field_Neuroscience' in result.columns or 'field_P Psychology' in result.columns # depends on encoding
    # Actually, with drop_first, if 'Psychology' is first, we expect 'field_Neuroscience'
    # Let's just check that the categorical columns are transformed
    assert any(col.startswith('field_') for col in result.columns), "Field dummies should exist"
    assert any(col.startswith('effect_size_domain_') for col in result.columns), "Effect size dummies should exist"

def test_preprocess_for_regression_missing_target(mock_power_data):
    """Test that missing 'power_gap' column raises an error."""
    df_no_target = mock_power_data.drop(columns=['power_gap'])
    
    with pytest.raises(RegressionPreprocessingError, match="Target variable 'power_gap' not found"):
        preprocess_for_regression(df_no_target)

def test_preprocess_for_regression_manual_verification(mock_power_data):
    """Manual check of the dummy encoding logic."""
    result = preprocess_for_regression(mock_power_data)
    
    # Verify that the original categorical columns are gone
    assert 'field' not in result.columns
    assert 'effect_size_domain' not in result.columns
    
    # Verify that numeric columns remain
    assert 'power_gap' in result.columns
    assert 'planned_power' in result.columns