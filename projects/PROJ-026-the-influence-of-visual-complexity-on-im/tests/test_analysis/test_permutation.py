"""
Tests for the permutation analysis module.
Includes unit tests for the main permutation logic and sensitivity analysis.
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import os

# Ensure code directory is in path for imports
code_root = Path(__file__).resolve().parents[2] / "code"
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from analysis.permutation import (
    run_permutation_test,
    calculate_effect_size,
    run_sensitivity_analysis
)


class TestPermutationLogic:
    """Unit tests for the core permutation test logic."""

    def test_permutation_significant_difference(self):
        """Test that a clearly separated dataset yields a low p-value."""
        np.random.seed(42)
        # Create two groups with a large, clear difference
        group_low = np.random.normal(loc=0.0, scale=0.1, size=100)
        group_high = np.random.normal(loc=0.5, scale=0.1, size=100)

        result = run_permutation_test(group_low, group_high, n_permutations=1000, seed=42)

        # With such a large effect size and sample size, p-value should be very small
        assert result['p_value'] < 0.01, "Expected significant p-value for clearly separated groups"
        assert 'observed_diff' in result
        assert 'permutation_distribution' in result
        assert len(result['permutation_distribution']) == 1000

    def test_permutation_no_difference(self):
        """Test that identical distributions yield a high p-value."""
        np.random.seed(42)
        # Create two groups from the same distribution
        data = np.random.normal(loc=0.0, scale=0.1, size=200)
        group_a = data[:100]
        group_b = data[100:]

        result = run_permutation_test(group_a, group_b, n_permutations=1000, seed=42)

        # With no real difference, p-value should be high (not significant)
        assert result['p_value'] > 0.05, "Expected non-significant p-value for identical groups"

    def test_permutation_small_sample(self):
        """Test permutation test behavior with small sample sizes."""
        np.random.seed(42)
        group_small_1 = np.array([1.0, 2.0, 3.0])
        group_small_2 = np.array([4.0, 5.0, 6.0])

        # With very small samples, the number of unique permutations is limited
        # (6 choose 3 = 20), so n_permutations should be capped or handled gracefully
        result = run_permutation_test(group_small_1, group_small_2, n_permutations=1000, seed=42)

        assert 'p_value' in result
        assert result['observed_diff'] == 3.0  # (4+5+6)/3 - (1+2+3)/3 = 5 - 2 = 3.0


class TestSensitivityAnalysis:
    """Unit tests for the sensitivity analysis (threshold sweep) logic."""

    def test_sensitivity_analysis_structure(self):
        """Verify that sensitivity analysis returns the expected structure."""
        np.random.seed(42)
        # Create synthetic data mimicking D-scores
        n_low = 50
        n_high = 50
        scores_low = np.random.normal(loc=0.1, scale=0.2, size=n_low)
        scores_high = np.random.normal(loc=0.3, scale=0.2, size=n_high)

        # Create a mock dataframe with complexity scores and D-scores
        df = pd.DataFrame({
            'complexity_score': np.concatenate([
                np.random.normal(loc=1.0, scale=0.1, size=n_low),
                np.random.normal(loc=2.0, scale=0.1, size=n_high)
            ]),
            'd_score': np.concatenate([scores_low, scores_high]),
            'complexity_category': ['Low'] * n_low + ['High'] * n_high
        })

        result = run_sensitivity_analysis(df, n_permutations=100, seed=42)

        assert 'sweep_results' in result
        assert isinstance(result['sweep_results'], list)
        assert len(result['sweep_results']) > 0

        # Check structure of individual sweep points
        sweep_point = result['sweep_results'][0]
        assert 'threshold_offset' in sweep_point
        assert 'p_value' in sweep_point
        assert 'n_low' in sweep_point
        assert 'n_high' in sweep_point
        assert 'status' in sweep_point

    def test_sensitivity_analysis_threshold_range(self):
        """Verify that sensitivity analysis sweeps across the correct threshold range."""
        np.random.seed(42)
        df = pd.DataFrame({
            'complexity_score': np.random.normal(loc=1.5, scale=0.5, size=100),
            'd_score': np.random.normal(loc=0.2, scale=0.1, size=100),
            'complexity_category': ['Low'] * 50 + ['High'] * 50
        })

        # Run with specific offsets
        offsets = [-0.05, 0.0, 0.05]
        result = run_sensitivity_analysis(df, n_permutations=50, seed=42, offsets=offsets)

        # Check that the results match the requested offsets
        reported_offsets = [r['threshold_offset'] for r in result['sweep_results']]
        # Sort both to compare since order might vary slightly in implementation
        assert sorted(reported_offsets) == sorted(offsets), "Sensitivity analysis did not sweep the correct offsets"

    def test_sensitivity_analysis_invalid_thresholds(self):
        """Test that invalid thresholds (where n < 15) are marked correctly."""
        np.random.seed(42)
        # Create a dataset where extreme thresholds will result in very small groups
        df = pd.DataFrame({
            'complexity_score': np.random.normal(loc=1.5, scale=0.1, size=100),
            'd_score': np.random.normal(loc=0.2, scale=0.1, size=100),
            'complexity_category': ['Low'] * 50 + ['High'] * 50
        })

        # Use large offsets that will likely result in small groups
        large_offsets = [-1.0, 1.0]  # These are likely to filter out most data

        result = run_sensitivity_analysis(df, n_permutations=10, seed=42, offsets=large_offsets)

        # At least some results should be marked as 'invalid' due to small sample size
        invalid_count = sum(1 for r in result['sweep_results'] if r['status'] == 'invalid')
        # We expect at least one to be invalid given the extreme offsets and small N
        assert invalid_count > 0, "Expected some thresholds to be marked invalid due to small sample size"

    def test_sensitivity_analysis_valid_thresholds(self):
        """Test that valid thresholds (n >= 15) are processed correctly."""
        np.random.seed(42)
        # Create a dataset with enough samples for moderate thresholds
        df = pd.DataFrame({
            'complexity_score': np.random.normal(loc=1.5, scale=0.5, size=200),
            'd_score': np.random.normal(loc=0.2, scale=0.1, size=200),
            'complexity_category': ['Low'] * 100 + ['High'] * 100
        })

        # Use moderate offsets
        moderate_offsets = [-0.1, 0.0, 0.1]

        result = run_sensitivity_analysis(df, n_permutations=20, seed=42, offsets=moderate_offsets)

        # All results should be 'valid' given the large sample size and moderate offsets
        valid_count = sum(1 for r in result['sweep_results'] if r['status'] == 'valid')
        assert valid_count == len(result['sweep_results']), "Expected all moderate thresholds to be valid"

    def test_sensitivity_analysis_reproducibility(self):
        """Verify that sensitivity analysis is reproducible with the same seed."""
        np.random.seed(42)
        df = pd.DataFrame({
            'complexity_score': np.random.normal(loc=1.5, scale=0.5, size=100),
            'd_score': np.random.normal(loc=0.2, scale=0.1, size=100),
            'complexity_category': ['Low'] * 50 + ['High'] * 50
        })

        offsets = [-0.05, 0.0, 0.05]

        result1 = run_sensitivity_analysis(df, n_permutations=100, seed=42, offsets=offsets)
        result2 = run_sensitivity_analysis(df, n_permutations=100, seed=42, offsets=offsets)

        # Results should be identical
        assert result1['sweep_results'] == result2['sweep_results'], "Sensitivity analysis should be reproducible with same seed"

class TestEffectSizeCalculation:
    """Unit tests for effect size calculation."""

    def test_cohen_d_calculation(self):
        """Test Cohen's d calculation with known values."""
        # Simple case: equal variance, known effect size
        group1 = np.array([1, 2, 3, 4, 5])
        group2 = np.array([6, 7, 8, 9, 10])

        effect_size = calculate_effect_size(group1, group2)

        # Manual calculation:
        # mean1 = 3, mean2 = 8, diff = 5
        # pooled_std = sqrt(((4*2.5 + 4*2.5) / 8)) = sqrt(2.5) ≈ 1.581
        # d = 5 / 1.581 ≈ 3.162
        expected_d = (8 - 3) / np.sqrt(2.5)

        assert np.isclose(effect_size, expected_d, rtol=1e-3), f"Expected {expected_d}, got {effect_size}"

    def test_effect_size_zero_difference(self):
        """Test effect size when groups are identical."""
        group = np.array([1, 2, 3, 4, 5])
        effect_size = calculate_effect_size(group, group)

        assert effect_size == 0.0, "Effect size should be 0 for identical groups"