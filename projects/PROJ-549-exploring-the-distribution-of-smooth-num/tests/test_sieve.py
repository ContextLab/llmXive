"""
Tests for the Segmented Sieve implementation (T012).

Note: T010 and T011 were already implemented and marked complete.
This file extends the test suite for T012 specific requirements 
(integration with file output, runtime constraints, etc).
"""

import os
import time
import tempfile
import pytest
from unittest.mock import patch, MagicMock

import sys
# Add code directory to path if running from tests/
if os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) not in sys.path:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sieve import simple_sieve, segmented_sieve, run_sieve, validate_primes, DEFAULT_LIMIT
from utils import generate_checksum


class TestSimpleSieve:
    def test_sieve_empty_interval(self):
        """T010: range [1,1] returns 0"""
        result = simple_sieve(1)
        assert result == []
    
    def test_sieve_single_prime(self):
        """T010: range [2,2] returns 1"""
        result = simple_sieve(2)
        assert result == [2]
    
    def test_sieve_small_limit(self):
        result = simple_sieve(10)
        expected = [2, 3, 5, 7]
        assert result == expected
    
    def test_sieve_correctness_100(self):
        """Verify count for small limit"""
        result = simple_sieve(100)
        # pi(100) = 25
        assert len(result) == 25


class TestSegmentedSieve:
    def test_segmented_small(self):
        primes = list(segmented_sieve(30))
        expected = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
        assert primes == expected
    
    def test_segmented_empty(self):
        primes = list(segmented_sieve(1))
        assert primes == []
    
    def test_segmented_no_primes(self):
        primes = list(segmented_sieve(0))
        assert primes == []


class TestRunSieve:
    def test_run_sieve_writes_file(self):
        """T012: Verify file is created and contains data"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_primes.csv")
            count, runtime, checksum = run_sieve(
                limit=100, 
                output_path=output_path, 
                verbose=False
            )
            
            assert os.path.exists(output_path)
            assert count == 25
            assert checksum is not None
            
            # Verify content
            with open(output_path, 'r') as f:
                lines = f.readlines()
                assert lines[0].strip() == "prime"
                assert len(lines) == 26  # Header + 25 primes
    
    def test_run_sieve_checksum(self):
        """T012: Verify checksum generation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_primes.csv")
            _, _, checksum1 = run_sieve(limit=100, output_path=output_path, verbose=False)
            _, _, checksum2 = run_sieve(limit=100, output_path=output_path, verbose=False)
            
            assert checksum1 == checksum2
            assert len(checksum1) == 64  # SHA256 hex length
    
    def test_run_sieve_runtime_measurement(self):
        """T012: Verify runtime is measured and reasonable"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_primes.csv")
            start = time.time()
            count, runtime, _ = run_sieve(limit=1000, output_path=output_path, verbose=False)
            elapsed = time.time() - start
            
            assert runtime > 0
            assert abs(runtime - elapsed) < 0.1  # Should be close
            assert count > 0
    
    def test_run_sieve_large_limit(self):
        """Test a larger limit to ensure segmentation works"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_primes.csv")
            # Use a limit that is fast but large enough to test segmentation
            limit = 10000
            count, runtime, checksum = run_sieve(
                limit=limit, 
                output_path=output_path, 
                verbose=False
            )
            
            # pi(10000) = 1229
            assert count == 1229
            assert os.path.exists(output_path)

class TestValidatePrimes:
    def test_validate_primes_success(self):
        """T012: Verify validation logic on a valid file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_primes.csv")
            run_sieve(limit=100, output_path=output_path, verbose=False)
            
            result = validate_primes(output_path)
            assert result is True
    
    def test_validate_primes_missing_file(self):
        """T012: Verify validation handles missing file"""
        result = validate_primes("non_existent_file.csv")
        assert result is False
    
    def test_validate_primes_invalid_content(self):
        """T012: Verify validation detects bad content"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "bad_primes.csv")
            with open(output_path, 'w') as f:
                f.write("prime\n1\n4\n-5\n")
            
            result = validate_primes(output_path)
            assert result is False
