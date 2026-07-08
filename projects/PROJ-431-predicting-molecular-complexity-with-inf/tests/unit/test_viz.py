"""
Unit tests for viz.py plot rendering logic.

Tests verify that:
1. Regression metrics (slope, intercept, r_squared) are computed correctly.
2. Plot generation creates figures with correct labels, regression lines, and R² annotations.
3. The plot_all_correlations function handles multiple columns gracefully.
"""
import os
import tempfile
import pytest
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock
from matplotlib.figure import Figure

# Import the specific functions to test
from viz import compute_regression_metrics, plot_entropy_vs_property, plot_all_correlations


class TestComputeRegressionMetrics:
    """Tests for the compute_regression_metrics function."""

    def test_perfect_linear_relationship(self):
        """Test with a perfect y = 2x + 1 relationship."""
        x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y = np.array([3.0, 5.0, 7.0, 9.0, 11.0])

        slope, intercept, r_squared = compute_regression_metrics(x, y)

        assert np.isclose(slope, 2.0)
        assert np.isclose(intercept, 1.0)
        assert np.isclose(r_squared, 1.0)

    def test_no_correlation(self):
        """Test with uncorrelated data (R² should be low)."""
        np.random.seed(42)
        x = np.random.rand(100)
        y = np.random.rand(100)

        slope, intercept, r_squared = compute_regression_metrics(x, y)

        # R² should be close to 0 for uncorrelated data
        assert r_squared < 0.1

    def test_negative_correlation(self):
        """Test with a negative linear relationship."""
        x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y = np.array([5.0, 4.0, 3.0, 2.0, 1.0])

        slope, intercept, r_squared = compute_regression_metrics(x, y)

        assert np.isclose(slope, -1.0)
        assert np.isclose(intercept, 6.0)
        assert np.isclose(r_squared, 1.0)

    def test_empty_arrays(self):
        """Test handling of empty arrays."""
        x = np.array([])
        y = np.array([])

        with pytest.raises(ValueError):
            compute_regression_metrics(x, y)

    def test_single_point(self):
        """Test handling of a single data point (division by zero in R²)."""
        x = np.array([1.0])
        y = np.array([1.0])

        with pytest.raises(ValueError):
            compute_regression_metrics(x, y)


class TestPlotEntropyVsProperty:
    """Tests for the plot_entropy_vs_property function."""

    @pytest.fixture
    def sample_data(self):
        """Create a sample DataFrame for testing."""
        return pd.DataFrame({
            'atom_entropy': [1.0, 2.0, 3.0, 4.0, 5.0],
            'logS': [1.5, 2.0, 2.5, 3.0, 3.5]
        })

    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary directory for output files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    def test_plot_generates_figure(self, sample_data, temp_output_dir):
        """Test that the function generates a valid matplotlib Figure."""
        output_path = os.path.join(temp_output_dir, "test_plot.png")

        fig = plot_entropy_vs_property(
            df=sample_data,
            x_col='atom_entropy',
            y_col='logS',
            output_path=output_path,
            title="Test Plot"
        )

        assert isinstance(fig, Figure)
        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) > 0

    def test_plot_has_correct_labels(self, sample_data, temp_output_dir):
        """Test that the plot has correct axis labels and title."""
        output_path = os.path.join(temp_output_dir, "test_plot.png")

        fig = plot_entropy_vs_property(
            df=sample_data,
            x_col='atom_entropy',
            y_col='logS',
            output_path=output_path,
            title="Custom Title"
        )

        ax = fig.gca()

        # Check title
        assert ax.get_title() == "Custom Title"

        # Check axis labels (format: "Column Name (unit)" or just "Column Name")
        # The function should set these based on column names
        assert 'atom_entropy' in ax.get_xlabel()
        assert 'logS' in ax.get_ylabel()

    def test_plot_contains_regression_line(self, sample_data, temp_output_dir):
        """Test that the plot contains a regression line."""
        output_path = os.path.join(temp_output_dir, "test_plot.png")

        fig = plot_entropy_vs_property(
            df=sample_data,
            x_col='atom_entropy',
            y_col='logS',
            output_path=output_path
        )

        ax = fig.gca()
        lines = ax.get_lines()

        # Should have at least one line (the regression line)
        # The scatter points are usually markers, not lines
        assert len(lines) >= 1

    def test_plot_contains_r_squared_annotation(self, sample_data, temp_output_dir):
        """Test that the plot contains an R² annotation."""
        output_path = os.path.join(temp_output_dir, "test_plot.png")

        fig = plot_entropy_vs_property(
            df=sample_data,
            x_col='atom_entropy',
            y_col='logS',
            output_path=output_path
        )

        ax = fig.gca()
        texts = [child for child in ax.get_children() if isinstance(child, type(ax.text(0, 0, "")))]

        # Check if any text contains R² or r2
        has_r_squared = any('R²' in t.get_text() or 'r²' in t.get_text() or 'R2' in t.get_text() for t in texts)
        assert has_r_squared, "Plot should contain an R² annotation"

    def test_plot_handles_nan_values(self, temp_output_dir):
        """Test that the function handles NaN values gracefully."""
        data_with_nan = pd.DataFrame({
            'atom_entropy': [1.0, np.nan, 3.0, 4.0, 5.0],
            'logS': [1.5, 2.0, np.nan, 3.0, 3.5]
        })

        output_path = os.path.join(temp_output_dir, "test_plot_nan.png")

        # Should not raise an exception
        fig = plot_entropy_vs_property(
            df=data_with_nan,
            x_col='atom_entropy',
            y_col='logS',
            output_path=output_path
        )

        assert fig is not None
        assert os.path.exists(output_path)


class TestPlotAllCorrelations:
    """Tests for the plot_all_correlations function."""

    @pytest.fixture
    def sample_data_multi(self):
        """Create a sample DataFrame with multiple entropy columns."""
        return pd.DataFrame({
            'atom_entropy': [1.0, 2.0, 3.0, 4.0, 5.0],
            'bond_entropy': [0.5, 1.0, 1.5, 2.0, 2.5],
            'logS': [1.5, 2.0, 2.5, 3.0, 3.5],
            'logP': [2.0, 2.5, 3.0, 3.5, 4.0]
        })

    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary directory for output files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    def test_generates_multiple_plots(self, sample_data_multi, temp_output_dir):
        """Test that the function generates plots for all combinations."""
        output_dir = temp_output_dir

        plot_paths = plot_all_correlations(
            df=sample_data_multi,
            entropy_cols=['atom_entropy', 'bond_entropy'],
            property_cols=['logS', 'logP'],
            output_dir=output_dir
        )

        # Should generate 2 entropy * 2 property = 4 plots
        assert len(plot_paths) == 4

        # Verify all files exist
        for path in plot_paths:
            assert os.path.exists(path)
            assert os.path.getsize(path) > 0

    def test_plot_filenames_follow_convention(self, sample_data_multi, temp_output_dir):
        """Test that generated filenames follow the expected naming convention."""
        output_dir = temp_output_dir

        plot_paths = plot_all_correlations(
            df=sample_data_multi,
            entropy_cols=['atom_entropy'],
            property_cols=['logS'],
            output_dir=output_dir
        )

        # Should contain a file named like "atom_entropy_vs_logS.png"
        assert any('atom_entropy_vs_logS.png' in p for p in plot_paths)

    def test_handles_missing_columns_gracefully(self, temp_output_dir):
        """Test behavior when requested columns are missing."""
        data_missing = pd.DataFrame({
            'atom_entropy': [1.0, 2.0, 3.0],
            'logS': [1.5, 2.0, 2.5]
        })

        output_dir = temp_output_dir

        # Should not raise an exception for missing columns (e.g., 'bond_entropy')
        plot_paths = plot_all_correlations(
            df=data_missing,
            entropy_cols=['atom_entropy', 'bond_entropy'],  # bond_entropy missing
            property_cols=['logS'],
            output_dir=output_dir
        )

        # Should still generate the valid plot
        assert len(plot_paths) >= 1