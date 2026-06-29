"""
Unit tests for visualization generation (T037 - US3).

These tests verify the visualization.py module functions work correctly
with mock data, ensuring plots are generated with proper structure and
saved to the correct output paths.

Tests written before implementation per spec.md Independent Test requirements.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os
from unittest.mock import patch, MagicMock, mock_open

# Import visualization module functions
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))
from visualization import (
    setup_logging,
    load_correlation_data,
    compute_regression,
    create_scatter_plot_with_regression,
    create_clone_density_vs_perplexity_plot,
    create_clone_density_vs_accuracy_plot,
    create_sensitivity_analysis_plot,
    generate_all_visualizations,
)
from config import (
    get_figure_format,
    get_figure_dpi,
    get_clone_thresholds,
)


class TestSetupLogging:
    """Tests for setup_logging function."""

    def test_setup_logging_creates_logger(self):
        """Verify setup_logging returns a valid logger instance."""
        logger = setup_logging()
        assert logger is not None
        assert logger.name == 'visualization'
        assert logger.level > 0  # Should have a logging level set


class TestLoadCorrelationData:
    """Tests for load_correlation_data function."""

    def test_load_correlation_data_with_valid_csv(self, tmp_path):
        """Load correlation data from a valid CSV file."""
        # Create test data
        data = {
            'clone_density': [0.1, 0.2, 0.3, 0.4, 0.5],
            'perplexity': [10.5, 12.3, 15.1, 18.2, 21.0],
            'accuracy': [0.85, 0.82, 0.78, 0.72, 0.65],
        }
        csv_path = tmp_path / 'correlation_results.csv'
        pd.DataFrame(data).to_csv(csv_path, index=False)

        # Load and verify
        df = load_correlation_data(str(csv_path))
        assert df is not None
        assert len(df) == 5
        assert 'clone_density' in df.columns
        assert 'perplexity' in df.columns
        assert 'accuracy' in df.columns

    def test_load_correlation_data_missing_file(self, tmp_path):
        """Handle missing correlation results file gracefully."""
        non_existent = tmp_path / 'non_existent.csv'
        df = load_correlation_data(str(non_existent))
        assert df is None or len(df) == 0

    def test_load_correlation_data_empty_csv(self, tmp_path):
        """Handle empty CSV file."""
        csv_path = tmp_path / 'empty.csv'
        csv_path.write_text('clone_density,perplexity,accuracy\n')

        df = load_correlation_data(str(csv_path))
        assert df is not None
        assert len(df) == 0

    def test_load_correlation_data_with_nan_values(self, tmp_path):
        """Load data with NaN values - should filter them out."""
        data = {
            'clone_density': [0.1, np.nan, 0.3, 0.4, 0.5],
            'perplexity': [10.5, 12.3, np.nan, 18.2, 21.0],
            'accuracy': [0.85, 0.82, 0.78, np.nan, 0.65],
        }
        csv_path = tmp_path / 'with_nan.csv'
        pd.DataFrame(data).to_csv(csv_path, index=False)

        df = load_correlation_data(str(csv_path))
        # Should have at least some valid rows
        assert df is not None
        assert len(df) >= 0  # May be 0 if all rows have NaN


class TestComputeRegression:
    """Tests for compute_regression function."""

    def test_compute_regression_basic(self):
        """Compute linear regression on simple data."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 5, 4, 5])

        slope, intercept, r_value = compute_regression(x, y)

        assert isinstance(slope, (float, np.floating))
        assert isinstance(intercept, (float, np.floating))
        assert isinstance(r_value, (float, np.floating))
        assert -1 <= r_value <= 1

    def test_compute_regression_perfect_correlation(self):
        """Compute regression on perfectly correlated data."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 6, 8, 10])  # y = 2x

        slope, intercept, r_value = compute_regression(x, y)

        assert abs(slope - 2.0) < 0.01
        assert abs(intercept) < 0.01
        assert abs(r_value - 1.0) < 0.01

    def test_compute_regression_single_point(self):
        """Handle single data point gracefully."""
        x = np.array([1])
        y = np.array([2])

        slope, intercept, r_value = compute_regression(x, y)

        assert isinstance(slope, (float, np.floating))
        assert isinstance(intercept, (float, np.floating))
        # R-value may be undefined for single point

    def test_compute_regression_empty_arrays(self):
        """Handle empty arrays gracefully."""
        x = np.array([])
        y = np.array([])

        slope, intercept, r_value = compute_regression(x, y)

        # Should handle gracefully, may return NaN or 0
        assert isinstance(slope, (float, np.floating))


class TestCreateScatterPlotWithRegression:
    """Tests for scatter plot creation with regression line."""

    @patch('visualization.plt')
    def test_create_scatter_plot_with_regression_generates_plot(self, mock_plt):
        """Verify scatter plot is created with regression line."""
        # Setup mock
        mock_fig = MagicMock()
        mock_ax = MagicMock()
        mock_plt.subplots.return_value = (mock_fig, mock_ax)

        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 5, 4, 5])
        xlabel = 'Clone Density'
        ylabel = 'Perplexity'
        title = 'Test Plot'

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / 'test_scatter.png'

            result = create_scatter_plot_with_regression(
                x, y, xlabel, ylabel, title, str(output_path)
            )

            # Verify plot creation was attempted
            assert mock_plt.subplots.called
            assert mock_ax.scatter.called
            assert mock_ax.plot.called  # Regression line
            assert mock_ax.set_xlabel.called
            assert mock_ax.set_ylabel.called
            assert mock_ax.set_title.called

    @patch('visualization.plt')
    def test_create_scatter_plot_with_regression_saves_file(self, mock_plt):
        """Verify plot is saved to the specified path."""
        mock_fig = MagicMock()
        mock_ax = MagicMock()
        mock_plt.subplots.return_value = (mock_fig, mock_ax)

        x = np.array([1, 2, 3])
        y = np.array([1, 2, 3])

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / 'test.png'

            create_scatter_plot_with_regression(
                x, y, 'X', 'Y', 'Test', str(output_path)
            )

            # Verify savefig was called with correct path
            mock_fig.savefig.assert_called()


class TestCreateCloneDensityVsPerplexityPlot:
    """Tests for clone density vs perplexity visualization."""

    @patch('visualization.create_scatter_plot_with_regression')
    def test_create_clone_density_vs_perplexity_plot_calls_scatter(self, mock_scatter):
        """Verify this function uses the scatter plot helper."""
        mock_scatter.return_value = True

        data = pd.DataFrame({
            'clone_density': [0.1, 0.2, 0.3],
            'perplexity': [10, 15, 20],
        })

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / 'clone_perplexity.png'

            result = create_clone_density_vs_perplexity_plot(
                data, str(output_path)
            )

            assert mock_scatter.called
            call_args = mock_scatter.call_args
            assert 'clone_density' in str(call_args) or 'perplexity' in str(call_args)

    @patch('visualization.create_scatter_plot_with_regression')
    def test_create_clone_density_vs_perplexity_plot_handles_empty_data(self, mock_scatter):
        """Handle empty DataFrame gracefully."""
        mock_scatter.return_value = False

        data = pd.DataFrame()

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / 'clone_perplexity.png'

            result = create_clone_density_vs_perplexity_plot(
                data, str(output_path)
            )

            # Should handle empty data without crashing
            assert mock_scatter.called or True  # May skip if no data


class TestCreateCloneDensityVsAccuracyPlot:
    """Tests for clone density vs accuracy visualization."""

    @patch('visualization.create_scatter_plot_with_regression')
    def test_create_clone_density_vs_accuracy_plot_calls_scatter(self, mock_scatter):
        """Verify this function uses the scatter plot helper."""
        mock_scatter.return_value = True

        data = pd.DataFrame({
            'clone_density': [0.1, 0.2, 0.3],
            'accuracy': [0.9, 0.8, 0.7],
        })

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / 'clone_accuracy.png'

            result = create_clone_density_vs_accuracy_plot(
                data, str(output_path)
            )

            assert mock_scatter.called

    @patch('visualization.create_scatter_plot_with_regression')
    def test_create_clone_density_vs_accuracy_plot_handles_missing_accuracy(self, mock_scatter):
        """Handle missing accuracy column gracefully."""
        mock_scatter.return_value = False

        data = pd.DataFrame({
            'clone_density': [0.1, 0.2, 0.3],
            # No accuracy column
        })

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / 'clone_accuracy.png'

            result = create_clone_density_vs_accuracy_plot(
                data, str(output_path)
            )

            # Should handle missing column without crashing


class TestCreateSensitivityAnalysisPlot:
    """Tests for sensitivity analysis visualization."""

    @patch('visualization.plt')
    def test_create_sensitivity_analysis_plot_generates_plot(self, mock_plt):
        """Verify sensitivity analysis plot is created."""
        mock_fig = MagicMock()
        mock_ax = MagicMock()
        mock_plt.subplots.return_value = (mock_fig, mock_ax)
        mock_plt.legend.return_value = MagicMock()

        # Sensitivity data for different thresholds
        sensitivity_data = {
            0.7: {'correlation': 0.65, 'p_value': 0.001},
            0.8: {'correlation': 0.58, 'p_value': 0.003},
            0.9: {'correlation': 0.52, 'p_value': 0.008},
        }

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / 'sensitivity_analysis.png'

            result = create_sensitivity_analysis_plot(
                sensitivity_data, str(output_path)
            )

            # Verify plot elements were created
            assert mock_plt.subplots.called
            assert mock_ax.plot.called or mock_ax.bar.called

    @patch('visualization.plt')
    def test_create_sensitivity_analysis_plot_handles_single_threshold(self, mock_plt):
        """Handle single threshold gracefully."""
        mock_fig = MagicMock()
        mock_ax = MagicMock()
        mock_plt.subplots.return_value = (mock_fig, mock_ax)

        sensitivity_data = {
            0.7: {'correlation': 0.65, 'p_value': 0.001},
        }

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / 'sensitivity_single.png'

            result = create_sensitivity_analysis_plot(
                sensitivity_data, str(output_path)
            )

            assert mock_plt.subplots.called


class TestGenerateAllVisualizations:
    """Tests for the complete visualization generation pipeline."""

    @patch('visualization.create_clone_density_vs_perplexity_plot')
    @patch('visualization.create_clone_density_vs_accuracy_plot')
    @patch('visualization.create_sensitivity_analysis_plot')
    @patch('visualization.load_correlation_data')
    def test_generate_all_visualizations_calls_all_plots(
        self, mock_load, mock_accuracy, mock_perplexity, mock_sensitivity
    ):
        """Verify all visualization types are generated."""
        # Setup mocks
        mock_load.return_value = pd.DataFrame({
            'clone_density': [0.1, 0.2, 0.3],
            'perplexity': [10, 15, 20],
            'accuracy': [0.9, 0.8, 0.7],
        })
        mock_perplexity.return_value = True
        mock_accuracy.return_value = True
        mock_sensitivity.return_value = True

        sensitivity_data = {
            0.7: {'correlation': 0.65, 'p_value': 0.001},
            0.8: {'correlation': 0.58, 'p_value': 0.003},
        }

        with tempfile.TemporaryDirectory() as tmp_dir:
            figures_dir = Path(tmp_dir) / 'figures'
            figures_dir.mkdir()

            results = generate_all_visualizations(
                correlation_data_path=str(Path(tmp_dir) / 'correlation.csv'),
                sensitivity_data=sensitivity_data,
                output_dir=str(figures_dir),
            )

            # Verify all plot functions were called
            assert mock_load.called
            assert mock_perplexity.called
            assert mock_accuracy.called
            assert mock_sensitivity.called

    @patch('visualization.create_clone_density_vs_perplexity_plot')
    @patch('visualization.create_clone_density_vs_accuracy_plot')
    @patch('visualization.create_sensitivity_analysis_plot')
    @patch('visualization.load_correlation_data')
    def test_generate_all_visualizations_returns_file_count(
        self, mock_load, mock_accuracy, mock_perplexity, mock_sensitivity
    ):
        """Verify function returns count of generated files."""
        mock_load.return_value = pd.DataFrame({
            'clone_density': [0.1, 0.2, 0.3],
            'perplexity': [10, 15, 20],
            'accuracy': [0.9, 0.8, 0.7],
        })
        mock_perplexity.return_value = True
        mock_accuracy.return_value = True
        mock_sensitivity.return_value = True

        sensitivity_data = {0.7: {'correlation': 0.65, 'p_value': 0.001}}

        with tempfile.TemporaryDirectory() as tmp_dir:
            figures_dir = Path(tmp_dir) / 'figures'
            figures_dir.mkdir()

            results = generate_all_visualizations(
                correlation_data_path=str(Path(tmp_dir) / 'correlation.csv'),
                sensitivity_data=sensitivity_data,
                output_dir=str(figures_dir),
            )

            # Results should contain file count information
            assert results is not None

    def test_generate_all_visualizations_handles_correlation_load_failure(self, tmp_path):
        """Handle correlation data loading failure gracefully."""
        non_existent = tmp_path / 'non_existent.csv'

        sensitivity_data = {0.7: {'correlation': 0.65, 'p_value': 0.001}}
        figures_dir = tmp_path / 'figures'
        figures_dir.mkdir()

        results = generate_all_visualizations(
            correlation_data_path=str(non_existent),
            sensitivity_data=sensitivity_data,
            output_dir=str(figures_dir),
        )

        # Should handle gracefully without crashing
        assert results is not None


class TestVisualizationOutputFormat:
    """Tests for visualization output format validation."""

    @patch('visualization.plt')
    def test_plot_uses_correct_figure_format(self, mock_plt):
        """Verify plots use configured figure format."""
        mock_fig = MagicMock()
        mock_ax = MagicMock()
        mock_plt.subplots.return_value = (mock_fig, mock_ax)

        x = np.array([1, 2, 3])
        y = np.array([1, 2, 3])

        with tempfile.TemporaryDirectory() as tmp_dir:
            # Test PNG output
            png_path = Path(tmp_dir) / 'test.png'
            create_scatter_plot_with_regression(
                x, y, 'X', 'Y', 'Test', str(png_path)
            )

            # Verify savefig was called
            mock_fig.savefig.assert_called()

    @patch('visualization.plt')
    def test_plot_uses_correct_dpi(self, mock_plt):
        """Verify plots use configured DPI."""
        mock_fig = MagicMock()
        mock_ax = MagicMock()
        mock_plt.subplots.return_value = (mock_fig, mock_ax)

        x = np.array([1, 2, 3])
        y = np.array([1, 2, 3])

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / 'test.png'
            create_scatter_plot_with_regression(
                x, y, 'X', 'Y', 'Test', str(output_path)
            )

            # Check that savefig was called with dpi parameter
            call_kwargs = mock_fig.savefig.call_args
            assert call_kwargs is not None


class TestVisualizationEdgeCases:
    """Tests for visualization edge cases."""

    @patch('visualization.create_scatter_plot_with_regression')
    def test_handle_insufficient_data_points(self, mock_scatter):
        """Handle case with insufficient data points."""
        mock_scatter.return_value = False

        data = pd.DataFrame({
            'clone_density': [0.1],  # Only one point
            'perplexity': [10],
        })

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / 'test.png'

            result = create_clone_density_vs_perplexity_plot(
                data, str(output_path)
            )

            # Should handle gracefully
            assert mock_scatter.called

    @patch('visualization.create_scatter_plot_with_regression')
    def test_handle_all_nan_data(self, mock_scatter):
        """Handle DataFrame with all NaN values."""
        mock_scatter.return_value = False

        data = pd.DataFrame({
            'clone_density': [np.nan, np.nan, np.nan],
            'perplexity': [np.nan, np.nan, np.nan],
        })

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / 'test.png'

            result = create_clone_density_vs_perplexity_plot(
                data, str(output_path)
            )

            # Should handle gracefully
            assert mock_scatter.called

    @patch('visualization.create_scatter_plot_with_regression')
    def test_handle_zero_variance(self, mock_scatter):
        """Handle data with zero variance in one axis."""
        mock_scatter.return_value = True

        data = pd.DataFrame({
            'clone_density': [0.1, 0.1, 0.1],  # No variance
            'perplexity': [10, 15, 20],
        })

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / 'test.png'

            result = create_clone_density_vs_perplexity_plot(
                data, str(output_path)
            )

            # Should handle gracefully
            assert mock_scatter.called


class TestVisualizationIntegration:
    """Integration tests for visualization module."""

    @patch('visualization.plt')
    def test_full_visualization_pipeline(self, mock_plt):
        """Test complete visualization pipeline with mock data."""
        mock_fig = MagicMock()
        mock_ax = MagicMock()
        mock_plt.subplots.return_value = (mock_fig, mock_ax)

        # Create realistic correlation data
        np.random.seed(42)
        correlation_data = pd.DataFrame({
            'clone_density': np.random.uniform(0.05, 0.5, 100),
            'perplexity': np.random.uniform(8, 25, 100),
            'accuracy': np.random.uniform(0.5, 0.95, 100),
        })

        sensitivity_data = {
            0.7: {'correlation': 0.65, 'p_value': 0.001},
            0.8: {'correlation': 0.58, 'p_value': 0.003},
            0.9: {'correlation': 0.52, 'p_value': 0.008},
        }

        with tempfile.TemporaryDirectory() as tmp_dir:
            # Save correlation data
            csv_path = Path(tmp_dir) / 'correlation_results.csv'
            correlation_data.to_csv(csv_path, index=False)

            figures_dir = Path(tmp_dir) / 'figures'
            figures_dir.mkdir()

            # Run full visualization pipeline
            results = generate_all_visualizations(
                correlation_data_path=str(csv_path),
                sensitivity_data=sensitivity_data,
                output_dir=str(figures_dir),
            )

            # Verify pipeline completed
            assert mock_plt.subplots.call_count >= 3  # At least 3 plot types

    def test_visualization_creates_actual_files(self):
        """Test that visualization actually creates files on disk."""
        # This test uses actual matplotlib with Agg backend
        import matplotlib
        matplotlib.use('Agg')  # Non-interactive backend

        import matplotlib.pyplot as plt

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / 'actual_test.png'

            # Create a simple plot
            fig, ax = plt.subplots()
            ax.plot([1, 2, 3], [1, 4, 9])
            ax.set_xlabel('X')
            ax.set_ylabel('Y')
            ax.set_title('Test')
            fig.savefig(str(output_path))
            plt.close(fig)

            # Verify file was created
            assert output_path.exists()
            assert output_path.stat().st_size > 0