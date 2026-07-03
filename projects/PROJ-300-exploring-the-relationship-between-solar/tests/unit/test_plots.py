"""
Unit tests for viz/plots.py to verify SC-005:
- Plots load without error
- Correct axis labels and units
- Optimal lag annotation present
"""
import os
import sys
import tempfile
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for testing
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add project root to path if not already present
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from code.viz.plots import plot_scatter, plot_timeseries

def generate_sample_data():
    """Generate synthetic sample data for testing plot functions."""
    dates = pd.date_range(start='2023-01-01', periods=100, freq='1H')
    # Simulate Vsw (km/s) and Ey (mV/m) with some correlation
    np.random.seed(42)
    vsw = 400 + 150 * np.random.randn(100)
    # Ey correlated with Vsw plus noise
    ey = 0.05 * vsw + 2 + 0.5 * np.random.randn(100)
    
    df_vsw = pd.DataFrame({
        'timestamp': dates,
        'Vsw': vsw
    })
    df_ey = pd.DataFrame({
        'timestamp': dates,
        'Ey': ey
    })
    return df_vsw, df_ey

def test_plot_scatter_loads_without_error():
    """Test that plot_scatter generates a file without errors."""
    df_vsw, df_ey = generate_sample_data()
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, 'test_scatter.png')
        # Should not raise an exception
        plot_scatter(df_vsw, df_ey, lag_minutes=45, output_path=output_path)
        assert os.path.exists(output_path), "Plot file was not created"

def test_plot_scatter_has_correct_labels():
    """Test that plot_scatter has correct axis labels and units."""
    df_vsw, df_ey = generate_sample_data()
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, 'test_scatter_labels.png')
        plot_scatter(df_vsw, df_ey, lag_minutes=45, output_path=output_path)
        
        # Re-open the figure to check labels (matplotlib doesn't store labels in saved PNG easily)
        # Instead, we test by inspecting the function's behavior or re-plotting
        # We'll create a test figure and check axes
        fig, ax = plt.subplots()
        plot_scatter(df_vsw, df_ey, lag_minutes=45, ax=ax)
        
        xlabel = ax.get_xlabel()
        ylabel = ax.get_ylabel()
        
        assert 'Vsw' in xlabel or 'Solar Wind Speed' in xlabel, f"X-axis label missing Vsw: {xlabel}"
        assert 'km/s' in xlabel, f"X-axis label missing units: {xlabel}"
        assert 'Ey' in ylabel or 'Reconnection Rate' in ylabel, f"Y-axis label missing Ey: {ylabel}"
        assert 'mV/m' in ylabel, f"Y-axis label missing units: {ylabel}"
        plt.close(fig)

def test_plot_scatter_has_lag_annotation():
    """Test that plot_scatter includes optimal lag annotation."""
    df_vsw, df_ey = generate_sample_data()
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, 'test_scatter_annotation.png')
        plot_scatter(df_vsw, df_ey, lag_minutes=45, output_path=output_path)
        
        # Check by re-plotting and inspecting text elements
        fig, ax = plt.subplots()
        plot_scatter(df_vsw, df_ey, lag_minutes=45, ax=ax)
        
        text_elements = [t.get_text() for t in ax.texts]
        # Look for lag annotation (should contain "45" or "lag")
        lag_found = any('45' in t and ('min' in t or 'lag' in t) for t in text_elements)
        assert lag_found, f"Optimal lag annotation not found in plot. Text elements: {text_elements}"
        plt.close(fig)

def test_plot_timeseries_loads_without_error():
    """Test that plot_timeseries generates a file without errors."""
    df_vsw, df_ey = generate_sample_data()
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, 'test_timeseries.png')
        plot_timeseries(df_vsw, df_ey, lag_minutes=45, output_path=output_path)
        assert os.path.exists(output_path), "Plot file was not created"

def test_plot_timeseries_has_correct_labels():
    """Test that plot_timeseries has correct axis labels and units."""
    df_vsw, df_ey = generate_sample_data()
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, 'test_timeseries_labels.png')
        plot_timeseries(df_vsw, df_ey, lag_minutes=45, output_path=output_path)
        
        fig, ax = plt.subplots()
        plot_timeseries(df_vsw, df_ey, lag_minutes=45, ax=ax)
        
        # Check x-axis label (should be time)
        xlabel = ax.get_xlabel()
        assert 'Time' in xlabel or 'Date' in xlabel, f"X-axis label missing time: {xlabel}"
        
        # Check y-axis labels (dual axis)
        left_ax = ax
        right_ax = ax.twinx() if hasattr(ax, 'twinx') else None
        # In dual-axis plots, we check both axes
        ylabels = [ax.get_ylabel() for ax in [left_ax] + ([right_ax] if right_ax else [])]
        has_vsw_label = any('Vsw' in str(l) or 'Solar Wind' in str(l) for l in ylabels)
        has_ey_label = any('Ey' in str(l) or 'Reconnection' in str(l) for l in ylabels)
        
        assert has_vsw_label, f"Missing Vsw label in time series: {ylabels}"
        assert has_ey_label, f"Missing Ey label in time series: {ylabels}"
        plt.close(fig)

def test_plot_timeseries_has_lag_annotation():
    """Test that plot_timeseries includes optimal lag annotation."""
    df_vsw, df_ey = generate_sample_data()
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, 'test_timeseries_annotation.png')
        plot_timeseries(df_vsw, df_ey, lag_minutes=45, output_path=output_path)
        
        fig, ax = plt.subplots()
        plot_timeseries(df_vsw, df_ey, lag_minutes=45, ax=ax)
        
        text_elements = [t.get_text() for t in ax.texts]
        lag_found = any('45' in t and ('min' in t or 'lag' in t) for t in text_elements)
        assert lag_found, f"Optimal lag annotation not found in time series plot. Text elements: {text_elements}"
        plt.close(fig)
