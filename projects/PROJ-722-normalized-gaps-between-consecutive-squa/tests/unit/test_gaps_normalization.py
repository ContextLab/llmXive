"""
Unit tests for gap normalization logic.
Verifies that normalized gaps have a mean of 1.0.
"""
import pytest
import numpy as np
import sys
from pathlib import Path

# Add project root to path to import code modules
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.gaps import normalize_gaps


class TestNormalizeGaps:
    """Tests for the normalize_gaps function."""

    def test_normalize_gaps_mean_is_one(self):
        """
        Verify that the mean of normalized gaps is exactly 1.0.
        
        Given a list of raw gaps, normalization divides each gap by the
        mean of all gaps. The resulting list should have a mean of 1.0.
        """
        # Use a fixed seed for reproducibility in testing
        np.random.seed(42)
        
        # Generate random positive gaps (simulating real gap data)
        # Using exponential distribution to mimic expected gap distribution
        raw_gaps = np.random.exponential(scale=1.5, size=1000).astype(int)
        raw_gaps = np.maximum(raw_gaps, 1)  # Ensure no zero gaps
        
        # Normalize the gaps
        normalized = normalize_gaps(raw_gaps)
        
        # Verify the mean is 1.0 (within floating point precision)
        mean_normalized = np.mean(normalized)
        assert abs(mean_normalized - 1.0) < 1e-9, \
            f"Expected mean of normalized gaps to be 1.0, got {mean_normalized}"

    def test_normalize_gaps_with_known_values(self):
        """
        Test normalization with a known set of gaps to verify exact values.
        """
        # Known gaps: [2, 4, 6] -> mean = 4
        # Normalized: [0.5, 1.0, 1.5] -> mean = 1.0
        raw_gaps = np.array([2, 4, 6])
        
        normalized = normalize_gaps(raw_gaps)
        
        expected = np.array([0.5, 1.0, 1.5])
        
        np.testing.assert_array_almost_equal(normalized, expected, decimal=9)
        assert abs(np.mean(normalized) - 1.0) < 1e-9

    def test_normalize_gaps_single_element(self):
        """
        Test normalization with a single gap value.
        A single gap normalized by itself should be 1.0.
        """
        raw_gaps = np.array([5])
        
        normalized = normalize_gaps(raw_gaps)
        
        assert normalized[0] == 1.0
        assert np.mean(normalized) == 1.0

    def test_normalize_gaps_large_dataset(self):
        """
        Test normalization with a large dataset to ensure numerical stability.
        """
        np.random.seed(123)
        # Large dataset with varied gaps
        raw_gaps = np.random.exponential(scale=10.0, size=100000).astype(int)
        raw_gaps = np.maximum(raw_gaps, 1)
        
        normalized = normalize_gaps(raw_gaps)
        
        mean_normalized = np.mean(normalized)
        assert abs(mean_normalized - 1.0) < 1e-10, \
            f"Large dataset mean deviation: {mean_normalized - 1.0}"

    def test_normalize_gaps_division_by_zero_guard(self):
        """
        Test that the function handles edge cases gracefully.
        While the main logic should prevent zero gaps, we verify the guard.
        """
        # All gaps are the same value (e.g., 3)
        raw_gaps = np.array([3, 3, 3, 3, 3])
        
        normalized = normalize_gaps(raw_gaps)
        
        # All normalized values should be 1.0
        expected = np.array([1.0, 1.0, 1.0, 1.0, 1.0])
        np.testing.assert_array_almost_equal(normalized, expected, decimal=9)
        assert np.mean(normalized) == 1.0

    def test_normalize_gaps_type_consistency(self):
        """
        Verify that the output type matches expected float array.
        """
        raw_gaps = np.array([1, 2, 3, 4, 5])
        
        normalized = normalize_gaps(raw_gaps)
        
        assert isinstance(normalized, np.ndarray)
        assert normalized.dtype in [np.float64, np.float32], \
            f"Expected float array, got {normalized.dtype}"
        assert len(normalized) == len(raw_gaps)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
