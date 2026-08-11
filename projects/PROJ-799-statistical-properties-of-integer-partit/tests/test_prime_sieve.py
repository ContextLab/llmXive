import os
import sys
import numpy as np
import pytest

# Add the project code directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from utils.prime_sieve import generate_primes, get_prime_sieve

class TestPrimeSieve:
    """
    Contract tests for T004: Prime Sieve Implementation
    """

    def test_primes_file_exists(self):
        """Verify that primes.npy exists in the expected location."""
        expected_path = os.path.join(
            os.path.dirname(__file__), '..', 'code', 'utils', 'primes.npy'
        )
        assert os.path.exists(expected_path), f"Output file {expected_path} does not exist. Run code/utils/prime_sieve.py first."

    def test_primes_array_dtype(self):
        """Verify that the saved array has dtype int32 as required by T004."""
        expected_path = os.path.join(
            os.path.dirname(__file__), '..', 'code', 'utils', 'primes.npy'
        )
        primes_array = np.load(expected_path)
        assert primes_array.dtype == np.int32, f"Expected dtype int32, got {primes_array.dtype}"

    def test_primes_array_shape(self):
        """
        Verify the shape matches the count of primes <= 50,000.
        There are 5133 primes <= 50,000.
        """
        expected_path = os.path.join(
            os.path.dirname(__file__), '..', 'code', 'utils', 'primes.npy'
        )
        primes_array = np.load(expected_path)
        
        # Expected count of primes <= 50,000
        expected_count = 5133
        
        assert primes_array.shape == (expected_count,), (
            f"Expected shape ({expected_count},), got {primes_array.shape}. "
            f"Count of primes <= 50,000 should be {expected_count}."
        )

    def test_primes_array_is_1d(self):
        """Verify the array is 1-dimensional."""
        expected_path = os.path.join(
            os.path.dirname(__file__), '..', 'code', 'utils', 'primes.npy'
        )
        primes_array = np.load(expected_path)
        assert primes_array.ndim == 1, f"Expected 1D array, got {primes_array.ndim}D"

    def test_first_and_last_primes(self):
        """Verify the first and last primes in the array are correct."""
        expected_path = os.path.join(
            os.path.dirname(__file__), '..', 'code', 'utils', 'primes.npy'
        )
        primes_array = np.load(expected_path)
        
        # First prime is 2
        assert primes_array[0] == 2, f"First prime should be 2, got {primes_array[0]}"
        
        # Last prime <= 50,000 is 49999
        assert primes_array[-1] == 49999, f"Last prime should be 49999, got {primes_array[-1]}"

    def test_function_generate_primes_matches_file(self):
        """Verify that calling generate_primes(50000) produces the same list as the file."""
        limit = 50000
        generated_list = generate_primes(limit)
        
        expected_path = os.path.join(
            os.path.dirname(__file__), '..', 'code', 'utils', 'primes.npy'
        )
        file_array = np.load(expected_path)
        
        assert len(generated_list) == len(file_array), (
            f"Length mismatch: function returned {len(generated_list)}, "
            f"file has {len(file_array)}"
        )
        
        # Check values match
        for i, (g, f) in enumerate(zip(generated_list, file_array)):
            assert g == f, f"Mismatch at index {i}: function returned {g}, file has {f}"

    def test_sieve_logic_correctness_small(self):
        """Test the sieve logic on a small limit to ensure correctness."""
        limit = 30
        sieve = get_prime_sieve(limit)
        
        # Primes <= 30: 2, 3, 5, 7, 11, 13, 17, 19, 23, 29
        expected_primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
        actual_primes = [i for i, is_p in enumerate(sieve) if is_p]
        
        assert actual_primes == expected_primes, (
            f"Sieve logic error: expected {expected_primes}, got {actual_primes}"
        )

    def test_no_composites_marked_as_prime(self):
        """Ensure no composite numbers are marked as prime in the generated file."""
        expected_path = os.path.join(
            os.path.dirname(__file__), '..', 'code', 'utils', 'primes.npy'
        )
        primes_array = np.load(expected_path)
        
        def is_prime_simple(n):
            if n < 2: return False
            if n == 2: return True
            if n % 2 == 0: return False
            for i in range(3, int(n**0.5) + 1, 2):
                if n % i == 0: return False
            return True
        
        for p in primes_array:
            assert is_prime_simple(p), f"Composite number {p} found in primes array"