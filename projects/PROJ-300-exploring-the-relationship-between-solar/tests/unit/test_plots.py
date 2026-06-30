"""
Unit tests for visualization functions in code/viz/plots.py.
Specifically tests FR-008b (plot_timeseries) and FR-008a (plot_scatter).
"""
import os
import tempfile
import pandas as pd
import numpy as np
import pytest
from datetime import datetime, timedelta

# Import the function under test
import sys
import pathlib
project_root = pathlib.Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
from code.viz.plots import plot_timeseries, plot_scatter

@pytest.fixture
def sample_timeseries_data():
    """Generate synthetic time series data with DatetimeIndex."""
    n_points = 100
    start_time = datetime(2023, 1, 1)
    dates = [start_time + timedelta(minutes=i*5) for i in range(n_points)]
    index = pd.DatetimeIndex(dates)
    
    # Vsw: Solar wind speed (km/s)
    vsw_values = np.random.uniform(300, 800, n_points)
    vsw = pd.Series(vsw_values, index=index, name='Vsw')
    
    # Ey: Reconnection rate (mV/m)
    # Create a lagged relationship for realism
    ey_values = (vsw_values * 0.01) + np.random.normal(0, 0.5, n_points)
    ey = pd.Series(ey_values, index=index, name='Ey')
    
    return vsw, ey

def test_plot_timeseries_creates_file(sample_timeseries_data):
    """Test that plot_timeseries creates a valid PNG file."""
    vsw, ey = sample_timeseries_data
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test_timeseries.png")
        
        # Call the function
        plot_timeseries(vsw, ey, optimal_lag=45, output_path=output_path)
        
        # Verify file exists and has content
        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) > 0

def test_plot_timeseries_invalid_index():
    """Test that plot_timeseries raises error for non-datetime index."""
    # Create series with integer index
    vsw = pd.Series([1, 2, 3], index=[0, 1, 2])
    ey = pd.Series([0.1, 0.2, 0.3], index=[0, 1, 2])
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test_fail.png")
        
        with pytest.raises(ValueError, match="Input series must have a DatetimeIndex"):
            plot_timeseries(vsw, ey, output_path=output_path)

def test_plot_timeseries_with_lag_annotation(sample_timeseries_data):
    """Test that optimal_lag is included in title when provided."""
    vsw, ey = sample_timeseries_data
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test_lag.png")
        
        # This test primarily ensures no crash occurs with the parameter.
        # Visual inspection of the title would require loading the image,
        # which is beyond simple unit test scope, but we verify execution.
        plot_timeseries(vsw, ey, optimal_lag=60, output_path=output_path)
        
        assert os.path.exists(output_path)

def test_plot_scatter_creates_file(sample_timeseries_data):
    """Test that plot_scatter creates a valid PNG file."""
    vsw, ey = sample_timeseries_data
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test_scatter.png")
        
        plot_scatter(vsw, ey, optimal_lag=45, output_path=output_path)
        
        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) > 0

def test_plot_scatter_insufficient_data():
    """Test that plot_scatter raises error for too few points."""
    # Only 1 point
    dates = pd.DatetimeIndex([datetime(2023, 1, 1)])
    vsw = pd.Series([400], index=dates)
    ey = pd.Series([2.0], index=dates)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test_fail.png")
        
        with pytest.raises(ValueError, match="Insufficient data points"):
            plot_scatter(vsw, ey, output_path=output_path)