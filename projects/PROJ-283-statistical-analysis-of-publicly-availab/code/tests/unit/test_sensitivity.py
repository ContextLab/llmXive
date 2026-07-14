"""
Unit tests for sensitivity analysis functionality.
"""
import pytest
import pandas as pd
import numpy as np
from src.reports.sensitivity import (
    calculate_jaccard_index,
    get_significant_predictors,
    perform_threshold_sweep
)

class TestJaccardIndex:
    """Tests for Jaccard index calculation."""
    
    def test_identical_sets(self):
        """Jaccard index should be 1.0 for identical sets."""
        set_a = {'a', 'b', 'c'}
        set_b = {'a', 'b', 'c'}
        assert calculate_jaccard_index(set_a, set_b) == 1.0
    
    def test_disjoint_sets(self):
        """Jaccard index should be 0.0 for disjoint sets."""
        set_a = {'a', 'b'}
        set_b = {'c', 'd'}
        assert calculate_jaccard_index(set_a, set_b) == 0.0
    
    def test_partial_overlap(self):
        """Jaccard index should be between 0 and 1 for partial overlap."""
        set_a = {'a', 'b', 'c'}
        set_b = {'b', 'c', 'd'}
        # Intersection: {b, c} = 2
        # Union: {a, b, c, d} = 4
        assert calculate_jaccard_index(set_a, set_b) == 0.5
    
    def test_empty_sets(self):
        """Jaccard index should be 1.0 for two empty sets."""
        assert calculate_jaccard_index(set(), set()) == 1.0
    
    def test_one_empty_set(self):
        """Jaccard index should be 0.0 if one set is empty and other is not."""
        assert calculate_jaccard_index({'a'}, set()) == 0.0
        assert calculate_jaccard_index(set(), {'a'}) == 0.0

class TestSignificantPredictors:
    """Tests for extracting significant predictors."""
    
    def test_basic_extraction(self):
        """Should correctly extract predictors below threshold."""
        df = pd.DataFrame({
            'p_value': [0.01, 0.05, 0.1, 0.001]
        }, index=['pred_a', 'pred_b', 'pred_c', 'pred_d'])
        
        significant = get_significant_predictors(df, 'p_value', 0.05)
        assert significant == {'pred_a', 'pred_d'}
    
    def test_no_significant(self):
        """Should return empty set if no predictors are significant."""
        df = pd.DataFrame({
            'p_value': [0.1, 0.2, 0.3]
        }, index=['pred_a', 'pred_b', 'pred_c'])
        
        significant = get_significant_predictors(df, 'p_value', 0.01)
        assert significant == set()
    
    def test_all_significant(self):
        """Should return all predictors if all are significant."""
        df = pd.DataFrame({
            'p_value': [0.001, 0.002, 0.003]
        }, index=['pred_a', 'pred_b', 'pred_c'])
        
        significant = get_significant_predictors(df, 'p_value', 0.05)
        assert significant == {'pred_a', 'pred_b', 'pred_c'}

class TestThresholdSweep:
    """Tests for threshold sweep analysis."""
    
    def test_basic_sweep(self):
        """Should perform sweep and return expected structure."""
        df = pd.DataFrame({
            'p_value': [0.001, 0.01, 0.05, 0.1, 0.2]
        }, index=['pred_a', 'pred_b', 'pred_c', 'pred_d', 'pred_e'])
        
        thresholds = [0.01, 0.05, 0.1]
        results = perform_threshold_sweep(df, 'p_value', thresholds)
        
        assert 'thresholds' in results
        assert 'jaccard_indices' in results
        assert 'significant_sets' in results
        assert len(results['thresholds']) == 3
        assert len(results['jaccard_indices']) == 3
        assert len(results['significant_sets']) == 3
    
    def test_jaccard_calculation(self):
        """Jaccard indices should be calculated correctly."""
        # Create data where we know the expected Jaccard indices
        df = pd.DataFrame({
            'p_value': [0.001, 0.01, 0.05]
        }, index=['pred_a', 'pred_b', 'pred_c'])
        
        thresholds = [0.01, 0.05]
        results = perform_threshold_sweep(df, 'p_value', thresholds)
        
        # At 0.01: {pred_a}
        # At 0.05: {pred_a, pred_b}
        # Jaccard = 1 / 2 = 0.5
        assert results['jaccard_indices'][0] == 1.0  # First threshold
        assert results['jaccard_indices'][1] == 0.5  # Second threshold
    
    def test_mean_jaccard_calculation(self):
        """Mean Jaccard index should be calculated correctly."""
        df = pd.DataFrame({
            'p_value': [0.001, 0.01, 0.05, 0.1]
        }, index=['pred_a', 'pred_b', 'pred_c', 'pred_d'])
        
        thresholds = [0.01, 0.05, 0.1]
        results = perform_threshold_sweep(df, 'p_value', thresholds)
        
        # At 0.01: {pred_a}
        # At 0.05: {pred_a, pred_b} -> J=0.5
        # At 0.1: {pred_a, pred_b, pred_c} -> J=2/3
        # Mean = (0.5 + 0.666...) / 2
        expected_mean = (0.5 + 2/3) / 2
        assert abs(results['mean_jaccard_index'] - expected_mean) < 0.0001