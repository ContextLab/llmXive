import pytest
import pandas as pd
import numpy as np
from src.reports.sensitivity import calculate_jaccard_index, get_significant_predictors, perform_threshold_sweep

class TestSensitivityEdgeCases:
    """Additional unit tests for sensitivity analysis edge cases."""

    def test_jaccard_index_with_empty_sets(self):
        """Test Jaccard index with empty sets."""
        # Both empty
        assert calculate_jaccard_index(set(), set()) == 0.0
        
        # One empty
        assert calculate_jaccard_index(set(), {1, 2, 3}) == 0.0
        assert calculate_jaccard_index({1, 2, 3}, set()) == 0.0

    def test_jaccard_index_with_identical_sets(self):
        """Test Jaccard index with identical sets."""
        assert calculate_jaccard_index({1, 2, 3}, {1, 2, 3}) == 1.0

    def test_jaccard_index_with_disjoint_sets(self):
        """Test Jaccard index with disjoint sets."""
        assert calculate_jaccard_index({1, 2}, {3, 4}) == 0.0

    def test_jaccard_index_with_subset(self):
        """Test Jaccard index with one set being a subset of the other."""
        assert calculate_jaccard_index({1}, {1, 2, 3}) == 1/3

    def test_get_significant_predictors_with_empty_dataframe(self):
        """Test getting significant predictors with an empty dataframe."""
        df = pd.DataFrame(columns=['predictor', 'p_value'])
        significant = get_significant_predictors(df, 0.05)
        assert significant == set()

    def test_get_significant_predictors_with_no_significant_predictors(self):
        """Test getting significant predictors with none below threshold."""
        data = {
            'predictor': ['A', 'B', 'C'],
            'p_value': [0.1, 0.2, 0.3]
        }
        df = pd.DataFrame(data)
        significant = get_significant_predictors(df, 0.05)
        assert significant == set()

    def test_get_significant_predictors_with_all_significant(self):
        """Test getting significant predictors with all below threshold."""
        data = {
            'predictor': ['A', 'B', 'C'],
            'p_value': [0.01, 0.02, 0.03]
        }
        df = pd.DataFrame(data)
        significant = get_significant_predictors(df, 0.05)
        assert significant == {'A', 'B', 'C'}

    def test_get_significant_predictors_with_duplicate_predictors(self):
        """Test getting significant predictors with duplicate predictor names."""
        data = {
            'predictor': ['A', 'A', 'B'],
            'p_value': [0.01, 0.02, 0.03]
        }
        df = pd.DataFrame(data)
        # The function should handle duplicates (e.g., take the first or min p-value)
        significant = get_significant_predictors(df, 0.05)
        assert 'A' in significant or 'B' in significant

    def test_get_significant_predictors_with_nan_p_values(self):
        """Test getting significant predictors with NaN p-values."""
        data = {
            'predictor': ['A', 'B', 'C'],
            'p_value': [0.01, np.nan, 0.03]
        }
        df = pd.DataFrame(data)
        significant = get_significant_predictors(df, 0.05)
        # NaN should be ignored
        assert 'A' in significant
        assert 'B' not in significant
        assert 'C' in significant

    def test_get_significant_predictors_with_negative_p_values(self):
        """Test getting significant predictors with negative p-values (invalid)."""
        data = {
            'predictor': ['A', 'B', 'C'],
            'p_value': [-0.1, 0.01, 0.03]
        }
        df = pd.DataFrame(data)
        significant = get_significant_predictors(df, 0.05)
        # Negative p-values should be handled (e.g., treated as 0 or ignored)
        # Assuming they are treated as significant (since < 0.05)
        assert 'A' in significant

    def test_perform_threshold_sweep_with_empty_range(self):
        """Test threshold sweep with an empty range."""
        # Should return an empty list or handle gracefully
        result = perform_threshold_sweep([], 0.05)
        assert result == []

    def test_perform_threshold_sweep_with_single_threshold(self):
        """Test threshold sweep with a single threshold."""
        data = {
            'predictor': ['A', 'B', 'C'],
            'p_value': [0.01, 0.06, 0.03]
        }
        df = pd.DataFrame(data)
        
        thresholds = [0.05]
        result = perform_threshold_sweep(df, thresholds)
        
        assert len(result) == 1
        assert result[0]['threshold'] == 0.05
        assert result[0]['significant_predictors'] == {'A', 'C'}

    def test_perform_threshold_sweep_with_duplicate_thresholds(self):
        """Test threshold sweep with duplicate thresholds."""
        data = {
            'predictor': ['A', 'B', 'C'],
            'p_value': [0.01, 0.06, 0.03]
        }
        df = pd.DataFrame(data)
        
        thresholds = [0.05, 0.05, 0.1]
        result = perform_threshold_sweep(df, thresholds)
        
        assert len(result) == 3
        # The first two should be identical
        assert result[0]['threshold'] == result[1]['threshold']
        assert result[0]['significant_predictors'] == result[1]['significant_predictors']

    def test_perform_threshold_sweep_with_nan_thresholds(self):
        """Test threshold sweep with NaN thresholds."""
        data = {
            'predictor': ['A', 'B', 'C'],
            'p_value': [0.01, 0.06, 0.03]
        }
        df = pd.DataFrame(data)
        
        thresholds = [0.05, np.nan, 0.1]
        result = perform_threshold_sweep(df, thresholds)
        
        # Should handle NaN thresholds gracefully
        assert len(result) == 3
        # The NaN threshold might be skipped or handled specially

    def test_perform_threshold_sweep_with_negative_thresholds(self):
        """Test threshold sweep with negative thresholds."""
        data = {
            'predictor': ['A', 'B', 'C'],
            'p_value': [0.01, 0.06, 0.03]
        }
        df = pd.DataFrame(data)
        
        thresholds = [-0.1, 0.05, 0.1]
        result = perform_threshold_sweep(df, thresholds)
        
        # Negative threshold should result in no significant predictors (or handle gracefully)
        assert len(result) == 3
        # The first result might have an empty set of significant predictors

    def test_perform_threshold_sweep_with_very_large_thresholds(self):
        """Test threshold sweep with very large thresholds."""
        data = {
            'predictor': ['A', 'B', 'C'],
            'p_value': [0.01, 0.06, 0.03]
        }
        df = pd.DataFrame(data)
        
        thresholds = [100.0, 0.05, 0.1]
        result = perform_threshold_sweep(df, thresholds)
        
        assert len(result) == 3
        # The first result should have all predictors as significant

    def test_perform_threshold_sweep_with_empty_dataframe(self):
        """Test threshold sweep with an empty dataframe."""
        df = pd.DataFrame(columns=['predictor', 'p_value'])
        thresholds = [0.05, 0.1]
        result = perform_threshold_sweep(df, thresholds)
        
        assert len(result) == 2
        assert all(r['significant_predictors'] == set() for r in result)

    def test_perform_threshold_sweep_with_monotonic_significance(self):
        """Test that as threshold increases, the set of significant predictors grows."""
        data = {
            'predictor': ['A', 'B', 'C'],
            'p_value': [0.01, 0.06, 0.03]
        }
        df = pd.DataFrame(data)
        
        thresholds = [0.02, 0.04, 0.07]
        result = perform_threshold_sweep(df, thresholds)
        
        # As threshold increases, the set of significant predictors should grow
        # T1: 0.02 -> {A}
        # T2: 0.04 -> {A, C}
        # T3: 0.07 -> {A, B, C}
        assert result[0]['significant_predictors'] == {'A'}
        assert result[1]['significant_predictors'] == {'A', 'C'}
        assert result[2]['significant_predictors'] == {'A', 'B', 'C'}

    def test_perform_threshold_sweep_with_jaccard_index(self):
        """Test that Jaccard index is calculated correctly in threshold sweep."""
        data = {
            'predictor': ['A', 'B', 'C'],
            'p_value': [0.01, 0.06, 0.03]
        }
        df = pd.DataFrame(data)
        
        thresholds = [0.02, 0.04]
        result = perform_threshold_sweep(df, thresholds)
        
        # Calculate Jaccard index between T1 and T2
        # T1: {A}, T2: {A, C}
        # Jaccard = |{A} ∩ {A, C}| / |{A} ∪ {A, C}| = 1 / 2 = 0.5
        jaccard = calculate_jaccard_index(result[0]['significant_predictors'], result[1]['significant_predictors'])
        assert abs(jaccard - 0.5) < 0.01

    def test_perform_threshold_sweep_with_all_significant_at_all_thresholds(self):
        """Test threshold sweep where all predictors are significant at all thresholds."""
        data = {
            'predictor': ['A', 'B', 'C'],
            'p_value': [0.01, 0.02, 0.03]
        }
        df = pd.DataFrame(data)
        
        thresholds = [0.05, 0.1, 0.2]
        result = perform_threshold_sweep(df, thresholds)
        
        assert all(r['significant_predictors'] == {'A', 'B', 'C'} for r in result)
        # Jaccard index between any two should be 1.0
        for i in range(1, len(result)):
            jaccard = calculate_jaccard_index(result[i-1]['significant_predictors'], result[i]['significant_predictors'])
            assert abs(jaccard - 1.0) < 0.01

    def test_perform_threshold_sweep_with_no_significant_at_any_threshold(self):
        """Test threshold sweep where no predictors are significant at any threshold."""
        data = {
            'predictor': ['A', 'B', 'C'],
            'p_value': [0.1, 0.2, 0.3]
        }
        df = pd.DataFrame(data)
        
        thresholds = [0.01, 0.05, 0.1]
        result = perform_threshold_sweep(df, thresholds)
        
        assert all(r['significant_predictors'] == set() for r in result)
        # Jaccard index between empty sets is 0.0
        for i in range(1, len(result)):
            jaccard = calculate_jaccard_index(result[i-1]['significant_predictors'], result[i]['significant_predictors'])
            assert jaccard == 0.0