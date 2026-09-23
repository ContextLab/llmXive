"""
Unit tests for Task T020: Effect Size Calculation
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import json
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from task_t020_effect_sizes import calculate_cohen_d, calculate_effect_sizes, run_effect_size_analysis

class TestCalculateCohenD:
    """Tests for the calculate_cohen_d function."""

    def test_cohen_d_basic(self):
        """Test basic Cohen's d calculation with known values."""
        # Create two groups with known difference
        group1 = np.array([10, 12, 14, 16, 18])
        group2 = np.array([8, 10, 12, 14, 16])

        cohens_d, ci_lower, ci_upper = calculate_cohen_d(group1, group2)

        # Cohen's d should be positive (group1 > group2)
        assert cohens_d > 0
        # CI should contain the effect size
        assert ci_lower <= cohens_d <= ci_upper
        # CI should be reasonable width
        assert (ci_upper - ci_lower) < 5.0

    def test_cohen_d_negative(self):
        """Test Cohen's d when group1 < group2."""
        group1 = np.array([5, 6, 7, 8, 9])
        group2 = np.array([10, 12, 14, 16, 18])

        cohens_d, ci_lower, ci_upper = calculate_cohen_d(group1, group2)

        # Cohen's d should be negative
        assert cohens_d < 0

    def test_cohen_d_zero_variance(self):
        """Test handling of zero variance."""
        group1 = np.array([5, 5, 5, 5, 5])
        group2 = np.array([10, 12, 14, 16, 18])

        cohens_d, ci_lower, ci_upper = calculate_cohen_d(group1, group2)

        # Should return 0 when variance is zero
        assert cohens_d == 0.0
        assert ci_lower == 0.0
        assert ci_upper == 0.0

    def test_cohen_d_symmetric(self):
        """Test that swapping groups negates Cohen's d."""
        group1 = np.array([10, 12, 14, 16, 18])
        group2 = np.array([8, 10, 12, 14, 16])

        d1, _, _ = calculate_cohen_d(group1, group2)
        d2, _, _ = calculate_cohen_d(group2, group1)

        # Should be negatives of each other
        assert np.isclose(d1, -d2)

class TestCalculateEffectSizes:
    """Tests for the calculate_effect_sizes function."""

    def test_calculate_effect_sizes_success(self):
        """Test successful effect size calculation."""
        df = pd.DataFrame({
            'stimulus_type': ['nostalgia'] * 20 + ['control'] * 20,
            'perseverative_errors': [10] * 10 + [15] * 10 + [12] * 10 + [18] * 10
        })

        result = calculate_effect_sizes(df, 'perseverative_errors')

        assert result['status'] == 'success'
        assert result['cohens_d'] is not None
        assert result['ci_lower'] is not None
        assert result['ci_upper'] is not None
        assert result['n_group1'] == 20
        assert result['n_group2'] == 20

    def test_calculate_effect_sizes_insufficient_groups(self):
        """Test handling of insufficient groups."""
        df = pd.DataFrame({
            'stimulus_type': ['nostalgia'] * 20,
            'perseverative_errors': [10] * 20
        })

        result = calculate_effect_sizes(df, 'perseverative_errors')

        assert result['status'] == 'insufficient_groups'
        assert result['cohens_d'] is None

    def test_calculate_effect_sizes_missing_column(self):
        """Test handling of missing metric column."""
        df = pd.DataFrame({
            'stimulus_type': ['nostalgia'] * 10 + ['control'] * 10,
            'other_metric': [10] * 20
        })

        with pytest.raises(ValueError):
            calculate_effect_sizes(df, 'missing_metric')

    def test_calculate_effect_sizes_with_missing_values(self):
        """Test handling of missing values in data."""
        df = pd.DataFrame({
            'stimulus_type': ['nostalgia'] * 15 + ['control'] * 15,
            'perseverative_errors': [10] * 5 + [np.nan] * 5 + [12] * 5 + [15] * 10
        })

        result = calculate_effect_sizes(df, 'perseverative_errors')

        assert result['status'] == 'success'
        # Should have fewer records due to NaN filtering
        assert result['n_group1'] < 15 or result['n_group2'] < 15

class TestRunEffectSizeAnalysis:
    """Tests for the run_effect_size_analysis function."""

    def test_run_effect_size_analysis_all_metrics(self):
        """Test analysis for all primary metrics."""
        df = pd.DataFrame({
            'stimulus_type': ['nostalgia'] * 20 + ['control'] * 20,
            'perseverative_errors': [10] * 10 + [15] * 10 + [12] * 10 + [18] * 10,
            'categories_completed': [5] * 10 + [3] * 10 + [6] * 10 + [4] * 10
        })

        results = run_effect_size_analysis(df)

        assert 'perseverative_errors' in results
        assert 'categories_completed' in results
        assert results['perseverative_errors']['status'] in ['success', 'zero_variance']
        assert results['categories_completed']['status'] in ['success', 'zero_variance']

    def test_run_effect_size_analysis_partial_metrics(self):
        """Test analysis when one metric is missing."""
        df = pd.DataFrame({
            'stimulus_type': ['nostalgia'] * 20 + ['control'] * 20,
            'perseverative_errors': [10] * 10 + [15] * 10 + [12] * 10 + [18] * 10
            # categories_completed missing
        })

        results = run_effect_size_analysis(df)

        assert 'perseverative_errors' in results
        assert 'categories_completed' in results
        # Missing metric should have error status
        assert results['categories_completed']['status'] != 'success'

if __name__ == "__main__":
    pytest.main([__file__, "-v"])