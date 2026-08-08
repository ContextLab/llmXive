import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from stats import run_multiple_linear_regression, load_graph_metrics, load_behavioral_scores, merge_metrics_with_scores

class TestMultipleLinearRegression:
    """Unit tests for multiple linear regression analysis in stats.py"""

    @pytest.fixture
    def sample_merged_df(self):
        """Create a sample merged dataframe for regression testing."""
        np.random.seed(42)
        n = 20
        data = {
            'subject_id': [f'sub-{i:02d}' for i in range(n)],
            'fluid_intelligence': np.random.rand(n) * 100,
            'age': np.random.randint(18, 65, n),
            'gender': np.random.choice([0, 1], n), # 0=Female, 1=Male
            'global_efficiency': np.random.rand(n) * 0.5,
            'clustering_coefficient': np.random.rand(n) * 0.8,
            'modularity': np.random.rand(n) * 0.6
        }
        return pd.DataFrame(data)

    def test_regression_with_controls(self, sample_merged_df):
        """Test that regression runs and returns expected structure."""
        metric_cols = ['global_efficiency', 'clustering_coefficient', 'modularity']
        results = run_multiple_linear_regression(sample_merged_df, metric_cols)
        
        assert isinstance(results, list)
        assert len(results) == 3
        
        for res in results:
            assert 'metric' in res
            assert 'coefficient' in res
            assert 'p_value' in res
            assert 't_statistic' in res
            assert 'r_squared' in res
            assert isinstance(res['coefficient'], float)
            assert isinstance(res['p_value'], float)
            assert 0 <= res['p_value'] <= 1.0

    def test_regression_insufficient_data(self):
        """Test regression handles small sample size gracefully."""
        small_df = pd.DataFrame({
            'subject_id': ['s1', 's2', 's3'],
            'fluid_intelligence': [50, 60, 70],
            'age': [20, 30, 40],
            'gender': [0, 1, 0],
            'metric1': [0.1, 0.2, 0.3]
        })
        
        results = run_multiple_linear_regression(small_df, ['metric1'])
        # With n=3, regression might fail or produce NaNs, but shouldn't crash unexpectedly
        # The function returns a list. If it fails due to rank deficiency, it might return error dict.
        assert isinstance(results, list)
        assert len(results) >= 1

    def test_regression_missing_target(self, sample_merged_df):
        """Test regression raises error if target column missing."""
        df_no_target = sample_merged_df.drop(columns=['fluid_intelligence'])
        with pytest.raises(ValueError, match="Target column 'fluid_intelligence' not found"):
            run_multiple_linear_regression(df_no_target, ['global_efficiency'])

    def test_regression_missing_controls(self, sample_merged_df):
        """Test regression handles missing control variables."""
        df_no_age = sample_merged_df.drop(columns=['age'])
        # This should ideally handle the missing column or raise a clear error.
        # Based on current implementation, it will likely raise a KeyError or ValueError during OLS fitting.
        # We expect it to not crash the whole script but return an error in the result list or raise.
        # Let's assume it raises a KeyError which is acceptable if data is missing.
        with pytest.raises((KeyError, ValueError)):
            run_multiple_linear_regression(df_no_age, ['global_efficiency'])
