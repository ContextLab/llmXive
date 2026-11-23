"""
Unit tests for the convergence check module.
"""

import pytest
import pandas as pd
import numpy as np
import sys
import os
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from analysis.convergence_check import (
    calculate_coverage_se,
    check_convergence
)


class TestCoverageSE:
    """Tests for standard error calculation."""

    def test_se_calculation_perfect_coverage(self):
        """Test SE when coverage is 100%."""
        covered = pd.Series([1, 1, 1, 1, 1])
        se = calculate_coverage_se(covered)
        assert se == 0.0

    def test_se_calculation_zero_coverage(self):
        """Test SE when coverage is 0%."""
        covered = pd.Series([0, 0, 0, 0, 0])
        se = calculate_coverage_se(covered)
        assert se == 0.0

    def test_se_calculation_typical(self):
        """Test SE for a typical coverage rate."""
        # p = 0.95, n = 100 -> se = sqrt(0.95 * 0.05 / 100) = sqrt(0.000475) ≈ 0.0218
        n = 100
        p = 0.95
        covered = pd.Series([1] * int(n * p) + [0] * (n - int(n * p)))
        se = calculate_coverage_se(covered)
        expected_se = np.sqrt(p * (1 - p) / n)
        assert np.isclose(se, expected_se)

    def test_se_calculation_empty(self):
        """Test SE for empty series."""
        covered = pd.Series([], dtype=bool)
        se = calculate_coverage_se(covered)
        assert se == float('inf')


class TestConvergenceCheck:
    """Tests for the main convergence check logic."""

    def test_all_converged(self):
        """Test when all groups meet the target SE."""
        # Create data with high N to ensure low SE
        n_samples = 10000
        data = {
            'dataset': ['adult'] * n_samples,
            'epsilon': [0.5] * n_samples,
            'noise_type': ['laplace'] * n_samples,
            'statistic': ['mean'] * n_samples,
            'covered': [1] * int(n_samples * 0.95) + [0] * (n_samples - int(n_samples * 0.95))
        }
        df = pd.DataFrame(data)

        is_converged, details = check_convergence(df, target_se=0.005)
        assert is_converged is True
        assert len(details) == 1

    def test_not_converged(self):
        """Test when groups do not meet the target SE."""
        # Create data with low N to ensure high SE
        n_samples = 10
        data = {
            'dataset': ['adult'] * n_samples,
            'epsilon': [0.5] * n_samples,
            'noise_type': ['laplace'] * n_samples,
            'statistic': ['mean'] * n_samples,
            'covered': [1] * 5 + [0] * 5  # p=0.5, n=10 -> se = 0.158
        }
        df = pd.DataFrame(data)

        is_converged, details = check_convergence(df, target_se=0.005)
        assert is_converged is False
        assert len(details) == 1
        assert details["('adult', 0.5, 'laplace', 'mean')"]["converged"] is False

    def test_mixed_convergence(self):
        """Test with some groups converged and others not."""
        n_high = 10000
        n_low = 10

        data_high = {
            'dataset': ['adult'] * n_high,
            'epsilon': [0.5] * n_high,
            'noise_type': ['laplace'] * n_high,
            'statistic': ['mean'] * n_high,
            'covered': [1] * int(n_high * 0.95) + [0] * (n_high - int(n_high * 0.95))
        }
        df_high = pd.DataFrame(data_high)

        data_low = {
            'dataset': ['iris'] * n_low,
            'epsilon': [1.0] * n_low,
            'noise_type': ['gaussian'] * n_low,
            'statistic': ['mean'] * n_low,
            'covered': [1] * 5 + [0] * 5
        }
        df_low = pd.DataFrame(data_low)

        df = pd.concat([df_high, df_low], ignore_index=True)

        is_converged, details = check_convergence(df, target_se=0.005)
        assert is_converged is False
        assert len(details) == 2

        # Check specific keys (order might vary, so check values)
        converged_count = sum(1 for v in details.values() if v['converged'])
        assert converged_count == 1