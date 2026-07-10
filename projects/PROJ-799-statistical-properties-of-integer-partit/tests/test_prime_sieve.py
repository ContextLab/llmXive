"""
Tests for the prime_sieve module (T004).
"""

import pytest
import numpy as np
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from code.utils.prime_sieve import generate_primes, get_prime_sieve


class TestPrimeSieve:
    """Test suite for prime generation functions."""

    def test_generate_primes_basic(self):
        """Test basic prime generation up to a small limit."""
        primes = generate_primes(20)
        expected = [2, 3, 5, 7, 11, 13, 17, 19]
        assert primes == expected

    def test_generate_primes_limit_50000(self):
        """Test generation up to the project default limit (50,000)."""
        primes = generate_primes(50000)
        # Verify count: there are 5133 primes up to 50,000
        assert len(primes) == 5133, f"Expected 5133 primes, got {len(primes)}"
        assert primes[0] == 2
        assert primes[-1] == 49999  # Largest prime <= 50000

    def test_generate_primes_edge_cases(self):
        """Test edge cases like limit < 2."""
        assert generate_primes(0) == []
        assert generate_primes(1) == []
        assert generate_primes(2) == [2]

    def test_get_prime_sieve_returns_array(self):
        """Test that get_prime_sieve returns a numpy boolean array."""
        sieve = get_prime_sieve(20)
        assert isinstance(sieve, np.ndarray)
        assert sieve.dtype == bool
        assert len(sieve) == 21  # 0 to 20

    def test_get_prime_sieve_correctness(self):
        """Test correctness of the sieve array."""
        sieve = get_prime_sieve(20)
        # Check known primes
        for p in [2, 3, 5, 7, 11, 13, 17, 19]:
            assert sieve[p] is True, f"{p} should be prime"
        # Check known composites
        for c in [0, 1, 4, 6, 8, 9, 10, 12, 14, 15, 16, 18, 20]:
            assert sieve[c] is False, f"{c} should not be prime"

    def test_consistency_between_functions(self):
        """Test that generate_primes and get_prime_sieve are consistent."""
        limit = 1000
        primes_list = generate_primes(limit)
        sieve_array = get_prime_sieve(limit)

        # Reconstruct list from sieve
        primes_from_sieve = [i for i, is_p in enumerate(sieve_array) if is_p]
        assert primes_list == primes_from_sieve

    def test_performance_50000(self):
        """Basic performance check for 50,000 limit."""
        import time
        start = time.time()
        primes = generate_primes(50000)
        elapsed = time.time() - start
        # Should complete in well under 1 second
        assert elapsed < 1.0, f"Generation took {elapsed:.2f}s, expected < 1s"
        assert len(primes) == 5133
