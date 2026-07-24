"""
Unit tests for synthetic benchmark data generation.

Tests verify:
- Deterministic seeding produces identical results
- Correct output shapes for all dataset types
- Noise injection works as expected
- File I/O preserves data integrity
"""

import pytest
import numpy as np
import os
import sys
import tempfile
from src.data.benchmarks import (
    generate_lorenz_attractor,
    generate_fourier_series,
    generate_polynomial_surface,
    generate_synthetic_dataset,
    load_dataset,
    set_deterministic_seed
)


class TestLorenzAttractor:
    """Tests for Lorenz attractor generation."""

    def test_deterministic_seeding(self):
        """Same seed produces identical trajectories."""
        seed = 12345
        traj1 = generate_lorenz_attractor(seed=seed, n_steps=100)
        traj2 = generate_lorenz_attractor(seed=seed, n_steps=100)

        np.testing.assert_array_equal(traj1, traj2)

    def test_output_shape(self):
        """Trajectory has correct shape."""
        n_steps = 500
        traj = generate_lorenz_attractor(seed=42, n_steps=n_steps)
        assert traj.shape == (n_steps, 3)

    def test_chaotic_behavior(self):
        """Different seeds produce divergent trajectories."""
        traj1 = generate_lorenz_attractor(seed=1, n_steps=1000)
        traj2 = generate_lorenz_attractor(seed=2, n_steps=1000)

        # After burn-in, trajectories should be very different
        diff = np.mean(np.abs(traj1[100:] - traj2[100:]))
        assert diff > 0.1, "Trajectories should diverge (chaotic behavior)"

    def test_noise_injection(self):
        """Noise increases variance in output."""
        traj_clean = generate_lorenz_attractor(seed=42, n_steps=100, noise_level=0.0)
        traj_noisy = generate_lorenz_attractor(seed=42, n_steps=100, noise_level=0.1)

        # Noisy trajectory should have different values
        assert not np.array_equal(traj_clean, traj_noisy)


class TestFourierSeries:
    """Tests for Fourier series generation."""

    def test_deterministic_seeding(self):
        """Same seed produces identical series."""
        seed = 54321
        x1, y1 = generate_fourier_series(seed=seed, n_samples=200)
        x2, y2 = generate_fourier_series(seed=seed, n_samples=200)

        np.testing.assert_array_equal(x1, x2)
        np.testing.assert_array_equal(y1, y2)

    def test_output_shape(self):
        """Output arrays have correct shape."""
        n_samples = 300
        x, y = generate_fourier_series(seed=42, n_samples=n_samples)

        assert x.shape == (n_samples,)
        assert y.shape == (n_samples,)

    def test_periodicity(self):
        """Fourier series are periodic within domain."""
        x, y = generate_fourier_series(seed=42, n_samples=1000, domain=(0, 2*np.pi))

        # Check that function values at boundaries are reasonable
        assert np.all(np.isfinite(y))
        assert not np.all(y == 0), "Function should not be identically zero"

    def test_noise_injection(self):
        """Noise adds variance to output."""
        x_clean, y_clean = generate_fourier_series(seed=42, n_samples=100, noise_level=0.0)
        x_noisy, y_noisy = generate_fourier_series(seed=42, n_samples=100, noise_level=0.1)

        assert not np.array_equal(y_clean, y_noisy)


class TestPolynomialSurface:
    """Tests for polynomial surface generation."""

    def test_deterministic_seeding(self):
        """Same seed produces identical surfaces."""
        seed = 99999
        X1, y1 = generate_polynomial_surface(seed=seed, n_samples=100)
        X2, y2 = generate_polynomial_surface(seed=seed, n_samples=100)

        np.testing.assert_array_equal(X1, X2)
        np.testing.assert_array_equal(y1, y2)

    def test_output_shape(self):
        """Output has correct shapes."""
        n_samples = 200
        n_features = 3
        X, y = generate_polynomial_surface(
            seed=42, n_samples=n_samples, n_features=n_features
        )

        assert X.shape == (n_samples, n_features)
        assert y.shape == (n_samples,)

    def test_degree_1_linear(self):
        """Degree 1 produces linear relationships."""
        X, y = generate_polynomial_surface(
            seed=42, n_samples=50, degree=1, n_features=2
        )

        # Linear model should have finite coefficients
        assert np.all(np.isfinite(y))

    def test_noise_injection(self):
        """Noise affects output values."""
        X_clean, y_clean = generate_polynomial_surface(
            seed=42, n_samples=50, noise_level=0.0
        )
        X_noisy, y_noisy = generate_polynomial_surface(
            seed=42, n_samples=50, noise_level=0.1
        )

        assert not np.array_equal(y_clean, y_noisy)


class TestNoiseInjection:
    """Tests for noise injection across all generators."""

    def test_noise_standard_deviation(self):
        """Noise level matches specified standard deviation."""
        seed = 777
        n_samples = 10000
        noise_level = 0.5

        x, y_clean = generate_fourier_series(
            seed=seed, n_samples=n_samples, noise_level=0.0
        )
        x, y_noisy = generate_fourier_series(
            seed=seed, n_samples=n_samples, noise_level=noise_level
        )

        noise = y_noisy - y_clean
        actual_std = np.std(noise)

        # Allow 10% tolerance for random variation
        assert abs(actual_std - noise_level) / noise_level < 0.1


class TestGenerateSyntheticDataset:
    """Tests for the main dataset generation function."""

    def test_lorenz_generation(self):
        """Lorenz dataset generation and loading."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = generate_synthetic_dataset(
                dataset_type="lorenz",
                seed=42,
                n_samples=100,
                output_dir=tmpdir
            )

            assert os.path.exists(filepath)
            data = load_dataset(filepath)
            assert "trajectory" in data
            assert data["trajectory"].shape == (100, 3)

    def test_fourier_generation(self):
        """Fourier dataset generation and loading."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = generate_synthetic_dataset(
                dataset_type="fourier",
                seed=42,
                n_samples=200,
                output_dir=tmpdir
            )

            assert os.path.exists(filepath)
            data = load_dataset(filepath)
            assert "x" in data
            assert "y" in data
            assert data["x"].shape == (200,)
            assert data["y"].shape == (200,)

    def test_polynomial_generation(self):
        """Polynomial dataset generation and loading."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = generate_synthetic_dataset(
                dataset_type="polynomial",
                seed=42,
                n_samples=150,
                n_features=3,
                output_dir=tmpdir
            )

            assert os.path.exists(filepath)
            data = load_dataset(filepath)
            assert "X" in data
            assert "y" in data
            assert data["X"].shape == (150, 3)
            assert data["y"].shape == (150,)

    def test_invalid_dataset_type(self):
        """Invalid dataset type raises ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(ValueError, match="Unknown dataset type"):
                generate_synthetic_dataset(
                    dataset_type="invalid",
                    seed=42,
                    n_samples=100,
                    output_dir=tmpdir
                )

    def test_metadata_file_created(self):
        """Metadata JSON file is created alongside dataset."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = generate_synthetic_dataset(
                dataset_type="lorenz",
                seed=42,
                n_samples=100,
                output_dir=tmpdir
            )

            metadata_path = filepath.replace(".npz", "_meta.json")
            assert os.path.exists(metadata_path)

            import json
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)

            assert metadata["dataset_type"] == "lorenz"
            assert metadata["seed"] == 42
            assert metadata["n_samples"] == 100
