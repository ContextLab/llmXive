import pytest
import numpy as np
from code.stats import exact_test_fallback, StatisticalResult

class TestExactTestFallback:
    """Unit tests for exact_test_fallback function (T018c)."""

    def test_exact_test_uniform_distribution(self):
        """Test exact test with a perfectly uniform distribution."""
        prime = 3
        N = 300
        residue_counts = [N // prime] * prime  # [100, 100, 100]
        
        p_value = exact_test_fallback(residue_counts, prime)
        
        # For a uniform distribution, p-value should be high (not significant)
        assert 0.0 <= p_value <= 1.0
        assert p_value > 0.05  # Should not reject null hypothesis

    def test_exact_test_biased_distribution(self):
        """Test exact test with a highly biased distribution."""
        prime = 3
        N = 300
        # Highly skewed: [200, 50, 50]
        residue_counts = [200, 50, 50]
        
        p_value = exact_test_fallback(residue_counts, prime)
        
        # For a biased distribution, p-value should be low
        assert 0.0 <= p_value <= 1.0
        assert p_value < 0.05  # Should reject null hypothesis

    def test_exact_test_small_sample_size(self):
        """Test exact test with small sample size where expected < 5."""
        prime = 5
        N = 10
        # Small counts: [2, 2, 2, 2, 2]
        residue_counts = [2, 2, 2, 2, 2]
        
        p_value = exact_test_fallback(residue_counts, prime)
        
        # Should not raise error
        assert 0.0 <= p_value <= 1.0

    def test_exact_test_mismatched_length(self):
        """Test that mismatched length raises ValueError."""
        residue_counts = [10, 10]
        prime = 3
        
        with pytest.raises(ValueError):
            exact_test_fallback(residue_counts, prime)

    def test_exact_test_zero_total_count(self):
        """Test exact test with zero total count."""
        prime = 3
        residue_counts = [0, 0, 0]
        
        p_value = exact_test_fallback(residue_counts, prime)
        
        # Should return 1.0 (no evidence against null)
        assert p_value == 1.0

    def test_exact_test_monte_carlo_fallback(self):
        """Test that Monte Carlo fallback works when exact method is unavailable."""
        # This test is more of a sanity check since we can't easily disable scipy's exact method
        prime = 7
        N = 70
        residue_counts = [10] * prime
        
        p_value = exact_test_fallback(residue_counts, prime)
        
        assert 0.0 <= p_value <= 1.0