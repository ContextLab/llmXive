"""
Integration tests for the segmented sieve implementation (T012).

These tests verify the sieve's correctness, performance, and output integrity.
They are designed to run against the actual implementation and validate:
1. Correct prime count against OEIS A006880
2. Runtime within limits
3. Output file format and integrity
"""

import os
import tempfile
import time
import pytest
import numpy as np

# Add project root to path
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from code.sieve import segmented_sieve, run_sieve, EXPECTED_PRIME_COUNT, RUNTIME_LIMIT_SECONDS

@pytest.fixture
def small_limit():
    """Use a small limit for fast testing."""
    return 1000

@pytest.fixture
def output_path():
    """Generate a temporary output path."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        path = f.name
    yield path
    if os.path.exists(path):
        os.remove(path)

def test_segmented_sieve_small_limit(small_limit, output_path):
    """Test sieve with a small limit (1000)."""
    # Run sieve
    stats = run_sieve(limit=small_limit, output_path=output_path)
    
    # Verify output file exists
    assert os.path.exists(output_path)
    
    # Verify prime count
    # pi(1000) = 168
    expected_count = 168
    assert stats['prime_count'] == expected_count, \
        f"Expected {expected_count} primes up to {small_limit}, got {stats['prime_count']}"
    
    # Verify runtime is reasonable
    assert stats['runtime_seconds'] < 10, \
        f"Runtime {stats['runtime_seconds']:.2f}s exceeds 10s limit for small test"
    
    # Verify output file format
    with open(output_path, 'r') as f:
        lines = f.readlines()
    
    assert lines[0].strip() == "prime", "Header should be 'prime'"
    
    # Verify all values are integers and match the generator
    primes_from_file = [int(line.strip()) for line in lines[1:]]
    primes_from_gen = list(segmented_sieve(small_limit))
    
    assert primes_from_file == primes_from_gen, \
        "File contents do not match generator output"

def test_segmented_sieve_correctness():
    """Test that the sieve produces correct primes for a known range."""
    # Test range [1, 50]
    expected_primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47]
    actual_primes = list(segmented_sieve(50))
    
    assert actual_primes == expected_primes, \
        f"Primes up to 50 mismatch.\nExpected: {expected_primes}\nActual: {actual_primes}"

def test_segmented_sieve_empty_interval():
    """Test sieve with limit < 2."""
    primes = list(segmented_sieve(1))
    assert primes == [], f"Expected empty list for limit=1, got {primes}"
    
    primes = list(segmented_sieve(0))
    assert primes == [], f"Expected empty list for limit=0, got {primes}"

def test_segmented_sieve_single_prime():
    """Test sieve with limit=2 (should return [2])."""
    primes = list(segmented_sieve(2))
    assert primes == [2], f"Expected [2] for limit=2, got {primes}"

def test_segmented_sieve_performance_limit():
    """Test that sieve respects runtime limits (using a smaller limit for CI)."""
    # We can't run the full 10^9 in CI, so we test the logic with a smaller limit
    # and verify the runtime check mechanism works
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        temp_path = f.name
    
    try:
        # Run with a very small limit to ensure it completes quickly
        stats = run_sieve(limit=10000, output_path=temp_path)
        
        # Verify it completed within the global limit
        assert stats['runtime_seconds'] < RUNTIME_LIMIT_SECONDS
        
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

def test_output_file_checksum():
    """Test that output file has a valid checksum."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        temp_path = f.name
    
    try:
        stats = run_sieve(limit=1000, output_path=temp_path)
        
        # Verify checksum is generated and non-empty
        assert stats['checksum'] is not None
        assert len(stats['checksum']) == 64  # SHA256 hex length
        
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

def test_large_limit_count_verification():
    """
    Verify prime count against OEIS A006880 for a known large limit.
    This test is skipped in CI if the runtime would be too long.
    """
    # pi(10^9) = 50,847,534 (OEIS A006880)
    # We only run this if the environment allows long runs
    import os
    if os.environ.get('CI', 'false').lower() == 'true':
        pytest.skip("Skipping full 10^9 test in CI due to runtime constraints")
    
    # For local testing, we can run up to 10^7 which is faster
    # pi(10^7) = 664,579
    limit = 10**7
    expected_count = 664579
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        temp_path = f.name
    
    try:
        start = time.time()
        stats = run_sieve(limit=limit, output_path=temp_path)
        elapsed = time.time() - start
        
        assert stats['prime_count'] == expected_count, \
            f"pi({limit:,}) mismatch. Expected {expected_count:,}, got {stats['prime_count']:,}"
        
        # Verify it's reasonable for this scale
        assert elapsed < 60, f"Runtime {elapsed:.1f}s seems too long for 10^7"
        
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)