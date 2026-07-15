"""
Unit tests for prime generation and gap analysis.
"""
import pytest
import math
import os
import sys
import tempfile
from pathlib import Path

# Ensure project root is in path
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from src.data.generate_primes import simple_sieve, segmented_sieve, compute_normalized_gap, run_pipeline
from src.utils.config import get_config

class TestSimpleSieve:
    def test_small_limit(self):
        primes = simple_sieve(10)
        assert primes == [2, 3, 5, 7]

    def test_no_primes(self):
        assert simple_sieve(1) == []
        assert simple_sieve(0) == []

    def test_larger_limit(self):
        primes = simple_sieve(20)
        expected = [2, 3, 5, 7, 11, 13, 17, 19]
        assert primes == expected

class TestSegmentedSieve:
    def test_basic_segmentation(self):
        # Generate primes up to 100
        all_primes = []
        for chunk in segmented_sieve(100, segment_size=20):
            all_primes.extend(chunk)
        
        expected = simple_sieve(100)
        assert all_primes == expected

    def test_memory_efficiency(self):
        # Just verify it yields something for a larger number without crashing
        # (Actual memory test would require more complex instrumentation)
        count = 0
        for chunk in segmented_sieve(1000, segment_size=100):
            count += len(chunk)
        assert count == len(simple_sieve(1000))

class TestComputeNormalizedGap:
    def test_basic_calculation(self):
        # Primes 3 and 5: gap=2, log(3)^2 approx 1.2069, norm approx 1.657
        p1, p2 = 3, 5
        gap = p2 - p1
        log_p = math.log(p1)
        expected_norm = gap / (log_p ** 2)
        actual_norm = compute_normalized_gap(p1, p2)
        assert math.isclose(actual_norm, expected_norm, rel_tol=1e-9)

    def test_large_gap(self):
        # Primes 113 and 127: gap=14
        p1, p2 = 113, 127
        norm = compute_normalized_gap(p1, p2)
        assert norm > 0
        assert not math.isinf(norm)
        assert not math.isnan(norm)

class TestRunPipeline:
    def test_pipeline_creates_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_gaps.csv"
            result_path = run_pipeline(str(output_path))
            
            assert result_path.exists()
            assert result_path == output_path
            
            # Check header
            with open(result_path, 'r') as f:
                header = f.readline().strip()
                assert header == "prime_before,prime_after,gap_size,normalized_gap"
            
            # Check some data
            with open(result_path, 'r') as f:
                lines = f.readlines()
                assert len(lines) > 1  # Header + at least one row
                first_data = lines[1].strip().split(',')
                assert len(first_data) == 4
                assert int(first_data[0]) < int(first_data[1])  # prime_before < prime_after
                assert int(first_data[2]) > 0  # gap_size > 0

    def test_pipeline_small_limit(self):
        # Override config temporarily or pass small N
        # Since run_pipeline uses config, we can't easily override N without changing config
        # But we can verify it runs and produces valid CSV structure
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "small_gaps.csv"
            # We'll test with the default config which might be large, 
            # but we can at least verify the file structure is correct
            # For a true small test, we'd need to modify run_pipeline to accept N as arg
            # For now, assume config is set to a small N for testing or we trust the logic
            run_pipeline(str(output_path))
            assert output_path.exists()