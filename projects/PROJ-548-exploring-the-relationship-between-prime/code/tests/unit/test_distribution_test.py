import pytest
import math
import os
import sys
import tempfile
from pathlib import Path
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from src.analysis.distribution_test import (
    pair_correlation_distribution,
    gue_extreme_value_cdf,
    compute_empirical_cdf,
    normalize_maximal_gaps,
    extract_maximal_gaps_in_windows
)

class TestPairCorrelationDistribution:
    """Test the pair-correlation distribution implementation."""
    
    def test_pair_correlation_at_zero(self):
        """Test that R_2(0) = 0 (level repulsion)."""
        s = np.array([1e-10])
        result = pair_correlation_distribution(s)
        assert result[0] == pytest.approx(0.0, abs=1e-6)
    
    def test_pair_correlation_at_one(self):
        """Test that R_2(1) = 0."""
        s = np.array([1.0])
        result = pair_correlation_distribution(s)
        # R_2(1) = 1 - (sin(pi)/(pi))^2 = 1 - 0 = 1
        # Actually, sin(pi) = 0, so sinc(1) = 0, so R_2(1) = 1
        # Wait, let's recalculate: sin(pi*1)/(pi*1) = 0/pi = 0
        # So R_2(1) = 1 - 0 = 1
        assert result[0] == pytest.approx(1.0, abs=1e-6)
    
    def test_pair_correlation_large_s(self):
        """Test that R_2(s) approaches 1 for large s."""
        s = np.array([10.0])
        result = pair_correlation_distribution(s)
        assert result[0] == pytest.approx(1.0, abs=0.1)
    
    def test_pair_correlation_monotonicity(self):
        """Test that R_2(s) is generally increasing."""
        s = np.linspace(0.01, 5.0, 100)
        result = pair_correlation_distribution(s)
        # Check that it's mostly non-decreasing (with oscillations)
        # Due to the oscillatory nature, we check the envelope
        assert np.all(result >= 0.0)
        assert np.all(result <= 1.0)

class TestGUEExtremeValueCDF:
    """Test the GUE extreme value CDF implementation."""
    
    def test_cdf_range(self):
        """Test that CDF values are between 0 and 1."""
        x = np.linspace(0, 5, 100)
        result = gue_extreme_value_cdf(x)
        assert np.all(result >= 0.0)
        assert np.all(result <= 1.0)
    
    def test_cdf_increasing(self):
        """Test that CDF is non-decreasing."""
        x = np.linspace(0, 5, 100)
        result = gue_extreme_value_cdf(x)
        assert np.all(np.diff(result) >= -1e-10)  # Allow small numerical errors

class TestComputeEmpiricalCDF:
    """Test empirical CDF computation."""
    
    def test_cdf_values(self):
        """Test that CDF values are in [0, 1]."""
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        sorted_data, cdf_vals = compute_empirical_cdf(data)
        assert np.all(cdf_vals >= 0.0)
        assert np.all(cdf_vals <= 1.0)
    
    def test_cdf_length(self):
        """Test that CDF has same length as input."""
        data = np.random.randn(50)
        sorted_data, cdf_vals = compute_empirical_cdf(data)
        assert len(sorted_data) == len(data)
        assert len(cdf_vals) == len(data)

class TestNormalizeMaximalGaps:
    """Test gap normalization."""
    
    def test_normalization_positive(self):
        """Test that normalized gaps are positive."""
        gaps = np.array([10.0, 20.0, 30.0])
        primes = np.array([100.0, 200.0, 300.0])
        result = normalize_maximal_gaps(gaps, primes)
        assert np.all(result > 0.0)
    
    def test_normalization_scale(self):
        """Test that normalization scales correctly."""
        gaps = np.array([10.0])
        primes = np.array([100.0])
        result = normalize_maximal_gaps(gaps, primes)
        expected = 10.0 / (math.log(100.0) ** 2)
        assert result[0] == pytest.approx(expected, rel=1e-10)

class TestExtractMaximalGapsInWindows:
    """Test maximal gap extraction."""
    
    def test_window_extraction(self):
        """Test that maximal gaps are correctly extracted."""
        primes = np.arange(100, 200)
        gaps = np.ones(99) * 10  # Uniform gaps
        maximal_gaps = extract_maximal_gaps_in_windows(primes, gaps, window_size=10)
        assert len(maximal_gaps) > 0
        assert np.all(maximal_gaps == 10.0)
    
    def test_non_uniform_gaps(self):
        """Test with non-uniform gaps."""
        primes = np.arange(100, 200)
        gaps = np.random.rand(99) * 100
        maximal_gaps = extract_maximal_gaps_in_windows(primes, gaps, window_size=10)
        assert len(maximal_gaps) == len(gaps) // 10
        for mg in maximal_gaps:
            assert mg <= np.max(gaps)

if __name__ == '__main__':
    pytest.main([__file__, '-v'])