"""
tests/test_smoothness.py: Unit and integration tests for smoothness logic.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from smoothness import is_y_smooth, count_smooth_in_interval

class TestSmoothness:
    """Tests for smoothness classification logic."""

    def test_factor_all_smaller_y(self):
        """Test that a number with all factors < y returns True."""
        # Primes needed for factorization of 30 (2, 3, 5)
        primes = [2, 3, 5, 7, 11, 13]
        # 30 = 2 * 3 * 5, all factors <= 5
        assert is_y_smooth(30, 5, primes)

    def test_factor_larger_y(self):
        """Test that a number with a factor > y returns False."""
        # Primes needed for factorization of 22 (2, 11)
        primes = [2, 3, 5, 7, 11, 13]
        # 22 = 2 * 11, 11 > 10
        assert not is_y_smooth(22, 10, primes)

    def test_empty_interval_count(self):
        """Test that an empty interval returns 0."""
        primes = [2, 3, 5, 7, 11]
        # Interval starting at 100 with length 0
        count, total = count_smooth_in_interval(100, 0, 5, primes)
        assert count == 0
        assert total == 0

class TestIntegration:
    """Integration tests for density calculation."""

    def test_density_small_interval(self):
        """
        Integration test for density calculation.
        Verify count matches brute-force ground truth for x=10^6, y=100, h=1000.
        """
        # Generate small primes for testing
        def simple_sieve(limit):
            sieve = [True] * (limit + 1)
            sieve[0] = sieve[1] = False
            for i in range(2, int(limit**0.5) + 1):
                if sieve[i]:
                    for j in range(i*i, limit + 1, i):
                        sieve[j] = False
            return [i for i, is_prime in enumerate(sieve) if is_prime]

        primes = simple_sieve(100)  # Enough for y=100

        x, y, h = 10**6, 100, 1000
        
        # Calculate expected count via brute-force
        expected_count = 0
        for n in range(x, x + h):
            temp = n
            is_smooth = True
            for p in primes:
                if p > y:
                    break
                while temp % p == 0:
                    temp //= p
            if temp == 1:
                expected_count += 1

        count, total = count_smooth_in_interval(x, h, y, primes)

        # Verify total
        assert total == h

        # Verify count matches brute-force ground truth
        assert count == expected_count