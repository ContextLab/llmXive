"""
Tests for validate_sieve.py
"""
import json
import os
import random
import tempfile
from unittest.mock import patch, MagicMock

import pytest

# Import the functions to test
from validate_sieve import (
    load_primes_from_csv,
    is_prime_trial_division,
    verify_primes_sample,
    verify_primes_completeness,
    compute_file_checksum,
    EXPECTED_PRIME_COUNT,
    SAMPLE_SIZE
)

class TestLoadPrimesFromCsv:
    def test_load_primes_from_csv_valid_file(self, tmp_path):
        """Test loading primes from a valid CSV file."""
        primes_file = tmp_path / "primes.csv"
        primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
        
        with open(primes_file, 'w') as f:
            for p in primes:
                f.write(f"{p}\n")
        
        result = load_primes_from_csv(str(primes_file))
        assert result == primes
        assert len(result) == len(primes)
    
    def test_load_primes_from_csv_nonexistent_file(self):
        """Test loading from a nonexistent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_primes_from_csv("/nonexistent/path/primes.csv")
    
    def test_load_primes_from_csv_with_empty_lines(self, tmp_path):
        """Test loading primes from a CSV file with empty lines."""
        primes_file = tmp_path / "primes.csv"
        primes = [2, 3, 5, 7]
        
        with open(primes_file, 'w') as f:
            f.write("2\n")
            f.write("\n")  # Empty line
            f.write("3\n")
            f.write("5\n")
            f.write("\n")  # Empty line
            f.write("7\n")
        
        result = load_primes_from_csv(str(primes_file))
        assert result == primes

class TestIsPrimeTrialDivision:
    def test_is_prime_small_primes(self):
        """Test trial division for small primes."""
        primes_list = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
        
        # Test known primes
        assert is_prime_trial_division(2, primes_list)
        assert is_prime_trial_division(3, primes_list)
        assert is_prime_trial_division(5, primes_list)
        assert is_prime_trial_division(7, primes_list)
        assert is_prime_trial_division(29, primes_list)
        
        # Test known composites
        assert not is_prime_trial_division(4, primes_list)
        assert not is_prime_trial_division(6, primes_list)
        assert not is_prime_trial_division(9, primes_list)
        assert not is_prime_trial_division(15, primes_list)
        assert not is_prime_trial_division(25, primes_list)
    
    def test_is_prime_edge_cases(self):
        """Test edge cases."""
        primes_list = [2, 3, 5, 7]
        
        assert not is_prime_trial_division(0, primes_list)
        assert not is_prime_trial_division(1, primes_list)
        assert is_prime_trial_division(2, primes_list)
    
    def test_is_prime_large_prime(self):
        """Test a larger prime that requires trial division up to sqrt."""
        primes_list = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47]
        
        # 53 is prime, sqrt(53) ≈ 7.28, so we need primes up to 7
        assert is_prime_trial_division(53, primes_list)
        
        # 49 = 7*7 is composite
        assert not is_prime_trial_division(49, primes_list)

class TestVerifyPrimesSample:
    def test_verify_primes_sample_all_pass(self, tmp_path):
        """Test sample verification when all primes are valid."""
        primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47]
        sample_size = 5
        
        # Set seed for reproducibility
        random.seed(42)
        
        all_passed, indices, results = verify_primes_sample(primes, sample_size)
        
        assert all_passed
        assert len(indices) == sample_size
        assert all(results)
        assert all(idx < len(primes) for idx in indices)
    
    def test_verify_primes_sample_small_list(self):
        """Test sample verification with list smaller than sample size."""
        primes = [2, 3, 5, 7]
        sample_size = 10  # Larger than list size
        
        all_passed, indices, results = verify_primes_sample(primes, sample_size)
        
        assert all_passed
        assert len(indices) == len(primes)
        assert all(results)

class TestVerifyPrimesCompleteness:
    def test_verify_primes_completeness_valid(self):
        """Test completeness check with valid prime list."""
        primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
        
        passed, error = verify_primes_completeness(primes)
        
        # This should pass if count matches expected
        # Note: For this test, we're using a small list, so count will fail
        # unless we adjust EXPECTED_PRIME_COUNT for testing
        # The function should correctly identify the count mismatch
        assert not passed
        assert "Count mismatch" in error
    
    def test_verify_primes_completeness_duplicates(self):
        """Test completeness check detects duplicates."""
        primes = [2, 3, 5, 5, 7, 11]
        
        passed, error = verify_primes_completeness(primes)
        
        assert not passed
        assert "Duplicate" in error
    
    def test_verify_primes_completeness_unsorted(self):
        """Test completeness check detects unsorted list."""
        primes = [2, 3, 5, 11, 7, 13]  # 11 comes before 7
        
        passed, error = verify_primes_completeness(primes)
        
        assert not passed
        assert "sorted" in error
    
    def test_verify_primes_completeness_first_not_two(self):
        """Test completeness check detects first prime not 2."""
        primes = [3, 5, 7, 11]
        
        passed, error = verify_primes_completeness(primes)
        
        assert not passed
        assert "First prime" in error

class TestComputeFileChecksum:
    def test_compute_file_checksum(self, tmp_path):
        """Test checksum computation."""
        test_file = tmp_path / "test.txt"
        content = "Hello, World!"
        
        with open(test_file, 'w') as f:
            f.write(content)
        
        checksum = compute_file_checksum(str(test_file))
        
        assert len(checksum) == 64  # SHA256 hex length
        assert isinstance(checksum, str)
    
    def test_compute_file_checksum_consistency(self, tmp_path):
        """Test that checksum is consistent for same file."""
        test_file = tmp_path / "test.txt"
        content = "Test content for checksum"
        
        with open(test_file, 'w') as f:
            f.write(content)
        
        checksum1 = compute_file_checksum(str(test_file))
        checksum2 = compute_file_checksum(str(test_file))
        
        assert checksum1 == checksum2

class TestIntegration:
    def test_full_validation_workflow(self, tmp_path):
        """Test the full validation workflow with a mock prime list."""
        # Create a small prime list file
        primes_file = tmp_path / "primes_small.csv"
        primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
        
        with open(primes_file, 'w') as f:
            for p in primes:
                f.write(f"{p}\n")
        
        # Load and verify
        loaded_primes = load_primes_from_csv(str(primes_file))
        assert loaded_primes == primes
        
        # Check completeness (will fail on count, but should pass other checks)
        passed, error = verify_primes_completeness(loaded_primes)
        assert not passed  # Count will be wrong
        assert "Count mismatch" in error
        
        # Sample verification (should pass)
        random.seed(42)
        sample_passed, _, _ = verify_primes_sample(loaded_primes, 5)
        assert sample_passed
