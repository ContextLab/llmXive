"""
Unit tests for code/data/processor.py
"""
import pytest
import pandas as pd
import numpy as np
from data.processor import (
    MissingValueError,
    detect_missing_values,
    handle_missing_values,
    generate_statistical_summaries
)

def test_detect_missing_values():
    """Test missing value detection."""
    df = pd.DataFrame({
        'a': [1, 2, np.nan],
        'b': [4, np.nan, 6]
    })
    missing = detect_missing_values(df)
    assert 'a' in missing
    assert 'b' in missing
    assert missing['a'] == 1
    assert missing['b'] == 1

def test_handle_missing_values():
    """Test missing value handling (imputation)."""
    df = pd.DataFrame({
        'a': [1, 2, np.nan],
        'b': [4, np.nan, 6]
    })
    cleaned = handle_missing_values(df)
    assert not cleaned.isnull().any().any()

def test_generate_statistical_summaries():
    """Test statistical summary generation."""
    df = pd.DataFrame({
        'a': [1, 2, 3, 4, 5],
        'b': [10, 20, 30, 40, 50]
    })
    summaries = generate_statistical_summaries(df)
    assert 'a' in summaries
    assert 'b' in summaries
    assert summaries['a']['mean'] == 3.0
