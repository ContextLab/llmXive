import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from train_learning_curves import (
    generate_learning_curve_for_property,
    MIN_SAMPLES_THRESHOLD,
    DataInsufficientError
)

@pytest.fixture
def mock_feature_cols():
    return ['magpie_feature_1', 'magpie_feature_2', 'magpie_feature_3']

@pytest.fixture
def create_test_df():
    def _create(n_rows):
        data = {
            'property_name': ['test_prop'] * n_rows,
            'target': np.random.rand(n_rows),
            'magpie_feature_1': np.random.rand(n_rows),
            'magpie_feature_2': np.random.rand(n_rows),
            'magpie_feature_3': np.random.rand(n_rows),
        }
        return pd.DataFrame(data)
    return _create

def test_insufficient_data_raises_warning(create_test_df, mock_feature_cols, caplog):
    """Test that properties with < 1000 samples are skipped and logged."""
    n_samples = 500  # Below threshold
    df = create_test_df(n_samples)
    
    # Mock the logging to capture the warning
    with caplog.at_level("WARNING"):
        result = generate_learning_curve_for_property("test_prop", df, mock_feature_cols)
    
    assert result is None
    assert "Insufficient data points" in caplog.text
    assert f"Found {n_samples} samples" in caplog.text

def test_sufficient_data_proceeds(create_test_df, mock_feature_cols, caplog):
    """Test that properties with >= 1000 samples proceed."""
    n_samples = 1500  # Above threshold
    df = create_test_df(n_samples)
    
    with caplog.at_level("INFO"):
        result = generate_learning_curve_for_property("test_prop", df, mock_feature_cols)
    
    assert result is not None
    assert result['status'] == 'success'
    assert len(result['subset_sizes']) > 0

def test_edge_case_exact_threshold(create_test_df, mock_feature_cols):
    """Test behavior exactly at the threshold (1000 samples)."""
    n_samples = 1000
    df = create_test_df(n_samples)
    
    result = generate_learning_curve_for_property("test_prop", df, mock_feature_cols)
    
    # Should proceed since 1000 >= 1000
    assert result is not None
    assert result['total_samples'] == 1000

def test_zero_samples(create_test_df, mock_feature_cols, caplog):
    """Test behavior with zero samples."""
    n_samples = 0
    df = create_test_df(n_samples)
    
    with caplog.at_level("WARNING"):
        result = generate_learning_curve_for_property("test_prop", df, mock_feature_cols)
    
    assert result is None
    assert "Insufficient data points" in caplog.text