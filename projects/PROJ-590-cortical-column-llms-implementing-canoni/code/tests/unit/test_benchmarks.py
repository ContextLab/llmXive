"""
Unit tests for synthetic data generation in src/data/benchmarks.py.

Verifies:
1. Deterministic seeding (same seed -> same output)
2. Data shape consistency
3. Basic statistical properties (non-zero variance)
"""

import pytest
import numpy as np
import os
import sys

# Ensure code/src is in path for imports if running via pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from data.benchmarks import (
    generate_lorenz_attractor,
    generate_fourier_series,
    generate_polynomial_surface,
    BenchmarkConfig
)

class TestLorenzAttractor:
    def test_deterministic_seeding(self):
        config1 = BenchmarkConfig(seed=123, n_samples=100, noise_std=0.0)
        config2 = BenchmarkConfig(seed=123, n_samples=100, noise_std=0.0)
        
        data1 = generate_lorenz_attractor(config1)
        data2 = generate_lorenz_attractor(config2)

        assert np.allclose(data1['x'], data2['x']), "Lorenz x values should be identical with same seed"
        assert np.allclose(data1['y'], data2['y']), "Lorenz y values should be identical with same seed"
        assert np.allclose(data1['z'], data2['z']), "Lorenz z values should be identical with same seed"

    def test_output_shape(self):
        n_samples = 500
        config = BenchmarkConfig(seed=42, n_samples=n_samples, noise_std=0.0)
        data = generate_lorenz_attractor(config)

        assert len(data['t']) == n_samples
        assert len(data['x']) == n_samples
        assert len(data['y']) == n_samples
        assert len(data['z']) == n_samples

    def test_chaos_sensitivity(self):
        """Verify that small seed changes produce different trajectories (butterfly effect)."""
        config1 = BenchmarkConfig(seed=42, n_samples=100, noise_std=0.0)
        config2 = BenchmarkConfig(seed=43, n_samples=100, noise_std=0.0)
        
        data1 = generate_lorenz_attractor(config1)
        data2 = generate_lorenz_attractor(config2)

        # Trajectories should diverge
        assert not np.allclose(data1['x'], data2['x'], atol=0.1), "Trajectories should diverge with different seeds"

class TestFourierSeries:
    def test_deterministic_seeding(self):
        config1 = BenchmarkConfig(seed=99, n_samples=100, noise_std=0.0)
        config2 = BenchmarkConfig(seed=99, n_samples=100, noise_std=0.0)
        
        data1 = generate_fourier_series(config1)
        data2 = generate_fourier_series(config2)

        assert np.allclose(data1['signal'], data2['signal']), "Fourier signal should be identical with same seed"

    def test_output_shape(self):
        n_samples = 200
        config = BenchmarkConfig(seed=42, n_samples=n_samples, noise_std=0.0)
        data = generate_fourier_series(config)

        assert len(data['t']) == n_samples
        assert len(data['signal']) == n_samples
        assert len(data['frequencies']) > 0

    def test_periodicity(self):
        """Rough check that the signal is bounded and not exploding."""
        config = BenchmarkConfig(seed=42, n_samples=1000, noise_std=0.0)
        data = generate_fourier_series(config)
        
        assert np.isfinite(data['signal']).all(), "Signal must be finite"
        assert np.max(np.abs(data['signal'])) < 20.0, "Signal amplitude should be bounded"

class TestPolynomialSurface:
    def test_deterministic_seeding(self):
        config1 = BenchmarkConfig(seed=777, n_samples=100, noise_std=0.0)
        config2 = BenchmarkConfig(seed=777, n_samples=100, noise_std=0.0)
        
        data1 = generate_polynomial_surface(config1)
        data2 = generate_polynomial_surface(config2)

        assert np.allclose(data1['z'], data2['z']), "Polynomial z values should be identical with same seed"
        assert np.allclose(data1['x'], data2['x']), "Polynomial x values should be identical with same seed"
        assert np.allclose(data1['y'], data2['y']), "Polynomial y values should be identical with same seed"

    def test_output_shape(self):
        n_samples = 50
        config = BenchmarkConfig(seed=42, n_samples=n_samples, noise_std=0.0)
        data = generate_polynomial_surface(config)

        assert len(data['x']) == n_samples
        assert len(data['y']) == n_samples
        assert len(data['z']) == n_samples

    def test_non_zero_variance(self):
        config = BenchmarkConfig(seed=42, n_samples=1000, noise_std=0.0)
        data = generate_polynomial_surface(config)
        
        assert np.var(data['z']) > 0.0, "Polynomial surface must have non-zero variance"
        assert np.var(data['x']) > 0.0, "Input x must have variance"
        assert np.var(data['y']) > 0.0, "Input y must have variance"

class TestNoiseInjection:
    def test_noise_addition(self):
        config_no_noise = BenchmarkConfig(seed=42, n_samples=100, noise_std=0.0)
        config_with_noise = BenchmarkConfig(seed=42, n_samples=100, noise_std=1.0)
        
        data_clean = generate_lorenz_attractor(config_no_noise)
        data_noisy = generate_lorenz_attractor(config_with_noise)

        # With same seed, the deterministic part is same, but noise is added differently
        # So the values should differ
        assert not np.allclose(data_clean['x'], data_noisy['x']), "Noisy data should differ from clean data"
        
        # But the mean should be roughly similar (noise is zero mean)
        # This is a soft check, just ensuring we didn't break the generation logic
        assert np.abs(np.mean(data_clean['x']) - np.mean(data_noisy['x'])) < 1.0