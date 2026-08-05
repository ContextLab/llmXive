"""
Unit and integration tests for smoothness classification and density calculation.

This module tests the core logic for determining if an integer is y-smooth
and counting smooth numbers in intervals, as required for User Story 2.
It includes both unit tests for helper functions and an integration test
for density calculation against a brute-force ground truth.
"""

import pytest
import sys
import os

# Add parent directory to path to allow imports from code/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import the functions to be tested.
# We assume is_y_smooth and count_smooth_in_interval will be implemented in code/smoothness.py.
try:
    from smoothness import is_y_smooth, count_smooth_in_interval
except ImportError:
    # If smoothness.py is not yet implemented, we define stubs for testing
    # the structure, but the real tests will fail until T020 is done.
    def is_y_smooth(n, y, primes):
        """Stub for is_y_smooth."""
        return False

    def count_smooth_in_interval(x, h, y, primes):
        """Stub for count_smooth_in_interval."""
        return 0


class TestSmoothnessClassification:
    """Tests for the is_y_smooth function."""

    def test_factor_all_smaller_y(self):
        """
        Test that a number with all prime factors <= y returns True.
        Example: 12 = 2^2 * 3. If y=3, all factors (2, 3) are <= 3.
        """
        # We need a list of primes up to y.
        # For y=3, primes are [2, 3].
        primes = [2, 3]
        n = 12
        y = 3

        # The function should return True because 2 <= 3 and 3 <= 3.
        assert is_y_smooth(n, y, primes) is True

    def test_factor_larger_y(self):
        """
        Test that a number with at least one prime factor > y returns False.
        Example: 14 = 2 * 7. If y=5, factor 7 > 5.
        """
        # Primes up to 5: [2, 3, 5]
        primes = [2, 3, 5]
        n = 14
        y = 5

        # The function should return False because 7 > 5.
        assert is_y_smooth(n, y, primes) is False

    def test_prime_itself(self):
        """
        Test that a prime number p is y-smooth if and only if p <= y.
        """
        primes = [2, 3, 5, 7, 11]

        # 7 is in primes and 7 <= 7, so it should be smooth.
        assert is_y_smooth(7, 7, primes) is True

        # 11 is in primes but 11 > 7, so it should not be smooth.
        assert is_y_smooth(11, 7, primes) is False

    def test_one_is_smooth(self):
        """
        Test that 1 is considered y-smooth for any y >= 1.
        1 has no prime factors, so the condition is vacuously true.
        """
        primes = [2, 3, 5]
        assert is_y_smooth(1, 5, primes) is True


class TestIntervalCounting:
    """Tests for the count_smooth_in_interval function."""

    def test_empty_interval_count(self):
        """
        Test that an empty interval (h=0) returns a count of 0.
        The interval [x, x+0) contains no integers.
        """
        primes = [2, 3, 5, 7, 11, 13, 17, 19, 23]
        x = 100
        h = 0
        y = 10

        count = count_smooth_in_interval(x, h, y, primes)
        assert count == 0

    def test_interval_with_no_smooth_numbers(self):
        """
        Test an interval containing only numbers with large prime factors.
        Interval [22, 24) -> {22, 23}.
        22 = 2 * 11 (11 > 5) -> not smooth.
        23 is prime > 5 -> not smooth.
        So count should be 0 for y=5.
        """
        primes = [2, 3, 5, 7, 11, 13, 17, 19, 23]
        x = 22
        h = 2
        y = 5

        count = count_smooth_in_interval(x, h, y, primes)
        assert count == 0

    def test_interval_with_smooth_numbers(self):
        """
        Test an interval containing some smooth numbers.
        Interval [8, 12) -> {8, 9, 10, 11}.
        y = 5.
        8 = 2^3 (smooth)
        9 = 3^2 (smooth)
        10 = 2 * 5 (smooth)
        11 (prime > 5, not smooth)
        Expected count: 3.
        """
        primes = [2, 3, 5, 7, 11, 13, 17, 19, 23]
        x = 8
        h = 4
        y = 5

        count = count_smooth_in_interval(x, h, y, primes)
        assert count == 3

    def test_single_number_interval(self):
        """
        Test an interval of length 1.
        Interval [10, 11) -> {10}.
        y = 5.
        10 = 2 * 5 -> smooth.
        Expected count: 1.
        """
        primes = [2, 3, 5, 7, 11]
        x = 10
        h = 1
        y = 5

        count = count_smooth_in_interval(x, h, y, primes)
        assert count == 1


class TestDensityIntegration:
    """
    Integration tests for density calculation.
    These tests verify the end-to-end logic against a known brute-force ground truth.
    """

    def test_density_small_interval(self):
        """
        Integration test for density calculation with parameters:
        x = 10^6, y = 100, h = 1000.
        Verify count matches brute-force ground truth.

        Ground Truth Calculation:
        We need to count integers n in [1000000, 1001000) such that all prime factors of n are <= 100.
        Since we cannot easily run the full sieve here for the test, we will implement a
        brute-force check within the test itself to establish the ground truth.
        Then we assert that count_smooth_in_interval returns this value.
        """
        x = 10**6
        y = 100
        h = 1000

        # Generate primes up to y=100 for the test
        # Simple sieve for small y
        primes_small = []
        is_prime = [True] * (y + 1)
        for p in range(2, y + 1):
            if is_prime[p]:
                primes_small.append(p)
                for i in range(p * p, y + 1, p):
                    is_prime[i] = False

        # Brute-force ground truth calculation
        ground_truth_count = 0
        for n in range(x, x + h):
            temp = n
            is_smooth = True
            for p in primes_small:
                if p * p > temp:
                    break
                while temp % p == 0:
                    temp //= p
            if temp > 1:
                # If remaining temp > 1, it's a prime factor
                if temp > y:
                    is_smooth = False
            if is_smooth:
                ground_truth_count += 1

        # Now call the function under test
        result_count = count_smooth_in_interval(x, h, y, primes_small)

        # Verify they match
        assert result_count == ground_truth_count, f"Expected {ground_truth_count}, got {result_count}"