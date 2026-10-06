import pytest
import numpy as np
import os
import tempfile
from pathlib import Path
from viz.plots import plot_flexibility_vs_creativity, plot_residuals, _clean_nan_arrays
from analysis.statistics import RegressionResult

def test_clean_nan_arrays():
    """Test that NaN values are correctly removed."""
    x = np.array([1.0, 2.0, np.nan, 4.0])
    y = np.array([1.0, np.nan, 3.0, 4.0])
    
    x_clean, y_clean = _clean_nan_arrays(x, y)
    
    # Expected: index 0 and 3 are valid (1,1) and (4,4)
    # index 1: y is nan
    # index 2: x is nan
    assert len(x_clean) == 2
    assert np.allclose(x_clean, [1.0, 4.0])
    assert np.allclose(y_clean, [1.0, 4.0])

def test_clean_nan_arrays_raises_mismatch():
    """Test that mismatched shapes raise ValueError."""
    x = np.array([1.0, 2.0])
    y = np.array([1.0])
    
    with pytest.raises(ValueError):
        _clean_nan_arrays(x, y)

def test_plot_flexibility_vs_creativity_handles_nan(tmp_path):
    """Test that plot function skips NaN points and saves file."""
    output_path = tmp_path / "test_plot.png"
    
    x = np.array([1.0, 2.0, np.nan, 4.0, 5.0])
    y = np.array([1.0, 2.0, 3.0, np.nan, 5.0])
    
    # Should not raise, just log warnings
    plot_flexibility_vs_creativity(x, y, str(output_path))
    
    assert output_path.exists()
    assert output_path.stat().st_size > 0

def test_plot_residuals_handles_nan(tmp_path):
    """Test that residual plots handle NaN values."""
    output_dir = tmp_path
    residuals_path = output_dir / "residuals.png"
    qq_path = output_dir / "qq.png"
    
    # Create a mock RegressionResult
    # We need to simulate a model with some NaN residuals
    class MockResult:
        def __init__(self):
            self.residuals = np.array([0.1, -0.2, np.nan, 0.3])
            self.fitted_values = np.array([1.0, 2.0, 3.0, 4.0])
    
    mock_result = MockResult()
    
    # Should not raise
    plot_residuals(mock_result, str(residuals_path), str(qq_path))
    
    assert residuals_path.exists()
    assert qq_path.exists()