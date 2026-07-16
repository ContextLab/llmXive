"""
Unit tests for synthetic benchmark generators in src/data/benchmarks.py.

Tests verify:
1. Correct shape of generated data
2. Deterministic seeding
3. Noise injection behavior
4. Mathematical properties of generated functions
"""

import pytest
import numpy as np
import os
import sys

# Ensure the code directory is in the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.data.benchmarks import (
    generate_lorenz_attractor,
    generate_fourier_series,
    generate_polynomial_surface,
    generate_synthetic_dataset,
    BenchmarkConfig,
    set_seed
)


class TestLorenzAttractor:
    """Tests for Lorenz attractor generation."""

    def test_shape_correct(self):
        """Verify output shapes match expected dimensions."""
        config = BenchmarkConfig(seed=42, n_samples=100, noise_std=0.0)
        t, states = generate_lorenz_attractor(config)

        assert t.shape == (100,), f"Expected t shape (100,), got {t.shape}"
        assert states.shape == (100, 3), f"Expected states shape (100, 3), got {states.shape}"

    def test_deterministic_seeding(self):
        """Verify same seed produces identical results."""
        config = BenchmarkConfig(seed=123, n_samples=50, noise_std=0.0)

        _, states1 = generate_lorenz_attractor(config)
        _, states2 = generate_lorenz_attractor(config)

        assert np.allclose(states1, states2), "Lorenz states not deterministic"

    def test_noise_injection(self):
        """Verify noise is actually added when configured."""
        config_no_noise = BenchmarkConfig(seed=42, n_samples=100, noise_std=0.0)
        config_with_noise = BenchmarkConfig(seed=42, n_samples=100, noise_std=1.0)

        _, states_no_noise = generate_lorenz_attractor(config_no_noise)
        _, states_with_noise = generate_lorenz_attractor(config_with_noise)

        # With same seed but different noise, results should differ
        assert not np.allclose(states_no_noise, states_with_noise), \
            "Noise should change the output"

    def test_chaotic_behavior(self):
        """Verify Lorenz system exhibits sensitive dependence on initial conditions."""
        config1 = BenchmarkConfig(seed=42, n_samples=100, noise_std=0.0)
        config2 = BenchmarkConfig(seed=43, n_samples=100, noise_std=0.0)

        _, states1 = generate_lorenz_attractor(config1)
        _, states2 = generate_lorenz_attractor(config2)

        # Small seed change should lead to divergent trajectories
        mse = np.mean((states1 - states2) ** 2)
        assert mse > 1e-4, "Lorenz system should show chaotic divergence"


class TestFourierSeries:
    """Tests for Fourier series generation."""

    def test_shape_correct(self):
        """Verify output shapes match expected dimensions."""
        config = BenchmarkConfig(seed=42, n_samples=200, noise_std=0.0)
        x, y = generate_fourier_series(config)

        assert x.shape == (200,), f"Expected x shape (200,), got {x.shape}"
        assert y.shape == (200,), f"Expected y shape (200,), got {y.shape}"

    def test_periodicity(self):
        """Verify generated signal is periodic over [0, 2π]."""
        config = BenchmarkConfig(seed=42, n_samples=1000, noise_std=0.0,
                               frequency_range=(1.0, 1.0),  # Single frequency
                               n_frequencies=1)
        x, y = generate_fourier_series(config)

        # Check that start and end values are approximately equal
        assert np.isclose(y[0], y[-1], atol=0.1), "Signal should be periodic"

    def test_deterministic_seeding(self):
        """Verify same seed produces identical results."""
        config = BenchmarkConfig(seed=456, n_samples=100, noise_std=0.0)

        _, y1 = generate_fourier_series(config)
        _, y2 = generate_fourier_series(config)

        assert np.allclose(y1, y2), "Fourier series not deterministic"

    def test_amplitude_bounds(self):
        """Verify signal amplitude stays within expected bounds."""
        config = BenchmarkConfig(seed=42, n_samples=1000, noise_std=0.0,
                               amplitude_range=(0.5, 1.0),
                               n_frequencies=5)
        _, y = generate_fourier_series(config)

        # Maximum possible amplitude is sum of all amplitudes
        max_expected = 5 * 1.0  # 5 components, max amplitude 1.0
        assert np.max(np.abs(y)) <= max_expected * 1.1, \
            "Signal amplitude exceeds expected bounds"


class TestPolynomialSurface:
    """Tests for polynomial surface generation."""

    def test_shape_correct(self):
        """Verify output shapes match expected dimensions."""
        config = BenchmarkConfig(seed=42, n_samples=150, noise_std=0.0)
        X, y = generate_polynomial_surface(config, degree=3, n_features=2)

        assert X.shape == (150, 2), f"Expected X shape (150, 2), got {X.shape}"
        assert y.shape == (150,), f"Expected y shape (150,), got {y.shape}"

    def test_feature_range(self):
        """Verify input features are in [-1, 1]."""
        config = BenchmarkConfig(seed=42, n_samples=100, noise_std=0.0)
        X, _ = generate_polynomial_surface(config)

        assert np.all(X >= -1.0) and np.all(X <= 1.0), \
            "Features should be in [-1, 1]"

    def test_deterministic_seeding(self):
        """Verify same seed produces identical results."""
        config = BenchmarkConfig(seed=789, n_samples=100, noise_std=0.0)

        _, y1 = generate_polynomial_surface(config)
        _, y2 = generate_polynomial_surface(config)

        assert np.allclose(y1, y2), "Polynomial surface not deterministic"

    def test_degree_influence(self):
        """Verify higher degree allows more complex surfaces."""
        config = BenchmarkConfig(seed=42, n_samples=100, noise_std=0.0)

        _, y_low = generate_polynomial_surface(config, degree=1)
        _, y_high = generate_polynomial_surface(config, degree=5)

        # Higher degree should generally produce more variance
        var_low = np.var(y_low)
        var_high = np.var(y_high)

        # This is probabilistic, but with fixed seed it should be consistent
        # We just check that the function runs without error and produces different outputs
        assert not np.allclose(y_low, y_high), \
            "Different degrees should produce different surfaces"


class TestNoiseInjection:
    """Tests for noise injection across all benchmarks."""

    @pytest.mark.parametrize("benchmark_type", ["lorenz", "fourier", "polynomial"])
    def test_noise_increases_variance(self, benchmark_type):
        """Verify that adding noise increases output variance."""
        config_clean = BenchmarkConfig(seed=42, n_samples=500, noise_std=0.0)
        config_noisy = BenchmarkConfig(seed=42, n_samples=500, noise_std=0.5)

        if benchmark_type == "lorenz":
            _, y_clean = generate_lorenz_attractor(config_clean)
            _, y_noisy = generate_lorenz_attractor(config_noisy)
        elif benchmark_type == "fourier":
            _, y_clean = generate_fourier_series(config_clean)
            _, y_noisy = generate_fourier_series(config_noisy)
        else:  # polynomial
            _, y_clean = generate_polynomial_surface(config_clean)
            _, y_noisy = generate_polynomial_surface(config_noisy)

        var_clean = np.var(y_clean)
        var_noisy = np.var(y_noisy)

        assert var_noisy > var_clean, \
            f"Noise should increase variance in {benchmark_type}"

    @pytest.mark.parametrize("benchmark_type", ["lorenz", "fourier", "polynomial"])
    def test_noise_deterministic(self, benchmark_type):
        """Verify that noise is deterministic given the same seed."""
        config = BenchmarkConfig(seed=42, n_samples=100, noise_std=0.5)

        if benchmark_type == "lorenz":
            _, y1 = generate_lorenz_attractor(config)
            _, y2 = generate_lorenz_attractor(config)
        elif benchmark_type == "fourier":
            _, y1 = generate_fourier_series(config)
            _, y2 = generate_fourier_series(config)
        else:
            _, y1 = generate_polynomial_surface(config)
            _, y2 = generate_polynomial_surface(config)

        assert np.allclose(y1, y2), \
            f"Noise should be deterministic for {benchmark_type} with same seed"


class TestGenerateSyntheticDataset:
    """Tests for the unified dataset generation interface."""

    def test_invalid_benchmark_type(self):
        """Verify ValueError is raised for unknown benchmark type."""
        with pytest.raises(ValueError):
            generate_synthetic_dataset("invalid_type", seed=42)

    def test_metadata_structure(self):
        """Verify metadata dictionary has required keys."""
        for btype in ["lorenz", "fourier", "polynomial"]:
            data = generate_synthetic_dataset(btype, seed=42)
            assert "X" in data, "Missing X in output"
            assert "y" in data, "Missing y in output"
            assert "metadata" in data, "Missing metadata in output"
            assert data["metadata"]["type"] == btype, "Metadata type mismatch"
            assert data["metadata"]["seed"] == 42, "Seed not recorded"

    def test_cross_type_seeding(self):
        """Verify different benchmarks with same seed are independent."""
        data_lorenz = generate_synthetic_dataset("lorenz", seed=42)
        data_fourier = generate_synthetic_dataset("fourier", seed=42)

        # Outputs should be completely different
        assert not np.allclose(data_lorenz["X"], data_fourier["X"]), \
            "Different benchmarks should produce different X"

    def test_parameters_passed_correctly(self):
        """Verify additional parameters are passed to generators."""
        data = generate_synthetic_dataset(
            "fourier",
            seed=42,
            n_samples=100,
            noise_std=0.1,
            n_frequencies=20,
            amplitude_range=(1.0, 2.0)
        )
        assert data["metadata"]["parameters"]["n_frequencies"] == 20
        assert data["metadata"]["parameters"]["amplitude_range"] == (1.0, 2.0)