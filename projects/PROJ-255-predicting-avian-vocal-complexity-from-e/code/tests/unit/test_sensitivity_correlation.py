"""
Unit tests for T030b: Sensitivity Correlation Calculation.
"""
import os
import csv
import tempfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.analysis.sensitivity import pearson_correlation, calculate_correlations_for_thresholds


class TestPearsonCorrelation:
    """Tests for the pearson_correlation function."""

    def test_perfect_positive_correlation(self):
        """Test with perfectly correlated data."""
        x = [1, 2, 3, 4, 5]
        y = [2, 4, 6, 8, 10]
        r = pearson_correlation(x, y)
        assert r is not None
        assert abs(r - 1.0) < 1e-6

    def test_perfect_negative_correlation(self):
        """Test with perfectly negatively correlated data."""
        x = [1, 2, 3, 4, 5]
        y = [5, 4, 3, 2, 1]
        r = pearson_correlation(x, y)
        assert r is not None
        assert abs(r - (-1.0)) < 1e-6

    def test_no_correlation(self):
        """Test with uncorrelated data."""
        x = [1, 2, 3, 4, 5]
        y = [1, 5, 2, 4, 3]
        r = pearson_correlation(x, y)
        # This might not be exactly 0, but should be low
        assert r is not None
        assert abs(r) < 0.5

    def test_insufficient_data(self):
        """Test with insufficient data points."""
        x = [1]
        y = [2]
        r = pearson_correlation(x, y)
        assert r is None

    def test_constant_values(self):
        """Test with constant values (zero variance)."""
        x = [5, 5, 5, 5]
        y = [1, 2, 3, 4]
        r = pearson_correlation(x, y)
        assert r is None

    def test_mismatched_lengths(self):
        """Test with mismatched list lengths."""
        x = [1, 2, 3]
        y = [1, 2]
        r = pearson_correlation(x, y)
        assert r is None


class TestCalculateCorrelationsForThresholds:
    """Tests for the calculate_correlations_for_thresholds function."""

    def test_correlation_calculation(self, tmp_path):
        """Test correlation calculation with mock data."""
        # Create mock sensitivity datasets
        processed_dir = tmp_path / "processed"
        processed_dir.mkdir()

        # Create data for threshold 10
        df_10 = pd.DataFrame({
            'noise_level_db': [30, 40, 50, 60, 70],
            'spectral_entropy': [2.1, 2.3, 2.5, 2.7, 2.9]
        })
        df_10.to_csv(processed_dir / "sensitivity_10db.csv", index=False)

        # Calculate correlations
        results = calculate_correlations_for_thresholds([10])

        assert len(results) == 1
        assert results[0]['threshold'] == 10
        assert results[0]['sample_size'] == 5
        assert results[0]['correlation_r'] is not None
        assert abs(results[0]['correlation_r'] - 1.0) < 1e-6

    def test_missing_file(self, tmp_path):
        """Test handling of missing input file."""
        processed_dir = tmp_path / "processed"
        processed_dir.mkdir()

        results = calculate_correlations_for_thresholds([10])

        assert len(results) == 1
        assert results[0]['threshold'] == 10
        assert results[0]['sample_size'] == 0
        assert results[0]['correlation_r'] is None

    def test_missing_columns(self, tmp_path):
        """Test handling of missing required columns."""
        processed_dir = tmp_path / "processed"
        processed_dir.mkdir()

        # Create file with wrong columns
        df = pd.DataFrame({
            'wrong_col1': [1, 2, 3],
            'wrong_col2': [4, 5, 6]
        })
        df.to_csv(processed_dir / "sensitivity_10db.csv", index=False)

        results = calculate_correlations_for_thresholds([10])

        assert len(results) == 1
        assert results[0]['threshold'] == 10
        assert results[0]['correlation_r'] is None