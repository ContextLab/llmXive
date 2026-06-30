"""
Unit tests for the sensitivity analysis module.
"""

import os
import json
import tempfile
import pandas as pd
import numpy as np
import pytest

# Mock the project structure for testing
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis.sensitivity_analysis import (
    bootstrap_sample,
    compute_weighted_scores,
    run_statistical_test,
    SensitivityError
)


class TestBootstrapSample:
    def test_bootstrap_sample_size(self):
        df = pd.DataFrame({'a': range(100)})
        sampled = bootstrap_sample(df, 0.5, seed=42)
        assert len(sampled) == 50

    def test_bootstrap_replacement(self):
        df = pd.DataFrame({'a': range(10)})
        # With replacement, we expect duplicates if sample size > unique values
        # But here sample size is small, so we just check it runs
        sampled = bootstrap_sample(df, 0.8, seed=42)
        assert len(sampled) == 8
        assert sampled['a'].dtype == df['a'].dtype

    def test_bootstrap_deterministic(self):
        df = pd.DataFrame({'a': range(10)})
        s1 = bootstrap_sample(df, 0.5, seed=123)
        s2 = bootstrap_sample(df, 0.5, seed=123)
        pd.testing.assert_frame_equal(s1, s2)


class TestWeightedScores:
    def test_weighted_scores_sum(self):
        df = pd.DataFrame({
            'consistency': [1.0, 2.0],
            'stability': [1.0, 2.0],
            'markers': [1.0, 2.0]
        })
        weights = {'consistency': 0.5, 'stability': 0.5, 'markers': 0.0}
        result = compute_weighted_scores(df, weights)
        
        # Expected: 1.0*0.5 + 1.0*0.5 + 1.0*0.0 = 1.0
        # Expected: 2.0*0.5 + 2.0*0.5 + 2.0*0.0 = 2.0
        assert result['composite_score'].iloc[0] == 1.0
        assert result['composite_score'].iloc[1] == 2.0

    def test_weight_normalization(self):
        df = pd.DataFrame({
            'consistency': [1.0],
            'stability': [1.0],
            'markers': [1.0]
        })
        # Weights don't sum to 1
        weights = {'consistency': 10, 'stability': 10, 'markers': 10}
        result = compute_weighted_scores(df, weights)
        # Should be normalized to 1.0
        assert result['composite_score'].iloc[0] == 1.0


class TestStatisticalTest:
    def test_anova_detection(self):
        # Create data with clear difference between groups
        df = pd.DataFrame({
            'strategy': ['A'] * 50 + ['B'] * 50,
            'composite_score': [1.0] * 50 + [5.0] * 50
        })
        res = run_statistical_test(df)
        assert res['significant'] is True
        assert res['test_type'] in ['anova', 'kruskal_wallis']

    def test_no_difference(self):
        # Create data with no difference
        np.random.seed(42)
        df = pd.DataFrame({
            'strategy': ['A'] * 50 + ['B'] * 50,
            'composite_score': np.random.normal(0, 1, 100)
        })
        res = run_statistical_test(df)
        # Likely not significant, but randomness exists. 
        # We just check the function runs and returns structure.
        assert 'p_value' in res
        assert 'significant' in res

    def test_insufficient_groups(self):
        df = pd.DataFrame({
            'strategy': ['A'] * 50,
            'composite_score': [1.0] * 50
        })
        res = run_statistical_test(df)
        assert 'error' in res


if __name__ == '__main__':
    pytest.main([__file__, '-v'])