import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from data_loader import split_series, standardize
from utils.exceptions import DataValidationError

def test_split_series():
    """Test the split_series function with 80/20 split."""
    # Create a mock series
    data = np.arange(100)
    series = pd.Series(data, name='test')
    
    train, test = split_series(series, train_ratio=0.8)
    
    assert len(train) == 80
    assert len(test) == 20
    assert list(train.values) == list(range(80))
    assert list(test.values) == list(range(80, 100))

def test_split_series_short():
    """Test that split_series raises error for too short series."""
    data = np.arange(5)
    series = pd.Series(data, name='test')
    
    with pytest.raises(DataValidationError):
        split_series(series, train_ratio=0.8)

def test_standardize():
    """Test the standardize function."""
    data = np.array([10, 20, 30, 40, 50])
    series = pd.Series(data, name='test')
    
    standardized, mean, std = standardize(series)
    
    assert np.isclose(mean, 30.0)
    assert np.isclose(std, 14.142135623730951)
    assert np.isclose(standardized.mean(), 0.0)
    assert np.isclose(standardized.std(), 1.0)

def test_standardize_zero_std():
    """Test standardize with constant series."""
    data = np.array([5, 5, 5, 5, 5])
    series = pd.Series(data, name='test')
    
    standardized, mean, std = standardize(series)
    
    assert std == 0.0
    assert np.array_equal(standardized.values, series.values)
