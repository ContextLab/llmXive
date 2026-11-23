import pytest
import pandas as pd
import numpy as np
import logging
from io import StringIO
import sys
import os

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from power_calc import filter_and_log_invalid_rows, calculate_power_cohen_d

def test_filter_nan_effect_size(caplog):
    """Test that rows with NaN effect_size are filtered and logged."""
    df = pd.DataFrame({
        'effect_size': [0.5, np.nan, 0.8],
        'sample_size': [100, 100, 100],
        'study_id': [1, 2, 3]
    })
    
    with caplog.at_level(logging.WARNING):
        result = filter_and_log_invalid_rows(df)
    
    assert len(result) == 2
    assert 1 not in result.index
    assert "NaN in effect_size or sample_size" in caplog.text

def test_filter_nan_sample_size(caplog):
    """Test that rows with NaN sample_size are filtered and logged."""
    df = pd.DataFrame({
        'effect_size': [0.5, 0.8, 0.2],
        'sample_size': [100, np.nan, 100],
        'study_id': [1, 2, 3]
    })
    
    with caplog.at_level(logging.WARNING):
        result = filter_and_log_invalid_rows(df)
    
    assert len(result) == 2
    assert 1 not in result.index
    assert "NaN in effect_size or sample_size" in caplog.text

def test_filter_negative_sample_size(caplog):
    """Test that rows with negative sample_size are filtered and logged."""
    df = pd.DataFrame({
        'effect_size': [0.5, 0.8, 0.2],
        'sample_size': [100, -5, 100],
        'study_id': [1, 2, 3]
    })
    
    with caplog.at_level(logging.WARNING):
        result = filter_and_log_invalid_rows(df)
    
    assert len(result) == 2
    assert 1 not in result.index
    assert "Invalid sample_size" in caplog.text

def test_filter_zero_sample_size(caplog):
    """Test that rows with zero sample_size are filtered and logged."""
    df = pd.DataFrame({
        'effect_size': [0.5, 0.8, 0.2],
        'sample_size': [100, 0, 100],
        'study_id': [1, 2, 3]
    })
    
    with caplog.at_level(logging.WARNING):
        result = filter_and_log_invalid_rows(df)
    
    assert len(result) == 2
    assert 1 not in result.index
    assert "Invalid sample_size" in caplog.text

def test_filter_infinite_effect_size(caplog):
    """Test that rows with infinite effect_size are filtered and logged."""
    df = pd.DataFrame({
        'effect_size': [0.5, np.inf, 0.2],
        'sample_size': [100, 100, 100],
        'study_id': [1, 2, 3]
    })
    
    with caplog.at_level(logging.WARNING):
        result = filter_and_log_invalid_rows(df)
    
    assert len(result) == 2
    assert 1 not in result.index
    assert "Infinite effect_size" in caplog.text

def test_log_format_correctness(caplog):
    """Test that the log message matches the required format: WARNING: Skipping row {index} due to {reason}."""
    df = pd.DataFrame({
        'effect_size': [np.nan],
        'sample_size': [100],
        'study_id': [1]
    })
    
    with caplog.at_level(logging.WARNING):
        filter_and_log_invalid_rows(df)
    
    # Check for the exact format
    assert "WARNING: Skipping row 0 due to NaN in effect_size or sample_size" in caplog.text

def test_valid_rows_passed():
    """Test that valid rows are passed through."""
    df = pd.DataFrame({
        'effect_size': [0.5, 0.8],
        'sample_size': [100, 200],
        'study_id': [1, 2]
    })
    
    result = filter_and_log_invalid_rows(df)
    assert len(result) == 2
    assert list(result.index) == [0, 1]

def test_power_calc_handles_nan():
    """Unit test for NaN handling in power calculation."""
    assert pd.isna(calculate_power_cohen_d(np.nan, 100))
    assert pd.isna(calculate_power_cohen_d(0.5, np.nan))
    assert pd.isna(calculate_power_cohen_d(0.5, 0))
    assert pd.isna(calculate_power_cohen_d(0.5, 1))