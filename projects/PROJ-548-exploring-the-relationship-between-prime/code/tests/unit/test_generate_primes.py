import pytest
import math
import os
import sys
import tempfile
from pathlib import Path
import csv

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data.generate_primes import simple_sieve, segmented_sieve, compute_normalized_gap, run_pipeline
from src.utils.config import ensure_directories

class TestSimpleSieve:
    def test_small_limit(self):
        primes = simple_sieve(10)
        assert primes == [2, 3, 5, 7]

    def test_limit_below_two(self):
        assert simple_sieve(1) == []
        assert simple_sieve(0) == []

    def test_known_primes(self):
        primes = simple_sieve(30)
        expected = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
        assert primes == expected

class TestSegmentedSieve:
    def test_first_segment(self):
        primes = list(segmented_sieve(30, segment_size=10))
        # Should yield primes in chunks: [2,3,5,7], [11,13,17,19], [23,29]
        # But the implementation yields a single list per segment call
        # Let's check the logic: 
        # Segment 1: 2-11 -> [2,3,5,7]
        # Segment 2: 12-22 -> [13,17,19] (11 is in first segment if range is inclusive of start?)
        # Actually, the loop is: low=2, high=12. Primes in [2,12): 2,3,5,7,11.
        # Wait, the range is `while low <= n`. 
        # Segment 1: low=2, high=12. Primes: 2,3,5,7,11.
        # Segment 2: low=12, high=22. Primes: 13,17,19.
        # Segment 3: low=22, high=32. Primes: 23,29.
        
        all_primes = []
        for seg in segmented_sieve(30, segment_size=10):
            all_primes.extend(seg)
        
        expected = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
        assert sorted(all_primes) == expected

    def test_large_limit(self):
        # Test a slightly larger limit to ensure no memory issues in unit test
        count = 0
        for seg in segmented_sieve(10000, segment_size=1000):
            count += len(seg)
        # Approximate pi(10000) = 1229
        assert count == 1229

class TestComputeNormalizedGap:
    def test_normal_case(self):
        # Gap between 2 and 3 is 1. log(2)^2 approx 0.48
        gap = compute_normalized_gap(1, 2)
        assert gap == 1 / (math.log(2) ** 2)

    def test_large_prime(self):
        # Gap between 100 and 101 (if 101 is prime) - 100 not prime, use 97, 101
        # Gap 4. log(97)^2
        gap = compute_normalized_gap(4, 97)
        expected = 4 / (math.log(97) ** 2)
        assert math.isclose(gap, expected)

    def test_edge_case_small_prime(self):
        # Gap 1 for prime 2
        gap = compute_normalized_gap(1, 2)
        assert gap > 0

class TestRunPipeline:
    def test_pipeline_creates_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Mock the paths to use temp dir
            import src.utils.config as config_module
            original_paths = config_module.get_project_paths
            
            def mock_paths():
                class MockPaths:
                    processed = Path(tmpdir)
                return MockPaths()
            
            config_module.get_project_paths = mock_paths
            ensure_directories() # Ensure dirs exist in mock path
            
            try:
                # Run with small limit for testing
                run_pipeline(n=100, segment_size=10)
                
                output_file = Path(tmpdir) / 'primes_gaps.csv'
                assert output_file.exists()
                
                with open(output_file, 'r') as f:
                    reader = csv.reader(f)
                    header = next(reader)
                    assert header == ['prime_before', 'prime_after', 'gap_size', 'normalized_gap']
                    
                    rows = list(reader)
                    # Primes up to 100: 2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97
                    # Gaps: 24 gaps
                    assert len(rows) == 24
                    
                    # Check first row
                    p_before, p_after, gap, norm = rows[0]
                    assert int(p_before) == 2
                    assert int(p_after) == 3
                    assert int(gap) == 1
                    
            finally:
                config_module.get_project_paths = original_paths
