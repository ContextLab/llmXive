"""Tests for scaling plot generation (T030)."""
import pytest
import tempfile
import os
from pathlib import Path
import pandas as pd
import numpy as np

from analysis.scaling_plot_generator import (
    generate_scaling_plot_with_notes,
    load_scaling_data_real,
    fit_power_law_with_ci,
    power_law
)


class TestPowerLawFit:
    def test_power_law_function(self):
        """Test the power-law function implementation."""
        x = np.array([1.0, 2.0, 3.0])
        a, b = 2.0, 0.5
        y = power_law(x, a, b)
        expected = a * np.power(x, b)
        np.testing.assert_array_almost_equal(y, expected)

    def test_fit_with_sufficient_points(self):
        """Test fitting with more than 3 points."""
        x = np.array([2.0, 4.0, 8.0, 16.0, 32.0])
        y = 3.0 * np.power(x, 0.7) + np.random.normal(0, 0.1, len(x))
        a, b, ci = fit_power_law_with_ci(x, y, "test")
        assert isinstance(a, float)
        assert isinstance(b, float)
        assert abs(b - 0.7) < 0.2  # Should be close to true value
        assert ci >= 0  # CI half-width should be non-negative


class TestScalingPlotGeneration:
    def test_generate_plot_creates_file(self):
        """Test that the plot generation creates the PDF file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            results_dir = Path(tmpdir)
            output_path = Path(tmpdir) / "test_plot.pdf"

            # Create dummy CSV files for N=3, 5, 7
            for n in [3, 5, 7]:
                df = pd.DataFrame({
                    'game_id': range(10),
                    'specialization_index': np.random.uniform(0.1, 0.9, 10),
                    'retrieval_efficiency': np.random.uniform(0.1, 0.9, 10)
                })
                df.to_csv(results_dir / f"results_scaling_N={n}.csv", index=False)

            result = generate_scaling_plot_with_notes(results_dir, output_path)

            assert output_path.exists()
            assert output_path.suffix == ".pdf"
            assert result.n_points == 3
            assert "3 data points" in result.note

    def test_load_scaling_data_real(self):
        """Test loading scaling data from CSVs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            results_dir = Path(tmpdir)

            # Create dummy CSVs
            for n in [3, 5, 7]:
                df = pd.DataFrame({
                    'game_id': range(100),
                    'specialization_index': np.random.uniform(0.1, 0.9, 100),
                    'retrieval_efficiency': np.random.uniform(0.1, 0.9, 100)
                })
                df.to_csv(results_dir / f"results_scaling_N={n}.csv", index=False)

            loaded_df = load_scaling_data_real(results_dir)

            assert len(loaded_df) == 3
            assert set(loaded_df['agent_count'].values) == {3, 5, 7}
            assert 'avg_specialization_index' in loaded_df.columns
            assert 'avg_retrieval_efficiency' in loaded_df.columns

    def test_missing_file_raises(self):
        """Test that missing CSV raises FileNotFoundError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            results_dir = Path(tmpdir)
            output_path = Path(tmpdir) / "test.pdf"

            # Only create N=3, missing N=5 and N=7
            df = pd.DataFrame({'game_id': [1], 'specialization_index': [0.5]})
            df.to_csv(results_dir / "results_scaling_N=3.csv", index=False)

            with pytest.raises(FileNotFoundError):
                generate_scaling_plot_with_notes(results_dir, output_path)
