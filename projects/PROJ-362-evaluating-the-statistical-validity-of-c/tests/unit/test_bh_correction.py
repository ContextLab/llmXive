import pytest
import math
from code.corrected_p_values_saver import (
    load_bh_correction_factors,
    apply_bh_correction_to_raw,
    run_corrected_p_values_generation
)

class TestBHCorrection:
    """Unit tests for Benjamini-Hochberg correction logic."""

    def test_bh_correction_monotonicity(self):
        """Test that corrected p-values are monotonically non-decreasing when sorted by raw p."""
        # Create a mock dataset with known p-values
        # Sorted by raw_p: 0.01, 0.02, 0.03, 0.04
        # m = 4
        # Expected q values before monotonicity:
        # 1: 0.01 * 4 / 1 = 0.04
        # 2: 0.02 * 4 / 2 = 0.04
        # 3: 0.03 * 4 / 3 = 0.04
        # 4: 0.04 * 4 / 4 = 0.04
        # Result should be all 0.04
        
        data = [
            {'query_id': 1, 'metric': 'NDCG@10', 'raw_p': 0.01},
            {'query_id': 2, 'metric': 'NDCG@10', 'raw_p': 0.02},
            {'query_id': 3, 'metric': 'NDCG@10', 'raw_p': 0.03},
            {'query_id': 4, 'metric': 'NDCG@10', 'raw_p': 0.04},
        ]
        
        result = apply_bh_correction_to_raw(data)
        
        # Check monotonicity: corrected_p[i] <= corrected_p[i+1]
        # Since input is sorted by raw_p, and BH ensures monotonicity of corrected values
        # when sorted by raw_p, the sequence of corrected_p should be non-decreasing.
        corrected_p_values = [r['corrected_p'] for r in result]
        
        for i in range(len(corrected_p_values) - 1):
            assert corrected_p_values[i] <= corrected_p_values[i+1], \
                f"Monotonicity violation: {corrected_p_values[i]} > {corrected_p_values[i+1]}"

    def test_bh_correction_separate_families(self):
        """Test that BH correction is applied separately to NDCG and MAP families."""
        data = [
            {'query_id': 1, 'metric': 'NDCG@10', 'raw_p': 0.01},
            {'query_id': 2, 'metric': 'NDCG@10', 'raw_p': 0.02},
            {'query_id': 3, 'metric': 'MAP', 'raw_p': 0.01},
            {'query_id': 4, 'metric': 'MAP', 'raw_p': 0.02},
        ]
        
        result = apply_bh_correction_to_raw(data)
        
        # Extract NDCG and MAP results
        ndcg_results = [r for r in result if r['metric'] == 'NDCG@10']
        map_results = [r for r in result if r['metric'] == 'MAP']
        
        # Both families have m=2
        # For NDCG:
        # rank 1: 0.01 * 2 / 1 = 0.02
        # rank 2: 0.02 * 2 / 2 = 0.02
        # Monotonicity: min(0.02, 0.02) = 0.02
        
        # For MAP: same logic
        # Both should result in corrected_p = 0.02 for both queries in each family
        
        for r in ndcg_results:
            assert math.isclose(r['corrected_p'], 0.02, abs_tol=1e-9), \
                f"Expected 0.02 for NDCG, got {r['corrected_p']}"
        
        for r in map_results:
            assert math.isclose(r['corrected_p'], 0.02, abs_tol=1e-9), \
                f"Expected 0.02 for MAP, got {r['corrected_p']}"

    def test_bh_correction_clipping(self):
        """Test that corrected p-values are clipped to [0, 1]."""
        # Create a case where uncorrected BH value > 1
        # m=2, raw_p=0.6, rank=1 -> 0.6 * 2 / 1 = 1.2 -> should clip to 1.0
        data = [
            {'query_id': 1, 'metric': 'NDCG@10', 'raw_p': 0.6},
            {'query_id': 2, 'metric': 'NDCG@10', 'raw_p': 0.8},
        ]
        
        result = apply_bh_correction_to_raw(data)
        
        for r in result:
            assert 0.0 <= r['corrected_p'] <= 1.0, \
                f"Corrected p-value {r['corrected_p']} out of bounds [0, 1]"

    def test_bh_correction_empty_family(self):
        """Test handling of a metric family with no data."""
        data = [
            {'query_id': 1, 'metric': 'NDCG@10', 'raw_p': 0.05},
            # No MAP data
        ]
        
        result = apply_bh_correction_to_raw(data)
        
        # Should return the original data with corrected_p = raw_p for the existing metric
        assert len(result) == 1
        assert result[0]['corrected_p'] == 0.05  # m=1, rank=1 -> 0.05 * 1 / 1 = 0.05

    def test_bh_correction_vs_statsmodels(self):
        """
        Compare our implementation against statsmodels.stats.multitest.multipletests
        for a small known dataset.
        """
        try:
            from statsmodels.stats.multitest import multipletests
        except ImportError:
            pytest.skip("statsmodels not installed, skipping comparison test")
        
        # Create a simple dataset
        p_values = [0.01, 0.04, 0.03, 0.001]
        # Sort them
        sorted_p = sorted(p_values)
        
        # Apply statsmodels
        _, corrected_p, _, _ = multipletests(p_values, alpha=0.05, method='fdr_bh')
        
        # Our implementation (need to wrap in the expected format)
        data = [{'query_id': i, 'metric': 'NDCG@10', 'raw_p': p} for i, p in enumerate(p_values)]
        result = apply_bh_correction_to_raw(data)
        
        # Map back to original order
        our_corrected = {r['query_id']: r['corrected_p'] for r in result}
        
        # Verify each value matches statsmodels (within tolerance)
        for i, expected in enumerate(corrected_p):
            actual = our_corrected[i]
            assert math.isclose(actual, expected, abs_tol=1e-9), \
                f"Mismatch at index {i}: expected {expected}, got {actual}"

if __name__ == '__main__':
    pytest.main([__file__, '-v'])