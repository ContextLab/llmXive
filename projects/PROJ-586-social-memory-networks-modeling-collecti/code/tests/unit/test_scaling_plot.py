"""
Unit tests for the scaling plot generator.
"""
import pytest
from pathlib import Path
import tempfile
import os
import numpy as np
import pandas as pd

from analysis.scaling_plot_generator import generate_scaling_plot_with_notes, ScalingPlotResult
from analysis.scaling import fit_power_law


class TestScalingPlotGeneration:
    """Tests for the scaling plot generation functionality."""

    def test_generate_plot_with_real_data(self, tmp_path):
        """Test generating a plot from a CSV file with real data structure."""
        # Create a temporary CSV with mock real data
        data = {
            'agent_count': [3, 5, 7],
            'specialization_index': [0.45, 0.62, 0.71],
            'retrieval_efficiency': [0.88, 0.85, 0.82]
        }
        df = pd.DataFrame(data)
        csv_path = tmp_path / "scaling_results.csv"
        df.to_csv(csv_path, index=False)

        output_path = tmp_path / "scaling_plot.pdf"

        # Run the generator
        result = generate_scaling_plot_with_notes(csv_path, output_path)

        # Assertions
        assert isinstance(result, ScalingPlotResult)
        assert output_path.exists()
        assert output_path.stat().st_size > 0  # File is not empty
        assert "3 data points" in result.note
        assert result.exponent_specialization is not None
        assert result.exponent_retrieval is not None

    def test_fit_power_law_basic(self):
        """Test the power law fitting function with known data."""
        # Create synthetic data following y = 2 * x^0.5
        x = np.array([3.0, 5.0, 7.0])
        y = 2 * np.power(x, 0.5)

        popt, _ = fit_power_law(x, y)
        a, b = popt

        # Check if fitted parameters are close to true values
        # Allow some tolerance for numerical errors
        assert abs(b - 0.5) < 0.1
        assert abs(a - 2.0) < 0.5

    def test_empty_data_raises(self, tmp_path):
        """Test that empty data raises an error."""
        csv_path = tmp_path / "empty.csv"
        pd.DataFrame(columns=['agent_count', 'specialization_index', 'retrieval_efficiency']).to_csv(csv_path, index=False)

        output_path = tmp_path / "plot.pdf"

        with pytest.raises(ValueError):
            generate_scaling_plot_with_notes(csv_path, output_path)

    def test_missing_columns_raises(self, tmp_path):
        """Test that missing columns raise an error."""
        data = {'agent_count': [3, 5], 'other_col': [1, 2]}
        df = pd.DataFrame(data)
        csv_path = tmp_path / "bad.csv"
        df.to_csv(csv_path, index=False)

        output_path = tmp_path / "plot.pdf"

        with pytest.raises(ValueError):
            generate_scaling_plot_with_notes(csv_path, output_path)
