"""
Unit tests for sensitivity analysis module.
"""
import pytest
import pandas as pd
import numpy as np
from src.reports.sensitivity import (
    calculate_jaccard_index,
    get_significant_predictors,
    perform_threshold_sweep,
    calculate_jaccard_index
)


class TestJaccardIndex:
    def test_identical_sets(self):
        set_a = {'a', 'b', 'c'}
        set_b = {'a', 'b', 'c'}
        assert calculate_jaccard_index(set_a, set_b) == 1.0

    def test_disjoint_sets(self):
        set_a = {'a', 'b'}
        set_b = {'c', 'd'}
        assert calculate_jaccard_index(set_a, set_b) == 0.0

    def test_partial_overlap(self):
        set_a = {'a', 'b', 'c'}
        set_b = {'b', 'c', 'd'}
        # Intersection: {b, c} -> 2
        # Union: {a, b, c, d} -> 4
        assert calculate_jaccard_index(set_a, set_b) == 0.5

    def test_empty_sets(self):
        assert calculate_jaccard_index(set(), set()) == 1.0

    def test_one_empty_set(self):
        set_a = {'a', 'b'}
        set_b = set()
        assert calculate_jaccard_index(set_a, set_b) == 0.0


class TestSignificantPredictors:
    def test_basic_significance(self):
        df = pd.DataFrame({
            'feature': ['f1', 'f2', 'f3', 'f4'],
            'p_values': [0.01, 0.04, 0.06, 0.10]
        })
        significant = get_significant_predictors(df, threshold=0.05)
        assert significant == {'f1', 'f2'}

    def test_no_significant(self):
        df = pd.DataFrame({
            'feature': ['f1', 'f2'],
            'p_values': [0.10, 0.20]
        })
        significant = get_significant_predictors(df, threshold=0.05)
        assert significant == set()

    def test_all_significant(self):
        df = pd.DataFrame({
            'feature': ['f1', 'f2'],
            'p_values': [0.01, 0.02]
        })
        significant = get_significant_predictors(df, threshold=0.05)
        assert significant == {'f1', 'f2'}

    def test_missing_column(self):
        df = pd.DataFrame({
            'feature': ['f1'],
            'other': [0.01]
        })
        with pytest.raises(ValueError):
            get_significant_predictors(df, p_value_col='nonexistent')


class TestThresholdSweep:
    def test_sweep_basic(self):
        df = pd.DataFrame({
            'feature': ['f1', 'f2', 'f3', 'f4', 'f5'],
            'p_values': [0.01, 0.03, 0.05, 0.07, 0.09]
        })
        
        results = perform_threshold_sweep(df, threshold_range=[0.02, 0.06, 0.10])
        
        assert len(results) == 3
        assert 'threshold' in results.columns
        assert 'n_significant' in results.columns
        assert 'jaccard_index' in results.columns

    def test_sweep_jaccard_calculation(self):
        # f1 (0.01), f2 (0.03) are significant at 0.02
        # f1, f2, f3 (0.05) are significant at 0.06
        # All 5 are significant at 0.10
        df = pd.DataFrame({
            'feature': ['f1', 'f2', 'f3', 'f4', 'f5'],
            'p_values': [0.01, 0.03, 0.05, 0.07, 0.09]
        })
        
        results = perform_threshold_sweep(df, threshold_range=[0.02, 0.06])
        
        # At 0.02: {f1, f2}
        # At 0.06: {f1, f2, f3}
        # Intersection: {f1, f2} -> 2
        # Union: {f1, f2, f3} -> 3
        # Jaccard = 2/3 ≈ 0.6667
        jaccard_at_06 = results[results['threshold'] == 0.06]['jaccard_index'].values[0]
        assert np.isclose(jaccard_at_06, 2/3, atol=0.0001)

    def test_sweep_order(self):
        df = pd.DataFrame({
            'feature': ['f1'],
            'p_values': [0.05]
        })
        
        # Test with unsorted thresholds (should be sorted internally)
        results = perform_threshold_sweep(df, threshold_range=[0.10, 0.02, 0.05])
        
        assert list(results['threshold']) == [0.02, 0.05, 0.10]
        # At 0.02: 0 significant
        # At 0.05: 1 significant (p < 0.05 is strict, so 0.05 is NOT significant)
        # Wait, our logic is p < threshold, so 0.05 < 0.05 is False
        # At 0.10: 1 significant
        assert results[results['threshold'] == 0.05]['n_significant'].values[0] == 0
        assert results[results['threshold'] == 0.10]['n_significant'].values[0] == 1