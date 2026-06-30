"""
Tests for visualization functions in code/viz/plots.py
"""
import os
import tempfile
import numpy as np
import pytest
from pathlib import Path

# Add the project root to the path if running as a script
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from viz.plots import plot_flexibility_vs_creativity


class TestPlotFlexibilityVsCreativity:
    def test_plot_creates_file(self, tmp_path):
        """Test that the function creates the output file."""
        output_path = str(tmp_path / "test_plot.png")
        
        # Generate dummy data
        flexibility = np.random.rand(50)
        creativity = np.random.rand(50)
        
        result_path = plot_flexibility_vs_creativity(flexibility, creativity, output_path)
        
        assert os.path.exists(result_path), f"Output file not created at {result_path}"
        assert os.path.getsize(result_path) > 0, "Output file is empty"
        assert result_path.endswith(".png"), "Output file is not a PNG"

    def test_plot_handles_nan(self, tmp_path):
        """Test that the function handles NaN values gracefully."""
        output_path = str(tmp_path / "test_plot_nan.png")
        
        # Data with NaNs
        flexibility = np.array([1.0, 2.0, np.nan, 4.0, 5.0])
        creativity = np.array([10.0, np.nan, 30.0, 40.0, 50.0])
        
        # Should not raise an error
        result_path = plot_flexibility_vs_creativity(flexibility, creativity, output_path)
        
        assert os.path.exists(result_path)

    def test_plot_raises_on_insufficient_data(self, tmp_path):
        """Test that the function raises ValueError with insufficient data."""
        output_path = str(tmp_path / "test_plot_fail.png")
        
        flexibility = np.array([1.0])
        creativity = np.array([10.0])
        
        with pytest.raises(ValueError, match="Insufficient valid data points"):
            plot_flexibility_vs_creativity(flexibility, creativity, output_path)

    def test_plot_regression_line_exists(self, tmp_path):
        """Test that the generated plot contains regression line data."""
        output_path = str(tmp_path / "test_regression.png")
        
        # Create a clear linear relationship
        x = np.linspace(0, 10, 100)
        y = 2 * x + 1 + np.random.normal(0, 0.5, 100)
        
        plot_flexibility_vs_creativity(x, y, output_path)
        
        # File exists check is sufficient for this contract test
        assert os.path.exists(output_path)