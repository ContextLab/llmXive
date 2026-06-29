"""
Unit tests for visualization module.

Tests verify that scatter plots with regression lines are generated correctly.
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for tests
import matplotlib.pyplot as plt
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from visualization import (
    compute_regression,
    create_scatter_plot_with_regression,
    create_clone_density_vs_perplexity_plot,
    create_clone_density_vs_accuracy_plot,
    create_sensitivity_analysis_plot,
    load_correlation_data
)


class TestComputeRegression:
    """Tests for the compute_regression function."""

    def test_basic_regression(self):
        """Test basic regression computation with known data."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 6, 8, 10])  # Perfect linear relationship
        
        result = compute_regression(x, y)
        
        assert result is not None
        slope, intercept, r_value, p_value, std_err = result
        
        # Perfect linear relationship: slope should be 2, intercept 0, r=1
        assert abs(slope - 2.0) < 0.01
        assert abs(intercept) < 0.01
        assert abs(r_value - 1.0) < 0.001

    def test_insufficient_data(self):
        """Test regression with insufficient data points."""
        x = np.array([1])
        y = np.array([2])
        
        result = compute_regression(x, y)
        
        assert result is None

    def test_empty_arrays(self):
        """Test regression with empty arrays."""
        x = np.array([])
        y = np.array([])
        
        result = compute_regression(x, y)
        
        assert result is None

    def test_nan_handling(self):
        """Test that NaN values are filtered out."""
        x = np.array([1, 2, np.nan, 4, 5])
        y = np.array([2, 4, 6, 8, 10])
        
        result = compute_regression(x, y)
        
        assert result is not None
        # Should still compute with 4 valid points

    def test_inf_handling(self):
        """Test that infinite values are filtered out."""
        x = np.array([1, 2, np.inf, 4, 5])
        y = np.array([2, 4, 6, 8, 10])
        
        result = compute_regression(x, y)
        
        assert result is not None


class TestLoadCorrelationData:
    """Tests for loading correlation data."""

    def test_load_from_file(self, tmp_path):
        """Test loading correlation data from a valid CSV file."""
        # Create test data
        test_data = pd.DataFrame({
            'threshold': [0.7, 0.8, 0.9],
            'correlation': [0.5, 0.6, 0.7],
            'p_value': [0.01, 0.02, 0.03],
            'metric': ['perplexity', 'perplexity', 'perplexity']
        })
        
        csv_path = tmp_path / 'test_correlation.csv'
        test_data.to_csv(csv_path, index=False)
        
        result = load_correlation_data(csv_path)
        
        assert result is not None
        assert len(result) == 3
        assert 'threshold' in result.columns
        assert 'correlation' in result.columns

    def test_file_not_found(self, tmp_path):
        """Test loading from non-existent file."""
        fake_path = tmp_path / 'nonexistent.csv'
        
        result = load_correlation_data(fake_path)
        
        assert result is None


class TestCreateScatterPlotWithRegression:
    """Tests for scatter plot creation."""

    def test_basic_plot_creation(self):
        """Test basic scatter plot creation."""
        fig, ax = plt.subplots()
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 6, 8, 10])
        
        create_scatter_plot_with_regression(
            ax, x, y,
            'X Label', 'Y Label', 'Test Title',
            regression=(2.0, 0.0, 1.0, 0.0, 0.0)
        )
        
        # Verify plot elements exist
        assert len(ax.collections) > 0  # Scatter points
        assert len(ax.lines) > 0  # Regression line
        assert ax.get_xlabel() == 'X Label'
        assert ax.get_ylabel() == 'Y Label'
        assert ax.get_title() == 'Test Title'
        
        plt.close(fig)

    def test_plot_without_regression(self):
        """Test scatter plot creation without regression line."""
        fig, ax = plt.subplots()
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 6, 8, 10])
        
        create_scatter_plot_with_regression(
            ax, x, y,
            'X Label', 'Y Label', 'Test Title',
            regression=None
        )
        
        # Should have scatter points but no regression line
        assert len(ax.collections) > 0
        assert len(ax.lines) == 0  # No regression line
        
        plt.close(fig)


class TestVisualizationPlots:
    """Tests for specific visualization plot functions."""

    @pytest.fixture
    def sample_correlation_data(self):
        """Provide sample correlation data for testing."""
        return pd.DataFrame({
            'clone_density': [0.1, 0.2, 0.3, 0.4, 0.5],
            'perplexity': [10.5, 11.2, 12.1, 13.0, 14.2],
            'accuracy': [0.85, 0.82, 0.78, 0.75, 0.70]
        })

    @pytest.fixture
    def sample_sensitivity_data(self):
        """Provide sample sensitivity analysis data."""
        return pd.DataFrame({
            'threshold': [0.7, 0.8, 0.9, 0.7, 0.8, 0.9],
            'correlation': [0.5, 0.6, 0.7, 0.3, 0.4, 0.5],
            'p_value': [0.01, 0.02, 0.03, 0.05, 0.06, 0.07],
            'metric': ['perplexity', 'perplexity', 'perplexity',
                      'accuracy', 'accuracy', 'accuracy']
        })

    def test_clone_density_vs_perplexity_plot(self, sample_correlation_data, tmp_path):
        """Test clone density vs perplexity plot generation."""
        success = create_clone_density_vs_perplexity_plot(
            sample_correlation_data, tmp_path, format='png', dpi=100
        )
        
        assert success
        output_file = tmp_path / 'clone_density_vs_perplexity.png'
        assert output_file.exists()
        assert output_file.stat().st_size > 0

    def test_clone_density_vs_accuracy_plot(self, sample_correlation_data, tmp_path):
        """Test clone density vs accuracy plot generation."""
        success = create_clone_density_vs_accuracy_plot(
            sample_correlation_data, tmp_path, format='png', dpi=100
        )
        
        assert success
        output_file = tmp_path / 'clone_density_vs_accuracy.png'
        assert output_file.exists()
        assert output_file.stat().st_size > 0

    def test_sensitivity_analysis_plot(self, sample_sensitivity_data, tmp_path):
        """Test sensitivity analysis plot generation."""
        success = create_sensitivity_analysis_plot(
            sample_sensitivity_data, tmp_path, format='png', dpi=100
        )
        
        assert success
        output_file = tmp_path / 'sensitivity_analysis.png'
        assert output_file.exists()
        assert output_file.stat().st_size > 0

    def test_pdf_format_output(self, sample_correlation_data, tmp_path):
        """Test PDF format output generation."""
        success = create_clone_density_vs_perplexity_plot(
            sample_correlation_data, tmp_path, format='pdf', dpi=100
        )
        
        assert success
        output_file = tmp_path / 'clone_density_vs_perplexity.pdf'
        assert output_file.exists()
        assert output_file.stat().st_size > 0

    def test_empty_dataframe(self, tmp_path):
        """Test plot generation with empty DataFrame."""
        empty_df = pd.DataFrame(columns=['clone_density', 'perplexity'])
        
        success = create_clone_density_vs_perplexity_plot(
            empty_df, tmp_path, format='png', dpi=100
        )
        
        # Should handle gracefully (may fail or succeed with empty plot)
        # At minimum, it should not crash
        assert isinstance(success, bool)