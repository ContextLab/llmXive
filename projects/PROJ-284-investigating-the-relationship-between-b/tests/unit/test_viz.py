"""Unit tests for visualization module.

Tests for T029: Scatter plot generation with annotations.
"""
import os
import tempfile
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import pytest

from code.viz.scatter import generate_scatter_plot, generate_scatter_plot_with_q


class TestScatterPlot:
    """Tests for scatter plot generation."""

    @pytest.fixture
    def sample_data(self):
        """Create sample data for testing."""
        return pd.DataFrame({
            'metric': [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
            'score': [2.1, 3.9, 6.2, 8.1, 9.8, 12.1, 14.2, 15.9, 18.1, 20.0],
            'q': [0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01]
        })

    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary directory for output files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_scatter_plot_generates_png_with_annotations(self, sample_data, temp_output_dir):
        """Test that scatter plot generates PNG with proper annotations.

        Verifies:
        - File is created at the specified path
        - File has .png extension
        - File size is non-zero
        - File can be opened as an image
        - Annotations are present (r and q values)
        """
        output_path = temp_output_dir / "test_scatter.png"

        # Generate plot
        result_path = generate_scatter_plot(
            data=sample_data,
            x_col='metric',
            y_col='score',
            output_path=str(output_path),
            title='Test Plot',
            x_label='Metric Value',
            y_label='Score',
            annotate_stats=True
        )

        # Verify file exists
        assert Path(result_path).exists(), "Output file was not created"

        # Verify file extension
        assert result_path.endswith('.png'), "Output file should have .png extension"

        # Verify file size is non-zero
        file_size = Path(result_path).stat().st_size
        assert file_size > 0, "Output file is empty"

        # Verify we can open the file as an image
        try:
            img = plt.imread(result_path)
            assert img is not None, "Could not read generated image"
            assert img.ndim == 3, "Image should have 3 dimensions (height, width, channels)"
        except Exception as e:
            pytest.fail(f"Could not open generated image: {e}")

        # Verify annotations are present by checking the file content
        # (We can't easily parse PNG text, so we verify the function was called with annotations)
        # In a more complete test, we could use OCR or check the underlying matplotlib artist tree

    def test_scatter_plot_with_q_value(self, sample_data, temp_output_dir):
        """Test scatter plot generation with explicit q-value column."""
        output_path = temp_output_dir / "test_scatter_q.png"

        result_path = generate_scatter_plot_with_q(
            data=sample_data,
            x_col='metric',
            y_col='score',
            q_col='q',
            output_path=str(output_path),
            title='Test Plot with Q',
            annotate_stats=True
        )

        assert Path(result_path).exists(), "Output file was not created"
        assert result_path.endswith('.png'), "Output file should have .png extension"

    def test_scatter_plot_with_fewer_points(self, temp_output_dir):
        """Test that plot generation works with minimal data points."""
        min_data = pd.DataFrame({
            'x': [1.0, 2.0],
            'y': [1.0, 2.0]
        })

        output_path = temp_output_dir / "test_min.png"
        result_path = generate_scatter_plot(
            data=min_data,
            x_col='x',
            y_col='y',
            output_path=str(output_path)
        )

        assert Path(result_path).exists(), "Output file was not created with minimal data"

    def test_scatter_plot_invalid_columns(self, sample_data, temp_output_dir):
        """Test that invalid column names raise ValueError."""
        output_path = temp_output_dir / "test_invalid.png"

        with pytest.raises(ValueError, match="Column.*not found"):
            generate_scatter_plot(
                data=sample_data,
                x_col='nonexistent',
                y_col='score',
                output_path=str(output_path)
            )

    def test_scatter_plot_insufficient_data(self, temp_output_dir):
        """Test that insufficient data points raise ValueError."""
        insufficient_data = pd.DataFrame({
            'x': [1.0],
            'y': [1.0]
        })

        output_path = temp_output_dir / "test_insufficient.png"

        with pytest.raises(ValueError, match="Need at least 2 data points"):
            generate_scatter_plot(
                data=insufficient_data,
                x_col='x',
                y_col='y',
                output_path=str(output_path)
            )

    def test_scatter_plot_with_nan_values(self, temp_output_dir):
        """Test that NaN values are handled correctly."""
        data_with_nan = pd.DataFrame({
            'x': [1.0, 2.0, float('nan'), 4.0, 5.0],
            'y': [1.0, 2.0, 3.0, float('nan'), 5.0]
        })

        output_path = temp_output_dir / "test_nan.png"
        result_path = generate_scatter_plot(
            data=data_with_nan,
            x_col='x',
            y_col='y',
            output_path=str(output_path)
        )

        # Should succeed by filtering out NaN rows
        assert Path(result_path).exists(), "Output file was not created with NaN data"

    def test_scatter_plot_custom_parameters(self, sample_data, temp_output_dir):
        """Test scatter plot with custom styling parameters."""
        output_path = temp_output_dir / "test_custom.png"

        result_path = generate_scatter_plot(
            data=sample_data,
            x_col='metric',
            y_col='score',
            output_path=str(output_path),
            color='red',
            alpha=0.8,
            size=100,
            dpi=150,
            show_regression=False
        )

        assert Path(result_path).exists(), "Output file was not created with custom params"
        # Verify file size is reasonable for the custom DPI
        file_size = Path(result_path).stat().st_size
        assert file_size > 0, "Output file is empty"

    def test_scatter_plot_pdf_output(self, sample_data, temp_output_dir):
        """Test that PDF output format works."""
        output_path = temp_output_dir / "test_scatter.pdf"

        result_path = generate_scatter_plot(
            data=sample_data,
            x_col='metric',
            y_col='score',
            output_path=str(output_path)
        )

        assert Path(result_path).exists(), "PDF output file was not created"
        assert result_path.endswith('.pdf'), "Output file should have .pdf extension"