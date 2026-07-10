"""
Unit tests for Benjamini-Hochberg FDR correction.
Task: T019 [US2] Unit test for Benjamini-Hochberg FDR correction in `tests/unit/test_fdr.py`
"""
import pytest
import numpy as np
from scipy.stats import rankdata
import pandas as pd
import sys
from pathlib import Path

# Add project root to path to allow imports if running standalone
# In the actual project structure, this is handled by conftest.py
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from utils import get_data_processed_path


def benjamini_hochberg_fdr(p_values, alpha=0.05):
    """
    Implement Benjamini-Hochberg FDR correction.
    
    Args:
        p_values: Array-like of p-values
        alpha: Significance threshold (default 0.05)
        
    Returns:
      - adjusted_p_values: Array of q-values
      - significant: Boolean array indicating significance
    """
    p_values = np.asarray(p_values)
    n = len(p_values)
    if n == 0:
        return np.array([]), np.array([])
    
    # Get sorted indices
    sorted_indices = np.argsort(p_values)
    sorted_p_values = p_values[sorted_indices]
    
    # Calculate ranks (1-based)
    ranks = np.arange(1, n + 1)
    
    # Calculate q-values: p * n / rank
    q_values = sorted_p_values * n / ranks
    
    # Ensure monotonicity (cumulative min from the end)
    for i in range(n - 2, -1, -1):
        q_values[i] = min(q_values[i], q_values[i + 1])
    
    # Clip to [0, 1]
    q_values = np.clip(q_values, 0, 1)
    
    # Restore original order
    adjusted_p_values = np.empty(n)
    adjusted_p_values[sorted_indices] = q_values
    
    # Determine significance
    significant = adjusted_p_values < alpha
    
    return adjusted_p_values, significant


class TestBenjaminiHochbergFDR:
    """Test suite for Benjamini-Hochberg FDR correction implementation."""

    def test_fdr_basic_calculation(self):
        """Test basic FDR calculation with known values."""
        # Simple known case: p-values [0.01, 0.02, 0.03, 0.04]
        p_values = np.array([0.01, 0.02, 0.03, 0.04])
        alpha = 0.05
        
        adj_p, sig = benjamini_hochberg_fdr(p_values, alpha)
        
        # Check that we get 4 results
        assert len(adj_p) == 4
        assert len(sig) == 4
        
        # First p-value (0.01) should be significant
        assert sig[0] is True
        
        # Last p-value (0.04) should likely not be significant
        # (depends on exact calculation, but typically not for n=4)
        assert adj_p[3] >= 0.05  # Should be >= alpha

    def test_fdr_monotonicity(self):
        """Test that q-values are monotonically non-decreasing with p-values."""
        # Generate random p-values
        np.random.seed(42)
        p_values = np.random.uniform(0, 1, 100)
        
        adj_p, _ = benjamini_hochberg_fdr(p_values)
        
        # Sort p-values and corresponding q-values
        sorted_indices = np.argsort(p_values)
        sorted_p = p_values[sorted_indices]
        sorted_q = adj_p[sorted_indices]
        
        # Check monotonicity: q-values should be non-decreasing
        assert np.all(np.diff(sorted_q) >= -1e-10)  # Small epsilon for float comparison

    def test_fdr_all_significant(self):
        """Test case where all p-values are very small."""
        p_values = np.array([0.001, 0.002, 0.003])
        alpha = 0.05
        
        adj_p, sig = benjamini_hochberg_fdr(p_values, alpha)
        
        # All should be significant
        assert all(sig)

    def test_fdr_none_significant(self):
        """Test case where all p-values are large."""
        p_values = np.array([0.5, 0.6, 0.7, 0.8])
        alpha = 0.05
        
        adj_p, sig = benjamini_hochberg_fdr(p_values, alpha)
        
        # None should be significant
        assert not any(sig)

    def test_fdr_edge_case_single_value(self):
        """Test with a single p-value."""
        p_values = np.array([0.03])
        alpha = 0.05
        
        adj_p, sig = benjamini_hochberg_fdr(p_values, alpha)
        
        assert len(adj_p) == 1
        assert adj_p[0] == 0.03  # For n=1, q = p * 1 / 1 = p
        assert sig[0] is True

    def test_fdr_edge_case_empty(self):
        """Test with empty array."""
        p_values = np.array([])
        alpha = 0.05
        
        adj_p, sig = benjamini_hochberg_fdr(p_values, alpha)
        
        assert len(adj_p) == 0
        assert len(sig) == 0

    def test_fdr_with_duplicates(self):
        """Test with duplicate p-values."""
        p_values = np.array([0.05, 0.05, 0.05])
        alpha = 0.05
        
        adj_p, sig = benjamini_hochberg_fdr(p_values, alpha)
        
        # All q-values should be equal
        assert np.allclose(adj_p, adj_p[0])
        
        # With n=3, q = 0.05 * 3 / 1 = 0.15 for the first, 
        # but due to monotonicity correction, they should be 0.15
        # Actually, for duplicate p-values, the calculation uses their rank
        # Rank 1: 0.05 * 3 / 1 = 0.15
        # Rank 2: 0.05 * 3 / 2 = 0.075 -> corrected to 0.15 (max of itself and next)
        # Rank 3: 0.05 * 3 / 3 = 0.05 -> corrected to 0.15
        # So all should be 0.15
        assert np.allclose(adj_p, 0.15)

    def test_fdr_alpha_threshold(self):
        """Test different alpha thresholds."""
        p_values = np.array([0.01, 0.02, 0.03, 0.04, 0.05])
        
        # Test with alpha = 0.01
        adj_p, sig_01 = benjamini_hochberg_fdr(p_values, alpha=0.01)
        # Test with alpha = 0.10
        adj_p, sig_10 = benjamini_hochberg_fdr(p_values, alpha=0.10)
        
        # More should be significant at alpha=0.10 than at alpha=0.01
        assert sum(sig_10) >= sum(sig_01)

    def test_fdr_integration_with_mock_data(self):
        """Integration test simulating a correlation analysis scenario."""
        # Simulate p-values from a correlation test (e.g., 100 taxa)
        np.random.seed(123)
        n_taxa = 100
        p_values = np.random.uniform(0, 1, n_taxa)
        
        # Add some truly significant p-values
        p_values[:5] = np.random.uniform(0, 0.01, 5)
        
        adj_p, sig = benjamini_hochberg_fdr(p_values, alpha=0.05)
        
        # Check that we found some significant taxa
        n_significant = sum(sig)
        assert n_significant > 0
        
        # The first 5 (truly significant) should likely be detected
        # (not guaranteed due to randomness, but highly probable)
        # We check that at least some of them are significant
        significant_in_first_5 = sum(sig[:5])
        assert significant_in_first_5 >= 1  # At least one should be found

    def test_fdr_consistency_with_scipy(self):
        """
        Compare our implementation with a known correct implementation.
        Since scipy doesn't have a direct BH FDR function in older versions,
        we verify against the mathematical definition.
        """
        # Use a deterministic set of p-values
        p_values = np.array([0.001, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5])
        n = len(p_values)
        
        adj_p, sig = benjamini_hochberg_fdr(p_values)
        
        # Verify the formula: q_i = min(p_j * n / j for j >= i)
        # where p_j are sorted
        sorted_indices = np.argsort(p_values)
        sorted_p = p_values[sorted_indices]
        
        for i in range(n):
            rank = i + 1
            expected_q = sorted_p[i] * n / rank
            
            # Apply monotonicity correction
            for j in range(i + 1, n):
                expected_q = min(expected_q, sorted_p[j] * n / (j + 1))
            
            expected_q = min(expected_q, 1.0)
            
            # Check against our result
            actual_q = adj_p[sorted_indices[i]]
            assert np.isclose(actual_q, expected_q, atol=1e-10), \
                f"Mismatch at rank {rank}: expected {expected_q}, got {actual_q}"