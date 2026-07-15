import pytest
import math
import os
import sys
import tempfile
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.data.generate_primes import simple_sieve, segmented_sieve, compute_normalized_gap

class TestSimpleSieve:
    def test_small_primes(self):
        primes = simple_sieve(30)
        expected = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
        assert primes == expected

    def test_limit_one(self):
        primes = simple_sieve(1)
        assert primes == []

    def test_limit_two(self):
        primes = simple_sieve(2)
        assert primes == [2]

class TestSegmentedSieve:
    def test_basic_segment(self):
        # Base primes up to sqrt(20) = 4 -> [2, 3]
        base_primes = [2, 3]
        # Generate primes in [10, 20)
        primes = segmented_sieve(10, 20, base_primes)
        expected = [11, 13, 17, 19]
        assert primes == expected

    def test_start_at_two(self):
        base_primes = [2, 3] # sqrt(10) ~ 3
        # Should handle start < base_primes[0]^2 correctly
        primes = segmented_sieve(2, 10, base_primes)
        expected = [2, 3, 5, 7]
        assert primes == expected

    def test_empty_segment(self):
        base_primes = [2, 3, 5]
        primes = segmented_sieve(8, 9, base_primes) # No primes in [8, 9)
        assert primes == []

    def test_large_gap_handling(self):
        # Test a segment with a known gap
        base_primes = simple_sieve(100)
        # Primes around 113, 127 (gap 14)
        primes = segmented_sieve(110, 130, base_primes)
        assert 113 in primes
        assert 127 in primes
        # Verify no others in between
        assert 120 in primes or 121 in primes or 122 in primes # Just checking logic works

class TestComputeNormalizedGap:
    def test_standard_gap(self):
        # Gap between 3 and 5 is 2. log(3)^2 ~ 1.2069
        gap = compute_normalized_gap(3, 5)
        expected = 2 / (math.log(3) ** 2)
        assert math.isclose(gap, expected, rel_tol=1e-9)

    def test_large_prime_gap(self):
        # Gap between 113 and 127 is 14. log(113)^2 ~ 49.9
        gap = compute_normalized_gap(113, 127)
        expected = 14 / (math.log(113) ** 2)
        assert math.isclose(gap, expected, rel_tol=1e-9)

    def test_zero_prime(self):
        # Should handle edge case gracefully
        gap = compute_normalized_gap(0, 2)
        assert gap == 0.0

class TestRunPipeline:
    def test_pipeline_creates_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_gaps.csv")
            # Run a small limit for testing
            from src.data.generate_primes import run_pipeline
            run_pipeline(output_path, limit=100, chunk_size=50)
            
            assert os.path.exists(output_path)
            
            with open(output_path, 'r') as f:
                lines = f.readlines()
                # Header + data
                assert len(lines) > 1
                header = lines[0].strip()
                assert "prime_before" in header
                assert "gap_size" in header

    def test_pipeline_content_accuracy(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_gaps.csv")
            from src.data.generate_primes import run_pipeline
            run_pipeline(output_path, limit=20, chunk_size=10)
            
            with open(output_path, 'r') as f:
                lines = f.readlines()
                # Skip header
                data_lines = lines[1:]
                # Primes up to 20: 2, 3, 5, 7, 11, 13, 17, 19
                # Gaps: 1, 2, 2, 4, 2, 4, 2
                # Expected gaps in CSV: 1, 2, 2, 4, 2, 4, 2
                expected_gaps = [1, 2, 2, 4, 2, 4, 2]
                
                for i, line in enumerate(data_lines):
                    parts = line.strip().split(',')
                    gap_size = int(parts[2])
                    assert gap_size == expected_gaps[i], f"Expected gap {expected_gaps[i]} at index {i}, got {gap_size}"