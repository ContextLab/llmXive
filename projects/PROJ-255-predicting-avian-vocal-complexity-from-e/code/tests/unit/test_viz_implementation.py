"""
Unit tests for the visualization module (T033).
Tests file generation and basic functionality.
"""
import os
import sys
import tempfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from src.analysis.viz import (
    calculate_regression_stats,
    generate_scatter_with_regression,
    generate_heatmap_complexity_by_noise,
    generate_residual_diagnostics,
    load_final_dataset
)


class TestVizImplementation:
    """Test suite for visualization functions."""

    @pytest.fixture
    def sample_data(self):
        """Create sample data for testing."""
        np.random.seed(42)
        n = 100
        noise = np.random.normal(45, 10, n)
        complexity = 2.5 + 0.1 * noise + np.random.normal(0, 2, n)

        return pd.DataFrame({
            'noise_level_db': noise,
            'complexity_score': complexity,
            'species_id': [f'spec_{i%10}' for i in range(n)],
            'location': [f'loc_{i%5}' for i in range(n)]
        })

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test outputs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_calculate_regression_stats(self, sample_data):
        """Test regression statistics calculation."""
        x = sample_data['noise_level_db'].values
        y = sample_data['complexity_score'].values

        stats_dict = calculate_regression_stats(x, y)

        assert 'slope' in stats_dict
        assert 'intercept' in stats_dict
        assert 'r_value' in stats_dict
        assert 'p_value' in stats_dict
        assert 'std_err' in stats_dict
        assert stats_dict['n'] == len(sample_data)
        assert -1 <= stats_dict['r_value'] <= 1

    def test_generate_scatter_with_regression(self, sample_data, temp_dir):
        """Test scatter plot generation."""
        output_path = temp_dir / "test_scatter.png"

        path = generate_scatter_with_regression(
            sample_data,
            x_col='noise_level_db',
            y_col='complexity_score',
            output_path=output_path
        )

        assert path.exists()
        assert path.stat().st_size > 0
        assert str(path) == str(output_path)

    def test_generate_heatmap(self, sample_data, temp_dir):
        """Test heatmap generation."""
        output_path = temp_dir / "test_heatmap.png"

        path = generate_heatmap_complexity_by_noise(
            sample_data,
            x_col='noise_level_db',
            y_col='complexity_score',
            bin_size=5.0,
            output_path=output_path
        )

        assert path.exists()
        assert path.stat().st_size > 0

    def test_generate_residual_diagnostics(self, sample_data, temp_dir):
        """Test residual diagnostics generation."""
        output_path = temp_dir / "test_residuals.png"

        path = generate_residual_diagnostics(
            sample_data,
            x_col='noise_level_db',
            y_col='complexity_score',
            output_path=output_path
        )

        assert path.exists()
        assert path.stat().st_size > 0

    def test_regression_with_perfect_correlation(self):
        """Test regression with perfect correlation."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 6, 8, 10])

        stats_dict = calculate_regression_stats(x, y)

        assert abs(stats_dict['r_value']) == 1.0
        assert abs(stats_dict['slope'] - 2.0) < 0.001
        assert abs(stats_dict['intercept']) < 0.001

    def test_scatter_with_nan_values(self, temp_dir):
        """Test scatter plot with NaN values in data."""
        data = pd.DataFrame({
            'noise_level_db': [1, 2, np.nan, 4, 5],
            'complexity_score': [10, 20, 30, np.nan, 50]
        })

        output_path = temp_dir / "test_scatter_nan.png"

        # Should not raise an error
        path = generate_scatter_with_regression(
            data,
            x_col='noise_level_db',
            y_col='complexity_score',
            output_path=output_path
        )

        assert path.exists()
        assert path.stat().st_size > 0

    def test_insufficient_data_for_regression(self):
        """Test regression with insufficient data points."""
        x = np.array([1])
        y = np.array([2])

        with pytest.raises(ValueError, match="Need at least 2 data points"):
            calculate_regression_stats(x, y)

    def test_heatmap_with_insufficient_data(self, temp_dir):
        """Test heatmap with very few data points."""
        data = pd.DataFrame({
            'noise_level_db': [1, 2, 3],
            'complexity_score': [10, 20, 30]
        })

        output_path = temp_dir / "test_heatmap_small.png"

        # Should create a placeholder plot
        path = generate_heatmap_complexity_by_noise(
            data,
            x_col='noise_level_db',
            y_col='complexity_score',
            bin_size=5.0,
            output_path=output_path
        )

        assert path.exists()
        assert path.stat().st_size > 0

    def test_file_output_format(self, sample_data, temp_dir):
        """Test that output files are valid PNG images."""
        scatter_path = temp_dir / "scatter.png"
        heatmap_path = temp_dir / "heatmap.png"
        residuals_path = temp_dir / "residuals.png"

        generate_scatter_with_regression(
            sample_data, output_path=scatter_path
        )
        generate_heatmap_complexity_by_noise(
            sample_data, output_path=heatmap_path
        )
        generate_residual_diagnostics(
            sample_data, output_path=residuals_path
        )

        # Check file headers for PNG format
        for path in [scatter_path, heatmap_path, residuals_path]:
            with open(path, 'rb') as f:
                header = f.read(8)
                # PNG magic number: 89 50 4E 47 0D 0A 1A 0A
                assert header[:8] == b'\x89PNG\r\n\x1a\n'