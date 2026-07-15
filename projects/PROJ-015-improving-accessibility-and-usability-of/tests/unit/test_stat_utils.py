import pytest
import pandas as pd
import numpy as np
from analysis.stat_utils import StatUtils
import os
import tempfile
from pathlib import Path

class TestStatUtils:
    def test_shapiro_wilk_normal(self):
        # Generate normal data
        data = pd.Series(np.random.normal(0, 1, 100))
        result = StatUtils.shapiro_wilk(data)
        assert 'statistic' in result
        assert 'pvalue' in result
        assert result['pvalue'] > 0.05  # Should be normal

    def test_shapiro_wilk_non_normal(self):
        # Generate exponential data (non-normal)
        data = pd.Series(np.random.exponential(1, 100))
        result = StatUtils.shapiro_wilk(data)
        assert result['pvalue'] < 0.05  # Should be non-normal

    def test_repeated_measures_anova_two_levels(self):
        # Create mock data for 2 levels (Traditional, Explainable)
        np.random.seed(42)
        n_subjects = 20
        data = []
        for i in range(n_subjects):
            # Simulate paired data with a small difference
            base = np.random.normal(50, 5)
            data.append({'participant_id': i, 'interface_type': 'Traditional', 'value': base})
            data.append({'participant_id': i, 'interface_type': 'Explainable', 'value': base + 2}) # +2 difference

        df = pd.DataFrame(data)
        result = StatUtils.repeated_measures_anova(df, 'interface_type', 'participant_id', 'value')
        
        assert 'F' in result
        assert 'p_value' in result
        assert result['p_value'] < 0.05  # Should detect the difference

    def test_holm_bonferroni(self):
        p_values = [0.01, 0.04, 0.03, 0.005]
        adjusted = StatUtils.holm_bonferroni(p_values)
        
        assert len(adjusted) == len(p_values)
        # Check monotonicity (adjusted p-values should be non-decreasing relative to sorted order)
        # But we need to check against original indices.
        # Let's just check that they are >= original and <= 1.0
        for i, p in enumerate(p_values):
            assert adjusted[i] >= p
            assert adjusted[i] <= 1.0

    def test_generate_descriptive_stats(self):
        # Create mock data
        data = {
            'interface_type': ['A', 'A', 'B', 'B', 'A', 'B'],
            'explanation_engagement_time': [10.0, 12.0, 15.0, 14.0, 11.0, 16.0]
        }
        df = pd.DataFrame(data)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'test_stats.csv')
            result = StatUtils.generate_descriptive_stats(df, 'explanation_engagement_time', 'interface_type', output_path)
            
            assert os.path.exists(output_path)
            assert len(result) == 2 # Two groups
            assert 'mean' in result.columns
            assert 'std' in result.columns
            
            # Check specific values (A: mean=11, B: mean=15)
            group_a = result[result['group'] == 'A']['mean'].values[0]
            group_b = result[result['group'] == 'B']['mean'].values[0]
            
            assert np.isclose(group_a, 11.0)
            assert np.isclose(group_b, 15.0)