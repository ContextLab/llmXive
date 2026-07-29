"""
Unit tests for code/viz/plots.py

These tests verify that plot generation functions work correctly.
"""
import pytest
import pandas as pd
import numpy as np
import os
import tempfile
from pathlib import Path

# Assuming plots.py exists and exports these functions
try:
    from viz.plots import generate_power_curve, save_plot
except ImportError:
    generate_power_curve = None
    save_plot = None


class TestPlotGeneration:
    """Tests for plot generation functions."""

    def test_generate_power_curve_basic(self):
        """Test generating a power curve plot."""
        if generate_power_curve is None:
            pytest.skip("generate_power_curve not implemented")

        # Create sample data
        data = {
            'snr': [0.5, 1.0, 2.0, 5.0],
            'power': [0.1, 0.3, 0.7, 0.9],
            'method': ['LASSO'] * 4
        }
        df = pd.DataFrame(data)

        # Generate plot
        fig = generate_power_curve(df, 'snr', 'power', 'method')

        assert fig is not None, "Should return a matplotlib figure"

    def test_save_plot(self):
        """Test saving a plot to disk."""
        if save_plot is None:
            pytest.skip("save_plot not implemented")

        # Create a temporary directory for testing
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_plot.png")

            # Create a dummy figure
            import matplotlib.pyplot as plt
            fig, ax = plt.subplots()
            ax.plot([1, 2, 3], [1, 4, 9])

            save_plot(fig, output_path)

            assert os.path.exists(output_path), "Plot file should be saved"
            assert os.path.getsize(output_path) > 0, "Plot file should not be empty"

    def test_plot_faceting(self):
        """Test generating faceted plots for different sparsity levels."""
        if generate_power_curve is None:
            pytest.skip("generate_power_curve not implemented")

        # Create sample data with sparsity
        data = {
            'snr': [0.5, 1.0, 2.0] * 2,
            'power': [0.1, 0.3, 0.7, 0.2, 0.4, 0.8],
            'method': ['LASSO'] * 6,
            'sparsity': [0.2] * 3 + [0.5] * 3
        }
        df = pd.DataFrame(data)

        # Generate faceted plot
        fig = generate_power_curve(df, 'snr', 'power', 'method', facet_by='sparsity')

        assert fig is not None, "Should return a matplotlib figure"