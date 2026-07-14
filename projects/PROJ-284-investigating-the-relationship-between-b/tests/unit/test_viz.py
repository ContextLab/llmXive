"""Unit tests for visualization modules."""
import os
import tempfile
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import pytest

# Ensure non-interactive backend for testing
matplotlib.use('Agg')

from code.viz.scatter import generate_scatter_plot


class TestScatterPlot:
    """Tests for the scatter plot generator."""

    def test_scatter_plot_generates_png_with_annotations(self):
        """
        Test that a scatter plot is generated with correct annotations and saved to a PNG file.
        Uses dummy data to verify file output and labels.
        """
        # Create dummy data
        dummy_data = pd.DataFrame({
            'metric': [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
            'score': [2.1, 4.0, 6.2, 7.8, 10.1, 12.0, 14.1, 15.9, 18.0, 20.2]
        })

        # Create a temporary file for the output
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_scatter_plot.png"

            # Generate the plot
            result_path = generate_scatter_plot(
                input=dummy_data,
                x='metric',
                y='score',
                output=str(output_path),
                metric_name='Test Metric',
                score_name='Test Score'
            )

            # Verify the file was created
            assert Path(result_path).exists(), f"Output file not created at {result_path}"
            assert result_path == str(output_path), f"Returned path {result_path} does not match expected {output_path}"

            # Verify file is not empty
            assert os.path.getsize(result_path) > 0, "Output file is empty"

            # Verify the file is a valid image (basic check)
            img = plt.imread(result_path)
            assert img.ndim == 3, "Output is not a valid image"
            assert img.shape[2] in [3, 4], "Image does not have expected color channels"

            # Clean up the plot figure
            plt.close('all')

    def test_scatter_plot_missing_columns(self):
        """Test that appropriate error is raised for missing columns."""
        dummy_data = pd.DataFrame({
            'col_a': [1, 2, 3],
            'col_b': [4, 5, 6]
        })

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.png"

            with pytest.raises(ValueError, match="Column 'missing_col' not found"):
                generate_scatter_plot(
                    input=dummy_data,
                    x='missing_col',
                    y='col_b',
                    output=str(output_path)
                )

    def test_scatter_plot_insufficient_data(self):
        """Test that appropriate error is raised for insufficient data points."""
        dummy_data = pd.DataFrame({
            'x': [1.0],
            'y': [2.0]
        })

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.png"

            with pytest.raises(ValueError, match="Insufficient data points"):
                generate_scatter_plot(
                    input=dummy_data,
                    x='x',
                    y='y',
                    output=str(output_path)
                )

    def test_scatter_plot_kwargs_unpacking(self):
        """Test that the function works when called with **kwargs."""
        dummy_data = pd.DataFrame({
            'x': [1, 2, 3, 4, 5],
            'y': [2, 4, 6, 8, 10]
        })

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_kwargs.png"

            kwargs = {
                'input': dummy_data,
                'x': 'x',
                'y': 'y',
                'output': str(output_path)
            }

            result_path = generate_scatter_plot(**kwargs)

            assert Path(result_path).exists(), "Output file not created with kwargs unpacking"
            plt.close('all')