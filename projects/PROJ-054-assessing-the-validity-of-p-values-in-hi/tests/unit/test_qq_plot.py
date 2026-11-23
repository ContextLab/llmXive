"""
Unit tests for QQ-plot generation utilities in plot_qq.py.
These tests verify QQ-plot data generation and visual validation.
"""
import pytest
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for testing
import matplotlib.pyplot as plt
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from plot_qq import load_pvalue_trajectories, generate_qq_plot


class TestQQPlotGeneration:
    """Tests for T027: QQ-plot generation and visual validation."""

    def test_qq_plot_uniform_data(self):
        """Test QQ-plot for uniform p-values (should be diagonal)."""
        np.random.seed(42)
        n_samples = 1000
        pvalues = np.random.uniform(0, 1, n_samples)

        # Generate QQ-plot data
        theoretical_quantiles, empirical_quantiles = generate_qq_plot(pvalues)

        # For uniform data, empirical should match theoretical
        assert len(theoretical_quantiles) == n_samples, "Should have n_samples quantiles"
        assert len(empirical_quantiles) == n_samples, "Should have n_samples quantiles"

        # Check that points are close to diagonal
        max_deviation = np.max(np.abs(empirical_quantiles - theoretical_quantiles))
        assert max_deviation < 0.1, f"Max deviation {max_deviation} should be < 0.1 for uniform data"

    def test_qq_plot_biased_data(self):
        """Test QQ-plot for biased p-values (should show deviation)."""
        np.random.seed(42)
        n_samples = 1000
        # Anti-conservative p-values (skewed towards 0)
        pvalues = np.random.beta(0.5, 1, n_samples)

        theoretical_quantiles, empirical_quantiles = generate_qq_plot(pvalues)

        # Biased data should show deviation from diagonal, especially at low quantiles
        low_quantile_idx = int(n_samples * 0.1)
        low_theoretical = theoretical_quantiles[:low_quantile_idx]
        low_empirical = empirical_quantiles[:low_quantile_idx]

        # Empirical should be lower than theoretical for anti-conservative p-values
        mean_deviation = np.mean(low_empirical - low_theoretical)
        assert mean_deviation < 0, \
            f"Biased p-values should show negative deviation at low quantiles, got {mean_deviation}"

    def test_qq_plot_max_deviation_point(self):
        """Test that maximum deviation point is correctly identified."""
        np.random.seed(42)
        n_samples = 1000
        pvalues = np.random.beta(0.5, 1, n_samples)

        theoretical_quantiles, empirical_quantiles = generate_qq_plot(pvalues)

        # Find point of maximum deviation
        deviations = np.abs(empirical_quantiles - theoretical_quantiles)
        max_idx = np.argmax(deviations)
        max_deviation = deviations[max_idx]

        assert max_deviation > 0, "Maximum deviation should be positive"
        assert 0 <= max_idx < n_samples, "Max deviation index should be valid"

    def test_qq_plot_save_file(self):
        """Test that QQ-plot can be saved to file."""
        np.random.seed(42)
        n_samples = 1000
        pvalues = np.random.uniform(0, 1, n_samples)

        # Generate plot
        fig, ax = generate_qq_plot(pvalues, save_path=None)

        assert fig is not None, "Figure should be created"
        assert ax is not None, "Axes should be created"

        # Check that plot has expected elements
        assert len(ax.lines) > 0, "QQ-plot should have at least one line"

        # Save to temporary file
        temp_path = "/tmp/test_qq_plot.png"
        try:
            fig.savefig(temp_path)
            assert os.path.exists(temp_path), "Plot file should be saved"
            assert os.path.getsize(temp_path) > 0, "Plot file should not be empty"
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_qq_plot_highlight_max_deviation(self):
        """Test that max deviation point is highlighted in plot."""
        np.random.seed(42)
        n_samples = 1000
        pvalues = np.random.beta(0.5, 1, n_samples)

        # Generate plot with max deviation highlighting
        fig, ax = generate_qq_plot(pvalues, save_path=None)

        # Check that there are multiple line collections (diagonal + data + highlight)
        lines = ax.get_lines()
        assert len(lines) >= 2, "QQ-plot should have diagonal line and data points"

        # Verify max deviation is highlighted (red dot typically)
        collections = ax.collections
        # There should be at least one collection for the highlighted point
        assert len(collections) >= 1, "Should have at least one collection for highlighted point"

        plt.close(fig)
