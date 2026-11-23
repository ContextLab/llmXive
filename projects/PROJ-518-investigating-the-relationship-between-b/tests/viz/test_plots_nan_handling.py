import pytest
import numpy as np
import os
import tempfile
from pathlib import Path
import warnings

# Adjust import based on project structure
# Assuming tests are at root, and code is at code/
# But the prompt says "single project: src/, tests/ at repository root" but also "path conventions... code/"
# The API surface shows imports like "from viz.plots import ..."
# We will assume the code is in the PYTHONPATH or we run from project root.
# For the test file, we need to import the functions.

# Mock the RegressionResult for testing plot_residuals
from dataclasses import dataclass
import pandas as pd

@dataclass
class MockRegressionResult:
    fittedvalues: np.ndarray
    resid: np.ndarray
    rsquared: float
    rsquared_adj: float
    pearson_r: float
    delta_r2: float
    params: pd.Series

def test_plot_flexibility_vs_creativity_with_nan():
    """Test that plot_flexibility_vs_creativity handles NaNs gracefully."""
    from viz.plots import plot_flexibility_vs_creativity
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, 'test_plot.png')
        
        # Data with NaNs
        flex = np.array([1.0, 2.0, np.nan, 4.0, 5.0])
        creat = np.array([10.0, np.nan, 30.0, 40.0, 50.0])
        
        # Should not raise
        plot_flexibility_vs_creativity(flex, creat, output_path)
        
        assert os.path.exists(output_path)
        # File should be non-empty
        assert os.path.getsize(output_path) > 0

def test_plot_residuals_with_nan():
    """Test that plot_residuals handles NaNs gracefully."""
    from viz.plots import plot_residuals
    
    fitted = np.array([1.0, 2.0, np.nan, 4.0, 5.0])
    resid = np.array([0.1, np.nan, 0.3, 0.4, 0.5])
    
    mock_result = MockRegressionResult(
        fittedvalues=fitted,
        resid=resid,
        rsquared=0.8,
        rsquared_adj=0.75,
        pearson_r=0.9,
        delta_r2=0.1,
        params=pd.Series([0.5, 0.2], index=['const', 'x'])
    )
    
    with tempfile.TemporaryDirectory() as tmpdir:
        res_path = os.path.join(tmpdir, 'residuals.png')
        qq_path = os.path.join(tmpdir, 'qq.png')
        
        plot_residuals(mock_result, res_path, qq_path)
        
        assert os.path.exists(res_path)
        assert os.path.exists(qq_path)
        assert os.path.getsize(res_path) > 0
        assert os.path.getsize(qq_path) > 0

def test_all_nan_data():
    """Test behavior when all data is NaN."""
    from viz.plots import plot_flexibility_vs_creativity
    
    flex = np.array([np.nan, np.nan])
    creat = np.array([np.nan, np.nan])
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, 'empty_plot.png')
        
        # Should handle gracefully, creating an empty plot or raising a specific handled error
        # Based on implementation, it creates a plot with "No valid data"
        plot_flexibility_vs_creativity(flex, creat, output_path)
        
        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) > 0
