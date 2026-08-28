import numpy as np
import pandas as pd
import pytest
from analysis.sensitivity import run_sensitivity_analysis
from errors import DataMissingCreativityError

def test_run_sensitivity_analysis_1d():
    """Test with 1D flexibility array (single window length)."""
    flexibility = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
    creativity = np.array([10, 20, 30, 40, 50])
    window_lengths = [30]
    
    df = run_sensitivity_analysis(flexibility, creativity, window_lengths)
    
    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == ["window_length", "correlation", "p_value"]
    assert len(df) == 1
    assert df.iloc[0]["window_length"] == 30
    # Check correlation is close to 1.0 for this perfect linear data
    assert np.isclose(df.iloc[0]["correlation"], 1.0)

def test_run_sensitivity_analysis_2d():
    """Test with 2D flexibility array (multiple window lengths)."""
    n_subjects = 10
    n_windows = 3
    window_lengths = [20, 30, 40]
    
    # Create synthetic data with known correlations
    creativity = np.random.randn(n_subjects)
    flexibility = np.column_stack([
        creativity + np.random.randn(n_subjects) * 0.1, # High correlation
        creativity * 0.5 + np.random.randn(n_subjects) * 0.5, # Medium
        np.random.randn(n_subjects) # No correlation
    ])
    
    df = run_sensitivity_analysis(flexibility, creativity, window_lengths)
    
    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == ["window_length", "correlation", "p_value"]
    assert len(df) == 3
    
    # Check that window lengths match
    assert list(df["window_length"]) == window_lengths
    
    # Check that correlations are different (not all 0 or 1)
    corrs = df["correlation"].values
    assert not np.all(np.isclose(corrs, corrs[0]))

def test_run_sensitivity_analysis_nan_handling():
    """Test that NaN values are handled correctly."""
    flexibility = np.array([0.1, np.nan, 0.3, 0.4, 0.5])
    creativity = np.array([10, 20, 30, 40, 50])
    window_lengths = [30]
    
    df = run_sensitivity_analysis(flexibility, creativity, window_lengths)
    
    # Should have computed correlation on valid data
    assert len(df) == 1
    assert not np.isnan(df.iloc[0]["correlation"])
    assert not np.isnan(df.iloc[0]["p_value"])

def test_run_sensitivity_analysis_mismatched_shapes():
    """Test error when flexibility shape doesn't match window_lengths."""
    flexibility = np.random.randn(10, 2)
    creativity = np.random.randn(10)
    window_lengths = [20, 30, 40] # 3 lengths but only 2 columns in flexibility
    
    with pytest.raises(ValueError):
        run_sensitivity_analysis(flexibility, creativity, window_lengths)
