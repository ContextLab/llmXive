"""
Tests for sensitivity analysis functionality.
"""
import numpy as np
import pandas as pd
import pytest
from analysis.sensitivity import run_sensitivity_analysis


def test_run_sensitivity_analysis_returns_dataframe():
    """Test that run_sensitivity_analysis returns a DataFrame with correct columns."""
    np.random.seed(42)
    flexibility = np.random.randn(100)
    creativity = np.random.randn(100)
    window_lengths = [20, 30, 40]

    result = run_sensitivity_analysis(flexibility, creativity, window_lengths)

    assert isinstance(result, pd.DataFrame)
    assert list(result.columns) == ['window_length', 'correlation', 'p_value']
    assert len(result) == len(window_lengths)


def test_run_sensitivity_analysis_window_lengths_match():
    """Test that the window lengths in the result match the input."""
    np.random.seed(42)
    flexibility = np.random.randn(50)
    creativity = np.random.randn(50)
    window_lengths = [20, 30, 40]

    result = run_sensitivity_analysis(flexibility, creativity, window_lengths)

    assert list(result['window_length']) == window_lengths


def test_run_sensitivity_analysis_correlation_values():
    """Test that correlation values are within valid range [-1, 1]."""
    np.random.seed(42)
    flexibility = np.random.randn(50)
    creativity = np.random.randn(50)
    window_lengths = [20, 30, 40]

    result = run_sensitivity_analysis(flexibility, creativity, window_lengths)

    assert all((result['correlation'] >= -1) & (result['correlation'] <= 1))


def test_run_sensitivity_analysis_p_values():
    """Test that p-values are within valid range [0, 1]."""
    np.random.seed(42)
    flexibility = np.random.randn(50)
    creativity = np.random.randn(50)
    window_lengths = [20, 30, 40]

    result = run_sensitivity_analysis(flexibility, creativity, window_lengths)

    assert all((result['p_value'] >= 0) & (result['p_value'] <= 1))


def test_run_sensitivity_analysis_empty_input():
    """Test that empty input raises ValueError."""
    flexibility = np.array([])
    creativity = np.array([])

    with pytest.raises(ValueError, match="Input arrays cannot be empty"):
        run_sensitivity_analysis(flexibility, creativity)


def test_run_sensitivity_analysis_mismatched_lengths():
    """Test that mismatched array lengths raise ValueError."""
    flexibility = np.random.randn(50)
    creativity = np.random.randn(60)

    with pytest.raises(ValueError, match="must have the same length"):
        run_sensitivity_analysis(flexibility, creativity)


def test_run_sensitivity_analysis_default_window_lengths():
    """Test that default window lengths are [20, 30, 40]."""
    np.random.seed(42)
    flexibility = np.random.randn(50)
    creativity = np.random.randn(50)

    result = run_sensitivity_analysis(flexibility, creativity)

    assert list(result['window_length']) == [20, 30, 40]