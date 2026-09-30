"""
Tests for Vectorized Smooth Number Factorization (T032b)
"""
import numpy as np
import pytest
import os
import tempfile

from smoothness_vectorized import (
    load_primes_as_array,
    is_y_smooth_vectorized,
    count_smooth_in_interval_vectorized
)


def test_load_primes_as_array():
    """Test loading primes from a temporary CSV file."""
    primes_data = [2, 3, 5, 7, 11, 13, 17, 19]
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        for p in primes_data:
            f.write(f"{p}\n")
        temp_path = f.name
    
    try:
        loaded = load_primes_as_array(temp_path)
        assert isinstance(loaded, np.ndarray)
        assert len(loaded) == len(primes_data)
        assert np.array_equal(loaded, np.array(primes_data))
    finally:
        os.unlink(temp_path)


def test_is_y_smooth_vectorized():
    """Test vectorized smoothness check logic."""
    # Create a small set of primes
    primes = np.array([2, 3, 5, 7, 11, 13], dtype=np.int64)
    
    # Test numbers:
    # 6 = 2 * 3 (smooth for y=3)
    # 10 = 2 * 5 (smooth for y=5, not for y=3)
    # 14 = 2 * 7 (smooth for y=7, not for y=5)
    # 15 = 3 * 5 (smooth for y=5)
    # 22 = 2 * 11 (smooth for y=11)
    # 25 = 5 * 5 (smooth for y=5)
    # 26 = 2 * 13 (smooth for y=13)
    
    # Test case 1: y=5
    # Expected: 6(T), 10(T), 14(F), 15(T), 22(F), 25(T), 26(F)
    intervals = np.array([6, 10, 14, 15, 22, 25, 26], dtype=np.int64)
    result = is_y_smooth_vectorized(intervals, primes, y=5)
    expected = np.array([True, True, False, True, False, True, False])
    assert np.array_equal(result, expected), f"Expected {expected}, got {result}"
    
    # Test case 2: y=3
    # Expected: 6(T), 10(F), 14(F), 15(F), 22(F), 25(F), 26(F)
    result = is_y_smooth_vectorized(intervals, primes, y=3)
    expected = np.array([True, False, False, False, False, False, False])
    assert np.array_equal(result, expected), f"Expected {expected}, got {result}"


def test_count_smooth_in_interval_vectorized():
    """Test counting smooth numbers in an interval."""
    primes = np.array([2, 3, 5, 7, 11, 13], dtype=np.int64)
    
    # Interval [1, 10] -> 1, 2, 3, 4, 5, 6, 7, 8, 9, 10
    # Smooth with y=5:
    # 1 (yes), 2 (yes), 3 (yes), 4=2*2 (yes), 5 (yes), 6=2*3 (yes), 7 (no), 8=2*3 (yes), 9=3*3 (yes), 10=2*5 (yes)
    # Count: 9 (excluding 7)
    count = count_smooth_in_interval_vectorized(1, 10, primes, y=5)
    assert count == 9, f"Expected 9, got {count}"
    
    # Interval [1, 10] with y=3
    # 1, 2, 3, 4, 5(no), 6, 7(no), 8, 9, 10(no)
    # Count: 1, 2, 3, 4, 6, 8, 9 -> 7 numbers
    count = count_smooth_in_interval_vectorized(1, 10, primes, y=3)
    assert count == 7, f"Expected 7, got {count}"


def test_empty_interval():
    """Test handling of empty intervals."""
    primes = np.array([2, 3, 5], dtype=np.int64)
    count = count_smooth_in_interval_vectorized(10, 0, primes, y=5)
    assert count == 0


def test_large_interval_performance():
    """Basic performance sanity check for vectorized vs scalar (conceptual)."""
    primes = np.array([2, 3, 5, 7, 11, 13, 17, 19, 23, 29], dtype=np.int64)
    # Create a large interval to ensure vectorization is triggered
    start = 1000000
    length = 10000
    # This should complete quickly without timing out
    count = count_smooth_in_interval_vectorized(start, length, primes, y=10)
    assert count >= 0
    assert count <= length