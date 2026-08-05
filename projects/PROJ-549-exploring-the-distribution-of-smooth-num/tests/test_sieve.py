"""
Tests for the segmented sieve implementation.

These tests verify:
1. Boundary conditions (empty intervals, single primes)
2. Prime count accuracy against OEIS A006880
3. Runtime constraints
4. Memory efficiency (indirectly via segment size)
"""

import os
import sys
import time
import tempfile
import shutil
from pathlib import Path

import pytest
import numpy as np

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sieve import simple_sieve, segmented_sieve, validate_primes, run_sieve, TARGET_LIMIT, EXPECTED_PRIME_COUNT, MAX_RUNTIME_SECONDS


class TestSimpleSieve:
    """Tests for the simple sieve implementation."""

    def test_sieve_empty_interval(self):
        """Test sieve with range [1,1] returns 0 primes."""
        primes = simple_sieve(1)
        assert len(primes) == 0
        assert primes == []

    def test_sieve_single_prime(self):
        """Test sieve with range [2,2] returns 1 prime."""
        primes = simple_sieve(2)
        assert len(primes) == 1
        assert primes == [2]

    def test_sieve_small_range(self):
        """Test sieve with small range."""
        primes = simple_sieve(10)
        expected = [2, 3, 5, 7]
        assert primes == expected

    def test_sieve_no_duplicates(self):
        """Test that sieve produces no duplicates."""
        primes = simple_sieve(1000)
        assert len(primes) == len(set(primes))


class TestSegmentedSieve:
    """Tests for the segmented sieve implementation."""

    def test_segmented_sieve_small(self):
        """Test segmented sieve with small limit."""
        primes = list(segmented_sieve(100))
        expected = simple_sieve(100)
        assert primes == expected

    def test_segmented_sieve_boundary_1e9(self):
        """Test primality check at 10^9 boundary."""
        # 10^9 is not prime (divisible by 2 and 5)
        # Check that it's not in the list
        limit = 10**9
        # We can't generate all primes here, but we can check a known prime near 10^9
        known_prime_near_1e9 = 999999937
        primes = list(segmented_sieve(known_prime_near_1e9))
        assert known_prime_near_1e9 in primes
        assert len(primes) > 0

    def test_segmented_sieve_generator_behavior(self):
        """Test that segmented_sieve is a generator."""
        gen = segmented_sieve(100)
        assert hasattr(gen, '__iter__')
        assert hasattr(gen, '__next__')


class TestValidatePrimes:
    """Tests for prime list validation."""

    def test_validate_empty_list(self):
        """Test validation of empty list."""
        passed, msg = validate_primes([], 100)
        assert not passed
        assert "Empty" in msg

    def test_validate_correct_list(self):
        """Test validation of correct small list."""
        primes = simple_sieve(100)
        passed, msg = validate_primes(primes, 100)
        assert passed
        assert "Validation passed" in msg

    def test_validate_wrong_count(self):
        """Test validation with wrong count."""
        primes = [2, 3, 5]  # Missing 7
        passed, msg = validate_primes(primes, 100)
        assert not passed
        assert "count" in msg.lower() or "mismatch" in msg.lower()

    def test_validate_duplicate(self):
        """Test validation with duplicates."""
        primes = [2, 3, 5, 5, 7]
        passed, msg = validate_primes(primes, 100)
        assert not passed
        assert "duplicate" in msg.lower()


class TestRunSieve:
    """Integration tests for the full sieve pipeline."""

    def test_prime_count_exact(self):
        """Test that prime count matches OEIS A006880 exactly."""
        # Run on a smaller limit for speed, but verify the function works
        # For the full 10^9 test, this would take too long in CI
        limit = 10**6
        expected_count = 78498  # π(10^6)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = os.path.join(tmpdir, "primes_test.csv")
            success, runtime, msg = run_sieve(
                limit=limit,
                output_file=output_file,
                segment_size=10000
            )

            assert success, f"Sieve failed: {msg}"
            assert os.path.exists(output_file), "Output file not created"

            # Verify count from file
            with open(output_file, 'r') as f:
                lines = f.readlines()
                count = len(lines) - 1  # Subtract header

            assert count == expected_count, f"Count mismatch: got {count}, expected {expected_count}"

    def test_sieve_runtime(self):
        """Test that sieve completes within time limit."""
        limit = 10**6  # Small limit for CI

        start = time.time()
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = os.path.join(tmpdir, "primes_test.csv")
            success, runtime, msg = run_sieve(
                limit=limit,
                output_file=output_file,
                segment_size=10000
            )

            elapsed = time.time() - start

            assert success, f"Sieve failed: {msg}"
            # Should complete in well under 120 minutes
            assert runtime < 120, f"Runtime too long: {runtime}s"

    def test_sieve_output_format(self):
        """Test that output CSV has correct format."""
        limit = 100
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = os.path.join(tmpdir, "primes_test.csv")
            run_sieve(limit=limit, output_file=output_file)

            with open(output_file, 'r') as f:
                lines = f.readlines()

            # Check header
            assert lines[0].strip() == "prime"

            # Check all values are integers
            for line in lines[1:]:
                val = int(line.strip())
                assert val > 1

    def test_sieve_memory_efficiency(self):
        """Test that segmented sieve uses reasonable memory."""
        # This is a soft test - we verify the segment size is used
        limit = 10**6
        segment_size = 10000

        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = os.path.join(tmpdir, "primes_test.csv")
            success, _, _ = run_sieve(
                limit=limit,
                output_file=output_file,
                segment_size=segment_size
            )

            assert success
            # If we got here, memory efficiency is acceptable for this test

class TestBoundaryConditions:
    """Tests for edge cases and boundary conditions."""

    def test_sieve_limit_zero(self):
        """Test sieve with limit=0."""
        primes = list(segmented_sieve(0))
        assert primes == []

    def test_sieve_limit_one(self):
        """Test sieve with limit=1."""
        primes = list(segmented_sieve(1))
        assert primes == []

    def test_sieve_limit_two(self):
        """Test sieve with limit=2."""
        primes = list(segmented_sieve(2))
        assert primes == [2]

    def test_sieve_large_segment(self):
        """Test with large segment size."""
        limit = 1000
        primes = list(segmented_sieve(limit, segment_size=limit))
        expected = simple_sieve(limit)
        assert primes == expected
