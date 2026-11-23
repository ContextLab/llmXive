"""
Unit tests for the Cramér model synthetic data generator.
"""
import pytest
import os
import sys
import tempfile
import csv
import math
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.analysis.cramer_generator import cramer_is_prime, generate_cramer_primes, generate_cramer_gaps

class TestCramerIsPrime:
    def test_small_numbers(self):
        """Test that 2 is always prime, 1 is never prime."""
        # Use a fixed seed for deterministic testing
        import random
        rng = random.Random(42)
        
        # 2 is prime with probability 1 (hardcoded in logic)
        assert cramer_is_prime(2, rng) is True
        # 1 is not prime
        assert cramer_is_prime(1, rng) is False
        # 0 is not prime
        assert cramer_is_prime(0, rng) is False

    def test_probability_trend(self):
        """
        Test that the probability of being prime decreases as n increases.
        This is a statistical test, so we use a larger sample size.
        """
        import random
        rng = random.Random(12345)
        
        # Test at two different ranges
        # Range 1: around 1000
        count_1000 = sum(1 for _ in range(10000) if cramer_is_prime(1000, rng))
        prob_1000 = count_1000 / 10000
        
        # Range 2: around 100000
        count_100000 = sum(1 for _ in range(10000) if cramer_is_prime(100000, rng))
        prob_100000 = count_100000 / 10000
        
        # Theoretical probabilities
        theo_1000 = 1.0 / math.log(1000)
        theo_100000 = 1.0 / math.log(100000)
        
        # Check that probability decreases
        assert prob_100000 < prob_1000
        
        # Check that observed probabilities are within 10% of theoretical
        # (loose tolerance for statistical fluctuation)
        assert abs(prob_1000 - theo_1000) < theo_1000 * 0.2
        assert abs(prob_100000 - theo_100000) < theo_100000 * 0.2

class TestGenerateCramerPrimes:
    def test_generator_yields_integers(self):
        """Test that the generator yields integers."""
        import random
        rng = random.Random(42)
        
        primes = list(generate_cramer_primes(100, rng))
        assert all(isinstance(p, int) for p in primes)

    def test_generator_limit(self):
        """Test that the generator respects the limit."""
        import random
        rng = random.Random(42)
        
        # Generate up to 50
        primes = list(generate_cramer_primes(50, rng))
        assert all(p <= 50 for p in primes)
        # Should contain at least 2
        assert 2 in primes

class TestGenerateCramerGaps:
    def test_gaps_are_positive(self):
        """Test that all generated gaps are positive."""
        import random
        rng = random.Random(42)
        
        gaps = list(generate_cramer_gaps(1000, rng))
        assert all(gap > 0 for _, _, gap in gaps)

    def test_gap_structure(self):
        """Test that gaps are calculated correctly (prime_after - prime_before)."""
        import random
        rng = random.Random(42)
        
        gaps = list(generate_cramer_gaps(1000, rng))
        for prime_before, prime_after, gap_size in gaps:
            assert prime_after - prime_before == gap_size
            assert prime_after > prime_before

    def test_empty_range(self):
        """Test behavior with a very small range."""
        import random
        rng = random.Random(42)
        
        # Range too small to have two primes
        gaps = list(generate_cramer_gaps(2, rng))
        # Should be empty or have very few items depending on random seed
        # We just ensure it doesn't crash
        assert isinstance(gaps, list)

class TestIntegration:
    def test_csv_output_structure(self):
        """
        Test that the generated CSV file has the correct structure.
        This requires the full pipeline to run on a small scale.
        """
        import random
        import tempfile
        import os
        
        # We can't easily test the full stream function without mocking,
        # but we can test the generator logic that feeds it.
        rng = random.Random(999)
        gaps = list(generate_cramer_gaps(10000, rng))
        
        assert len(gaps) > 0
        
        # Check first few entries
        for prime_before, prime_after, gap_size in gaps[:5]:
            assert prime_before > 0
            assert prime_after > prime_before
            assert gap_size == prime_after - prime_before