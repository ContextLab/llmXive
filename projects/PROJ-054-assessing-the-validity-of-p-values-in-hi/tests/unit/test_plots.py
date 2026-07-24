"""
Unit tests for QQ-plot generation and visual validation.

This module tests the QQ-plot generation logic for p-value distributions.
It verifies that the plotting functions produce valid matplotlib figures
and that the data points are calculated correctly against a uniform reference.
"""

import os
import tempfile
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for testing
import matplotlib.pyplot as plt
import numpy as np
import pytest
from scipy import stats

from code.analyze_pvalues import generate_qq_plot, calculate_qq_data


class TestCalculateQQData:
    """Tests for the data calculation logic behind QQ-plots."""

    def test_uniform_pvalues_match_identity(self):
        """
        If p-values are perfectly uniform, the QQ-plot points should lie
        exactly on the identity line (sorted p-values vs theoretical quantiles).
        """
        n = 100
        # Generate perfect uniform p-values
        p_values = np.linspace(1 / (n + 1), n / (n + 1), n)
        
        observed, theoretical = calculate_qq_data(p_values)
        
        # They should be identical for perfect uniform data
        np.testing.assert_array_almost_equal(observed, theoretical, decimal=10)

    def test_anti_conservative_bias(self):
        """
        If p-values are biased towards 0 (anti-conservative), the observed
        quantiles should be lower than the theoretical quantiles at the left tail.
        """
        n = 100
        # Simulate anti-conservative p-values (more small values than expected)
        # Using a Beta distribution with alpha < 1 to skew towards 0
        p_values = np.random.beta(0.5, 1, size=n)
        p_values.sort()
        
        observed, theoretical = calculate_qq_data(p_values)
        
        # At the left tail (first 10%), observed should be significantly lower
        # than theoretical (which is roughly uniform)
        tail_idx = int(n * 0.1)
        assert np.mean(observed[:tail_idx]) < np.mean(theoretical[:tail_idx]), \
            "Anti-conservative bias not detected: observed tail is not lower than theoretical"

    def test_input_validation(self):
        """Test that invalid inputs raise appropriate errors."""
        with pytest.raises(ValueError):
            calculate_qq_data(np.array([]))
        
        with pytest.raises(ValueError):
            calculate_qq_data(np.array([-0.1, 0.5, 1.2]))  # Out of bounds

class TestGenerateQQPlot:
    """Tests for the QQ-plot generation function."""

    def test_plot_creation(self):
        """Verify that generate_qq_plot returns a valid figure and axes."""
        p_values = np.random.uniform(0, 1, 100)
        p_values.sort()
        
        fig, ax = generate_qq_plot(p_values)
        
        assert isinstance(fig, plt.Figure)
        assert isinstance(ax, plt.Axes)
        
        # Clean up
        plt.close(fig)

    def test_plot_saves_to_disk(self):
        """Verify that the plot can be saved to a file."""
        p_values = np.random.uniform(0, 1, 100)
        p_values.sort()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_qq_plot.png")
            
            fig, ax = generate_qq_plot(p_values, output_path=output_path)
            
            assert os.path.exists(output_path), f"Plot file not created at {output_path}"
            assert os.path.getsize(output_path) > 0, "Plot file is empty"
            
            plt.close(fig)

    def test_identity_line_present(self):
        """Verify that the identity line (y=x) is present in the plot."""
        p_values = np.random.uniform(0, 1, 100)
        p_values.sort()
        
        fig, ax = generate_qq_plot(p_values)
        
        # Find lines in the axes
        lines = ax.get_lines()
        assert len(lines) >= 2, "Expected at least 2 lines (data and identity)"
        
        # The last line is usually the identity line
        identity_line = lines[-1]
        x_data = identity_line.get_xdata()
        y_data = identity_line.get_ydata()
        
        # Check if it's roughly y=x
        np.testing.assert_array_almost_equal(x_data, y_data, decimal=10)
        
        plt.close(fig)

    def test_labels_and_title(self):
        """Verify that the plot has correct labels and title."""
        p_values = np.random.uniform(0, 1, 100)
        p_values.sort()
        
        fig, ax = generate_qq_plot(p_values, title="Test Title")
        
        assert ax.get_xlabel() == "Theoretical Quantiles (Uniform)"
        assert ax.get_ylabel() == "Observed Quantiles (P-values)"
        assert ax.get_title() == "Test Title"
        
        plt.close(fig)

    def test_large_dataset_performance(self):
        """Test that the function handles large datasets without error."""
        n = 100000
        p_values = np.random.uniform(0, 1, n)
        p_values.sort()
        
        # Should not raise any errors
        fig, ax = generate_qq_plot(p_values)
        plt.close(fig)