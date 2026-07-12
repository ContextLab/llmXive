"""
Unit tests for entropy calculation stability.
Ensures that sample_entropy and approximate_entropy do not produce NaN or Inf values
on valid input data, covering edge cases and typical signal shapes.
"""
import numpy as np
import pytest
import sys
import os

# Ensure the project root is in the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from utils.entropy_utils import sample_entropy, approximate_entropy


class TestEntropyStability:
    """Tests to verify entropy functions return finite numbers."""

    def test_sample_entropy_no_nan_inf_normal_signal(self):
        """Test sample_entropy on a normal random signal."""
        np.random.seed(42)
        data = np.random.randn(1000)
        result = sample_entropy(data, m=2, r=0.2)
        assert not np.isnan(result), "sample_entropy returned NaN on normal signal"
        assert not np.isinf(result), "sample_entropy returned Inf on normal signal"
        assert isinstance(result, float), "sample_entropy did not return a float"

    def test_approximate_entropy_no_nan_inf_normal_signal(self):
        """Test approximate_entropy on a normal random signal."""
        np.random.seed(42)
        data = np.random.randn(1000)
        result = approximate_entropy(data, m=2, r=0.2)
        assert not np.isnan(result), "approximate_entropy returned NaN on normal signal"
        assert not np.isinf(result), "approximate_entropy returned Inf on normal signal"
        assert isinstance(result, float), "approximate_entropy did not return a float"

    def test_sample_entropy_no_nan_inf_sine_wave(self):
        """Test sample_entropy on a periodic signal (sine wave)."""
        t = np.linspace(0, 10, 1000)
        data = np.sin(t)
        result = sample_entropy(data, m=2, r=0.2)
        assert not np.isnan(result), "sample_entropy returned NaN on sine wave"
        assert not np.isinf(result), "sample_entropy returned Inf on sine wave"

    def test_approximate_entropy_no_nan_inf_sine_wave(self):
        """Test approximate_entropy on a periodic signal (sine wave)."""
        t = np.linspace(0, 10, 1000)
        data = np.sin(t)
        result = approximate_entropy(data, m=2, r=0.2)
        assert not np.isnan(result), "approximate_entropy returned NaN on sine wave"
        assert not np.isinf(result), "approximate_entropy returned Inf on sine wave"

    def test_sample_entropy_no_nan_inf_constant_signal(self):
        """Test sample_entropy on a constant signal (edge case)."""
        data = np.ones(1000)
        # Constant signals often result in 0 entropy or undefined behavior depending on r.
        # We test that it does not crash or return NaN/Inf.
        result = sample_entropy(data, m=2, r=0.2)
        assert not np.isnan(result), "sample_entropy returned NaN on constant signal"
        assert not np.isinf(result), "sample_entropy returned Inf on constant signal"

    def test_approximate_entropy_no_nan_inf_constant_signal(self):
        """Test approximate_entropy on a constant signal (edge case)."""
        data = np.ones(1000)
        result = approximate_entropy(data, m=2, r=0.2)
        assert not np.isnan(result), "approximate_entropy returned NaN on constant signal"
        assert not np.isinf(result), "approximate_entropy returned Inf on constant signal"

    def test_sample_entropy_no_nan_inf_small_r(self):
        """Test sample_entropy with a very small r value."""
        np.random.seed(42)
        data = np.random.randn(500)
        result = sample_entropy(data, m=2, r=0.01)
        assert not np.isnan(result), "sample_entropy returned NaN with small r"
        assert not np.isinf(result), "sample_entropy returned Inf with small r"

    def test_approximate_entropy_no_nan_inf_small_r(self):
        """Test approximate_entropy with a very small r value."""
        np.random.seed(42)
        data = np.random.randn(500)
        result = approximate_entropy(data, m=2, r=0.01)
        assert not np.isnan(result), "approximate_entropy returned NaN with small r"
        assert not np.isinf(result), "approximate_entropy returned Inf with small r"

    def test_sample_entropy_short_signal(self):
        """Test sample_entropy on a signal barely long enough for m=2."""
        data = np.random.randn(10)
        result = sample_entropy(data, m=2, r=0.2)
        assert not np.isnan(result), "sample_entropy returned NaN on short signal"
        assert not np.isinf(result), "sample_entropy returned Inf on short signal"

    def test_approximate_entropy_short_signal(self):
        """Test approximate_entropy on a signal barely long enough for m=2."""
        data = np.random.randn(10)
        result = approximate_entropy(data, m=2, r=0.2)
        assert not np.isnan(result), "approximate_entropy returned NaN on short signal"
        assert not np.isinf(result), "approximate_entropy returned Inf on short signal"

    def test_sample_entropy_large_signal(self):
        """Test sample_entropy on a larger signal to ensure scalability."""
        np.random.seed(42)
        data = np.random.randn(5000)
        result = sample_entropy(data, m=2, r=0.2)
        assert not np.isnan(result), "sample_entropy returned NaN on large signal"
        assert not np.isinf(result), "sample_entropy returned Inf on large signal"

    def test_approximate_entropy_large_signal(self):
        """Test approximate_entropy on a larger signal to ensure scalability."""
        np.random.seed(42)
        data = np.random.randn(5000)
        result = approximate_entropy(data, m=2, r=0.2)
        assert not np.isnan(result), "approximate_entropy returned NaN on large signal"
        assert not np.isinf(result), "approximate_entropy returned Inf on large signal"

    def test_sample_entropy_with_noise(self):
        """Test sample_entropy on a signal with added noise."""
        t = np.linspace(0, 10, 1000)
        data = np.sin(t) + 0.5 * np.random.randn(1000)
        result = sample_entropy(data, m=2, r=0.2)
        assert not np.isnan(result), "sample_entropy returned NaN on noisy signal"
        assert not np.isinf(result), "sample_entropy returned Inf on noisy signal"

    def test_approximate_entropy_with_noise(self):
        """Test approximate_entropy on a signal with added noise."""
        t = np.linspace(0, 10, 1000)
        data = np.sin(t) + 0.5 * np.random.randn(1000)
        result = approximate_entropy(data, m=2, r=0.2)
        assert not np.isnan(result), "approximate_entropy returned NaN on noisy signal"
        assert not np.isinf(result), "approximate_entropy returned Inf on noisy signal"

    def test_sample_entropy_input_type_float64(self):
        """Ensure sample_entropy handles float64 input correctly."""
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0] * 200, dtype=np.float64)
        result = sample_entropy(data, m=2, r=0.2)
        assert not np.isnan(result)
        assert not np.isinf(result)

    def test_approximate_entropy_input_type_float64(self):
        """Ensure approximate_entropy handles float64 input correctly."""
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0] * 200, dtype=np.float64)
        result = approximate_entropy(data, m=2, r=0.2)
        assert not np.isnan(result)
        assert not np.isinf(result)