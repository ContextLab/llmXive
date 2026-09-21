"""
Unit tests for FDR correction module.
"""

import json
import tempfile
from pathlib import Path

import numpy as np
import pytest

from code.analysis.fdr_corrector import (
    FDRCorrectionError,
    benjamini_hochberg,
    apply_fdr_to_power_curves
)


class TestBenjaminiHocheberg:
    """Tests for the BH correction function."""

    def test_empty_input(self):
        """Test that empty input raises error."""
        with pytest.raises(FDRCorrectionError):
            benjamini_hochberg(np.array([]))

    def test_none_input(self):
        """Test that None input raises error."""
        with pytest.raises(FDRCorrectionError):
            benjamini_hochberg(None)

    def test_invalid_p_values(self):
        """Test that p-values outside [0, 1] raise error."""
        with pytest.raises(FDRCorrectionError):
            benjamini_hochberg(np.array([0.5, 1.5]))
        with pytest.raises(FDRCorrectionError):
            benjamini_hochberg(np.array([-0.1, 0.5]))

    def test_single_p_value(self):
        """Test correction with a single p-value."""
        p_vals = np.array([0.03])
        reject, adj_p, threshold = benjamini_hochberg(p_vals, alpha=0.05)
        assert len(reject) == 1
        assert len(adj_p) == 1
        assert threshold == 0.05
        # Single value: reject if p <= 0.05
        assert reject[0] == (0.03 <= 0.05)

    def test_all_significant(self):
        """Test case where all p-values are significant."""
        p_vals = np.array([0.01, 0.02, 0.03])
        reject, adj_p, _ = benjamini_hochberg(p_vals, alpha=0.05)
        assert all(reject)
        # Adjusted p-values should be <= 0.05
        assert all(adj_p <= 0.05)

    def test_none_significant(self):
        """Test case where no p-values are significant."""
        p_vals = np.array([0.2, 0.3, 0.4])
        reject, adj_p, _ = benjamini_hochberg(p_vals, alpha=0.05)
        assert not any(reject)
        # Adjusted p-values should be > 0.05
        assert all(adj_p > 0.05)

    def test_mixed_significance(self):
        """Test case with mixed significance."""
        p_vals = np.array([0.01, 0.06, 0.15, 0.20])
        reject, adj_p, _ = benjamini_hochberg(p_vals, alpha=0.05)
        # With n=4, thresholds are: 0.0125, 0.025, 0.0375, 0.05
        # Only 0.01 < 0.0125, so only first is rejected
        assert reject[0]
        assert not reject[1]
        assert not reject[2]
        assert not reject[3]

    def test_adjusted_p_monotonic(self):
        """Test that adjusted p-values are monotonically increasing with original."""
        p_vals = np.array([0.01, 0.02, 0.03, 0.04, 0.05])
        _, adj_p, _ = benjamini_hochberg(p_vals, alpha=0.05)
        # Check monotonicity (after sorting by original p-value)
        sorted_indices = np.argsort(p_vals)
        sorted_adj = adj_p[sorted_indices]
        assert all(sorted_adj[i] <= sorted_adj[i+1] for i in range(len(sorted_adj)-1))

    def test_adjusted_p_capped_at_1(self):
        """Test that adjusted p-values do not exceed 1."""
        p_vals = np.array([0.5, 0.6, 0.7, 0.8, 0.9])
        _, adj_p, _ = benjamini_hochberg(p_vals, alpha=0.05)
        assert all(adj_p <= 1.0)

    def test_method_neg(self):
        """Test negative dependence method."""
        p_vals = np.array([0.01, 0.02, 0.03])
        _, _, threshold_neg = benjamini_hochberg(p_vals, alpha=0.05, method='neg')
        _, _, threshold_indep = benjamini_hochberg(p_vals, alpha=0.05, method='indep')
        # For 'neg', threshold should be smaller due to c_n > 1
        assert threshold_neg <= threshold_indep


class TestApplyFDRToPowerCurves:
    """Tests for the apply_fdr_to_power_curves function."""

    def create_mock_power_data(self, p_values_list):
        """Helper to create mock power curve data."""
        paradigm_results = []
        for i, p_val in enumerate(p_values_list):
            paradigm_results.append({
                'paradigm_name': f'paradigm_{i}',
                'model_stats': {
                    'p_values': {'sample_size': p_val}
                },
                'empirical_rates': [0.1, 0.5, 0.9]
            })
        return {
            'sample_sizes_tested': [10, 20, 30],
            'paradigm_results': paradigm_results
        }

    def test_missing_paradigm_results(self):
        """Test error when paradigm_results is missing."""
        data = {'sample_sizes_tested': [10]}
        with pytest.raises(FDRCorrectionError):
            apply_fdr_to_power_curves(data)

    def test_empty_paradigm_results(self):
        """Test warning and return when paradigm_results is empty."""
        data = {'paradigm_results': []}
        result = apply_fdr_to_power_curves(data)
        assert 'fdr_corrected' not in result or result['fdr_corrected'] is None

    def test_missing_model_stats(self):
        """Test warning when model_stats is missing."""
        data = {
            'paradigm_results': [
                {'paradigm_name': 'test', 'other_key': 'value'}
            ]
        }
        # Should warn and skip, resulting in no p-values
        with pytest.raises(FDRCorrectionError):
            apply_fdr_to_power_curves(data)

    def test_missing_p_values(self):
        """Test warning when p_values is missing in model_stats."""
        data = {
            'paradigm_results': [
                {
                    'paradigm_name': 'test',
                    'model_stats': {'other_key': 'value'}
                }
            ]
        }
        with pytest.raises(FDRCorrectionError):
            apply_fdr_to_power_curves(data)

    def test_successful_correction(self):
        """Test successful FDR correction."""
        p_vals = [0.01, 0.03, 0.06, 0.15]
        data = self.create_mock_power_data(p_vals)
        result = apply_fdr_to_power_curves(data, alpha=0.05)

        assert 'fdr_corrected' in result
        corrected = result['fdr_corrected']
        assert corrected['alpha'] == 0.05
        assert corrected['num_tested'] == 4
        assert len(corrected['adjusted_p_values']) == 4
        assert len(corrected['rejection_mask']) == 4
        assert len(corrected['corrected_significance']) == 4

    def test_rejection_logic(self):
        """Test that rejection logic is correct."""
        # Create data where we know the outcome
        p_vals = [0.01, 0.02, 0.10, 0.20]
        data = self.create_mock_power_data(p_vals)
        result = apply_fdr_to_power_curves(data, alpha=0.05)

        corrected = result['fdr_corrected']
        # With n=4, thresholds: 0.0125, 0.025, 0.0375, 0.05
        # Only 0.01 < 0.0125, so only first should be rejected
        assert corrected['rejection_mask'][0] == True
        assert corrected['rejection_mask'][1] == False
        assert corrected['rejection_mask'][2] == False
        assert corrected['rejection_mask'][3] == False
        assert corrected['num_significant'] == 1

    def test_adjusted_p_values_calculation(self):
        """Test that adjusted p-values are calculated correctly."""
        p_vals = [0.01, 0.02, 0.03]
        data = self.create_mock_power_data(p_vals)
        result = apply_fdr_to_power_curves(data, alpha=0.05)
        
        adj_p = result['fdr_corrected']['adjusted_p_values']
        # For n=3, BH adjusted p-value for p_i is min(1, n/i * p_i) with monotonicity
        # p=0.01: 3/1 * 0.01 = 0.03
        # p=0.02: 3/2 * 0.02 = 0.03 (capped by previous min)
        # p=0.03: 3/3 * 0.03 = 0.03
        # All should be <= 0.03
        assert all(p <= 0.03 for p in adj_p)

    def test_different_alpha(self):
        """Test correction with different alpha levels."""
        p_vals = [0.04, 0.05, 0.06]
        data = self.create_mock_power_data(p_vals)
        
        result_01 = apply_fdr_to_power_curves(data, alpha=0.01)
        result_05 = apply_fdr_to_power_curves(data, alpha=0.05)
        
        # Stricter alpha should have fewer or equal rejections
        assert result_01['fdr_corrected']['num_significant'] <= result_05['fdr_corrected']['num_significant']

    def test_output_structure(self):
        """Test that output has all required fields."""
        p_vals = [0.01, 0.02]
        data = self.create_mock_power_data(p_vals)
        result = apply_fdr_to_power_curves(data)
        
        corrected = result['fdr_corrected']
        required_keys = [
            'alpha', 'method', 'fdr_threshold', 'paradigm_names',
            'original_p_values', 'adjusted_p_values', 'rejection_mask',
            'corrected_significance', 'num_significant', 'num_tested'
        ]
        for key in required_keys:
            assert key in corrected, f"Missing key: {key}"