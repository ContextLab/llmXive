"""
Unit tests for Benjamini-Hochberg correction implementation.
"""

import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from code.power_analysis import apply_bh_correction, run_bh_correction


class TestBHCorrection:
    """Tests for Benjamini-Hochberg correction functions."""
    
    def test_apply_bh_correction_empty_list(self):
        """Test that empty list returns empty list."""
        result = apply_bh_correction([], 'ndcg')
        assert result == []
        
    def test_apply_bh_correction_single_value(self):
        """Test BH correction with a single p-value."""
        p_values = [('q1', 'ndcg@10', 0.03)]
        result = apply_bh_correction(p_values, 'ndcg')
        
        assert len(result) == 1
        q_id, metric, raw_p, corr_p, is_sig = result[0]
        assert q_id == 'q1'
        assert metric == 'ndcg@10'
        assert raw_p == 0.03
        # For m=1, corrected = raw * 1 / 1 = raw
        assert corr_p == pytest.approx(0.03)
        assert is_sig == True  # 0.03 < 0.05
        
    def test_apply_bh_correction_multiple_values(self):
        """Test BH correction with multiple p-values."""
        p_values = [
            ('q1', 'ndcg@10', 0.01),
            ('q2', 'ndcg@10', 0.04),
            ('q3', 'ndcg@10', 0.06),
            ('q4', 'ndcg@10', 0.10)
        ]
        result = apply_bh_correction(p_values, 'ndcg')
        
        assert len(result) == 4
        
        # Check that corrected p-values are >= raw p-values
        for q_id, metric, raw_p, corr_p, is_sig in result:
            assert corr_p >= raw_p
            
    def test_apply_bh_correction_monotonicity(self):
        """Test that corrected p-values are monotonically non-decreasing with rank."""
        p_values = [
            ('q1', 'ndcg@10', 0.10),
            ('q2', 'ndcg@10', 0.05),
            ('q3', 'ndcg@10', 0.01)
        ]
        result = apply_bh_correction(p_values, 'ndcg')
        
        # Sort by raw p-value to check monotonicity
        sorted_result = sorted(result, key=lambda x: x[2])
        
        corr_p_values = [r[3] for r in sorted_result]
        # Check monotonicity: each corrected p should be >= previous
        for i in range(1, len(corr_p_values)):
            assert corr_p_values[i] >= corr_p_values[i-1]
            
    def test_run_bh_correction_separate_families(self):
        """Test that BH correction is applied separately to NDCG and MAP families."""
        p_values = [
            ('q1', 'ndcg@10', 0.01),
            ('q2', 'ndcg@10', 0.04),
            ('q3', 'map@10', 0.02),
            ('q4', 'map@10', 0.08)
        ]
        result = run_bh_correction(p_values)
        
        # Should have 4 results (2 for each family)
        assert len(result) == 4
        
        # Separate by family
        ndcg_results = [r for r in result if 'ndcg' in r[1]]
        map_results = [r for r in result if 'map' in r[1]]
        
        assert len(ndcg_results) == 2
        assert len(map_results) == 2
        
    def test_bh_correction_vs_statsmodels(self):
        """
        Compare BH correction against statsmodels implementation.
        This is a sanity check - our implementation should match.
        """
        try:
            from statsmodels.stats.multitest import multipletests
        except ImportError:
            pytest.skip("statsmodels not installed")
            
        p_values = [
            ('q1', 'ndcg@10', 0.01),
            ('q2', 'ndcg@10', 0.04),
            ('q3', 'ndcg@10', 0.06),
            ('q4', 'ndcg@10', 0.10)
        ]
        
        raw_p_list = [p[2] for p in p_values]
        _, corrected_p, _, _ = multipletests(raw_p_list, alpha=0.05, method='fdr_bh')
        
        our_result = apply_bh_correction(p_values, 'ndcg')
        
        # Compare corrected p-values (sorted by raw p)
        our_sorted = sorted(our_result, key=lambda x: x[2])
        our_corr_p = [r[3] for r in our_sorted]
        
        # Allow small floating point differences
        for ours, stats in zip(our_corr_p, corrected_p):
            assert abs(ours - stats) < 1e-10, f"Mismatch: ours={ours}, stats={stats}"