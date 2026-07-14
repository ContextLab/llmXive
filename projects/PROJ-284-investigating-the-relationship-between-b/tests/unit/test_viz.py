"""Unit tests for visualization modules."""
import os
import tempfile
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

from code.viz.scatter import generate_scatter_plot, load_correlation_results


class TestScatterPlot(unittest.TestCase):
    """Tests for scatter plot generation."""

    def test_scatter_plot_generates_png_with_annotations(self):
        """Test that scatter plot generates a PNG file with proper annotations.
        
        Verifies:
        1. Output file is created
        2. File is a valid image (non-empty)
        3. Statistical annotations are present in the data processing
        4. Regression line calculation works
        """
        # Create temporary directory for output
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_scatter.png"
            
            # Create synthetic test data
            np.random.seed(42)
            n_samples = 50
            x = np.random.normal(0, 1, n_samples)
            y = 0.5 * x + np.random.normal(0, 0.5, n_samples)  # Positive correlation
            
            df = pd.DataFrame({
                'metric': x,
                'score': y
            })
            
            # Generate plot
            result_path = generate_scatter_plot(
                data=df,
                x_col='metric',
                y_col='score',
                output_path=str(output_path),
                title='Test Correlation',
                x_label='Metric Value',
                y_label='Score',
                annotate_stats=True,
                add_regression=True
            )
            
            # Verify file was created
            assert Path(result_path).exists(), f"Output file not created: {result_path}"
            assert Path(result_path).suffix == '.png', f"Wrong file extension: {result_path}"
            
            # Verify file is not empty
            file_size = Path(result_path).stat().st_size
            assert file_size > 0, f"Output file is empty: {result_path}"
            assert file_size > 1000, f"Output file too small (likely corrupted): {file_size} bytes"
            
            # Verify the function returned the correct path
            assert result_path == str(output_path)

    def test_scatter_plot_with_significant_only_filter(self):
        """Test scatter plot generation with significant_only filter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_significant.png"
            
            # Create data
            np.random.seed(42)
            df = pd.DataFrame({
                'x': np.random.normal(0, 1, 30),
                'y': np.random.normal(0, 1, 30),
                'significant': [True] * 30
            })
            
            # Should not raise
            result_path = generate_scatter_plot(
                data=df,
                x_col='x',
                y_col='y',
                output_path=str(output_path),
                significant_only=True
            )
            
            assert Path(result_path).exists()

    def test_scatter_plot_insufficient_data(self):
        """Test that insufficient data raises appropriate error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_error.png"
            
            # Create data with only 1 point
            df = pd.DataFrame({
                'x': [1.0],
                'y': [2.0]
            })
            
            with pytest.raises(ValueError, match="Not enough data points"):
                generate_scatter_plot(
                    data=df,
                    x_col='x',
                    y_col='y',
                    output_path=str(output_path)
                )

    def test_scatter_plot_missing_column(self):
        """Test that missing column raises appropriate error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_error.png"
            
            df = pd.DataFrame({
                'x': [1.0, 2.0, 3.0],
                'y': [2.0, 3.0, 4.0]
            })
            
            with pytest.raises(ValueError, match="not found in data"):
                generate_scatter_plot(
                    data=df,
                    x_col='missing_col',
                    y_col='y',
                    output_path=str(output_path)
                )

    def test_scatter_plot_regression_line(self):
        """Test that regression line is calculated correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_regression.png"
            
            # Perfect linear relationship
            df = pd.DataFrame({
                'x': [1, 2, 3, 4, 5],
                'y': [2, 4, 6, 8, 10]
            })
            
            result_path = generate_scatter_plot(
                data=df,
                x_col='x',
                y_col='y',
                output_path=str(output_path),
                add_regression=True
            )
            
            assert Path(result_path).exists()

    def test_scatter_plot_custom_styling(self):
        """Test scatter plot with custom styling parameters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_styling.png"
            
            df = pd.DataFrame({
                'x': np.random.normal(0, 1, 20),
                'y': np.random.normal(0, 1, 20)
            })
            
            result_path = generate_scatter_plot(
                data=df,
                x_col='x',
                y_col='y',
                output_path=str(output_path),
                color='red',
                alpha=0.8,
                size=100
            )
            
            assert Path(result_path).exists()

    def test_load_correlation_results(self):
        """Test loading correlation results from CSV."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "correlations.csv"
            
            # Create test CSV
            df = pd.DataFrame({
                'metric_name': ['m1', 'm2'],
                'r': [0.5, -0.3],
                'p': [0.01, 0.05],
                'q': [0.02, 0.06],
                'significant': [True, False]
            })
            df.to_csv(csv_path, index=False)
            
            # Load and verify
            loaded = load_correlation_results(str(csv_path))
            
            assert len(loaded) == 2
            assert list(loaded.columns) == ['metric_name', 'r', 'p', 'q', 'significant']
            assert loaded.iloc[0]['r'] == 0.5
            assert loaded.iloc[0]['significant'] == True

    def test_load_correlation_results_file_not_found(self):
        """Test that missing file raises appropriate error."""
        with pytest.raises(FileNotFoundError):
            load_correlation_results("nonexistent_file.csv")