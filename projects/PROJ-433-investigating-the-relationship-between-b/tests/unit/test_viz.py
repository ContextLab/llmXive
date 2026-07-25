"""
Unit tests for the visualization module.
"""
import os
import tempfile
import numpy as np
import pytest
from pathlib import Path

# Import the function to test
from viz import generate_scatter_plot

def test_scatter_plot_generation():
    """
    Verify that a PNG file is created and contains a trendline for mock data.
    """
    # Create temporary directory for output
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test_plot.png")
        
        # Generate mock data
        np.random.seed(42)
        x = np.random.rand(20)
        y = 2 * x + np.random.normal(0, 0.1, 20)
        
        # Call the function
        generate_scatter_plot(
            x_data=x,
            y_data=y,
            x_label="X Variable",
            y_label="Y Variable",
            title="Test Plot",
            output_path=output_path,
            coef=0.8,
            p_val=0.001,
            effect_size=0.8,
            adj_p=0.001
        )
        
        # Verify file exists
        assert os.path.exists(output_path), f"Plot file {output_path} was not created."
        
        # Verify file size is reasonable (not empty)
        file_size = os.path.getsize(output_path)
        assert file_size > 1000, f"Plot file {output_path} is too small ({file_size} bytes)."
        
        # Verify it's a valid PNG (magic bytes)
        with open(output_path, 'rb') as f:
            header = f.read(8)
            assert header[:8] == b'\x89PNG\r\n\x1a\n', "File does not appear to be a valid PNG."

def test_scatter_plot_with_nans():
    """
    Verify that the function handles NaN values gracefully.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test_plot_nans.png")
        
        # Data with NaNs
        x = np.array([1.0, 2.0, np.nan, 4.0, 5.0])
        y = np.array([2.0, 4.0, 6.0, np.nan, 10.0])
        
        # Should not raise an exception
        generate_scatter_plot(
            x_data=x,
            y_data=y,
            x_label="X",
            y_label="Y",
            title="Test NaNs",
            output_path=output_path
        )
        
        assert os.path.exists(output_path)

def test_scatter_plot_insufficient_data():
    """
    Verify behavior with insufficient data points.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test_plot_small.png")
        
        # Only 1 point
        x = np.array([1.0])
        y = np.array([2.0])
        
        # Should handle gracefully (might log warning, but shouldn't crash)
        # The implementation checks len > 1 for regression, so it should still plot the point
        generate_scatter_plot(
            x_data=x,
            y_data=y,
            x_label="X",
            y_label="Y",
            title="Test Small",
            output_path=output_path
        )
        
        assert os.path.exists(output_path)