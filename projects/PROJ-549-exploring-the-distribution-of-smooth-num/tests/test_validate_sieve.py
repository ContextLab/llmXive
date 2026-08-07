"""
Tests for validate_sieve.py
"""

import pytest
import os
import tempfile
import csv
from unittest.mock import patch, mock_open
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from code.validate_sieve import is_prime_trial_division, verify_primes_sample, verify_primes_completeness

class TestIsPrimeTrialDivision:
    """Test the trial division prime checker"""
    
    def test_small_primes(self):
        """Test known small primes"""
        for p in [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]:
            assert is_prime_trial_division(p) is True
    
    def test_small_composites(self):
        """Test known small composites"""
        for n in [1, 4, 6, 8, 9, 10, 12, 14, 15, 16, 18, 20, 21, 22, 24, 25, 26, 27, 28]:
            assert is_prime_trial_division(n) is False
    
    def test_medium_primes(self):
        """Test medium-sized primes"""
        assert is_prime_trial_division(97) is True
        assert is_prime_trial_division(101) is True
        assert is_prime_trial_division(103) is True
        assert is_prime_trial_division(107) is True
        assert is_prime_trial_division(109) is True
    
    def test_medium_composites(self):
        """Test medium-sized composites"""
        assert is_prime_trial_division(100) is False
        assert is_prime_trial_division(102) is False
        assert is_prime_trial_division(104) is False
        assert is_prime_trial_division(105) is False
        assert is_prime_trial_division(106) is False
    
    def test_large_prime(self):
        """Test a large prime"""
        assert is_prime_trial_division(104729) is True  # 10000th prime
    
    def test_large_composite(self):
        """Test a large composite"""
        assert is_prime_trial_division(104730) is False

class TestVerifyPrimesSample:
    """Test the sample verification function"""
    
    def test_valid_sample(self):
        """Test with a valid list of primes"""
        primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
        result = verify_primes_sample(primes, sample_size=5, seed=42)
        assert result is True
    
    def test_invalid_sample(self):
        """Test with a list containing a non-prime"""
        primes = [2, 3, 4, 5, 7, 11, 13, 17, 19, 23]  # 4 is not prime
        # Note: 4 might not be in the sample, so we test with a list that forces it
        primes = [4, 6, 8, 9, 10, 12, 14, 15, 16, 18]
        result = verify_primes_sample(primes, sample_size=5, seed=42)
        assert result is False
    
    def test_empty_list(self):
        """Test with empty list"""
        primes = []
        result = verify_primes_sample(primes, sample_size=5, seed=42)
        assert result is False
    
    def test_sample_larger_than_list(self):
        """Test when sample size is larger than list"""
        primes = [2, 3, 5]
        result = verify_primes_sample(primes, sample_size=10, seed=42)
        assert result is True

class TestVerifyPrimesCompleteness:
    """Test the completeness check function"""
    
    def test_valid_primes(self):
        """Test with a valid list of primes"""
        primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
        result = verify_primes_completeness(primes)
        assert result is True
    
    def test_wrong_first_primes(self):
        """Test with wrong first primes"""
        primes = [3, 5, 7, 11, 13, 17, 19, 23, 29, 31]  # Missing 2
        result = verify_primes_completeness(primes)
        assert result is False
    
    def test_empty_list(self):
        """Test with empty list"""
        primes = []
        result = verify_primes_completeness(primes)
        assert result is False
    
    def test_single_prime(self):
        """Test with single prime"""
        primes = [2]
        result = verify_primes_completeness(primes)
        # Should fail because we expect at least 10 primes for the first check
        assert result is False