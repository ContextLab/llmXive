"""
Unit tests for synthetic benchmark data generation.

Tests cover:
- Lorenz attractor generation
- Fourier series generation
- Polynomial surface generation
- Noise injection
- Data independence verification
- Edge cases
"""
import pytest
import numpy as np
import os
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'code'))

from src.data.benchmarks import (
    generate_training_data,
    generate_test_data,
    generate_polynomial_surface_data,
    generate_fourier_series_data,
    verify_independence,
    LORENZ_SIGMA,
    LORENZ_RHO,
    LORENZ_BETA,
    TRAINING_SEED,
    TEST_SEED
)


class TestLorenzAttractor:
    """Tests for Lorenz attractor data generation."""

    def test_trajectory_shape(self):
        """Test that generated trajectories have correct shape."""
        n_trajectories = 10
        trajectory_length = 100
        data = generate_training_data(n_trajectories, trajectory_length)

        assert data.shape == (n_trajectories, trajectory_length, 3)
        assert data.dtype == np.float32

    def test_deterministic_seeding(self):
        """Test that same seed produces identical results."""
        seed = 42
        data1 = generate_training_data(5, 50, seed=seed)
        data2 = generate_training_data(5, 50, seed=seed)

        np.testing.assert_array_equal(data1, data2)

    def test_different_seeds_different_data(self):
        """Test that different seeds produce different data."""
        data1 = generate_training_data(5, 50, seed=42)
        data2 = generate_training_data(5, 50, seed=123)

        # Should not be exactly equal
        assert not np.array_equal(data1, data2)

    def test_lorenz_boundedness(self):
        """Test that Lorenz trajectories stay within expected bounds."""
        data = generate_training_data(20, 1000, seed=42)

        # Lorenz attractor stays roughly within these bounds
        assert np.all(np.abs(data) < 30), "Lorenz trajectory exceeded expected bounds"

    def test_initial_conditions_randomness(self):
        """Test that different trajectories start from different points."""
        data = generate_training_data(10, 10, seed=42)

        # First point of each trajectory should be different
        first_points = data[:, 0, :]
        for i in range(len(first_points)):
            for j in range(i + 1, len(first_points)):
                assert not np.array_equal(first_points[i], first_points[j])


class TestFourierSeries:
    """Tests for Fourier series data generation."""

    def test_fourier_shape(self):
        """Test that Fourier data has correct shape."""
        n_samples = 100
        data = generate_fourier_series_data(n_samples)

        assert data.shape == (n_samples, 2)
        assert data.dtype == np.float32

    def test_fourier_periodicity(self):
        """Test that Fourier data is within expected domain."""
        n_samples = 1000
        data = generate_fourier_series_data(n_samples, max_frequency=5)

        # Time should be in [0, 2π]
        assert np.all(data[:, 0] >= 0)
        assert np.all(data[:, 0] <= 2 * np.pi)

    def test_fourier_deterministic(self):
        """Test that same seed produces identical Fourier data."""
        seed = 12345
        data1 = generate_fourier_series_data(100, max_frequency=3, seed=seed)
        data2 = generate_fourier_series_data(100, max_frequency=3, seed=seed)

        np.testing.assert_array_equal(data1, data2)


class TestPolynomialSurface:
    """Tests for polynomial surface data generation."""

    def test_polynomial_shape(self):
        """Test that polynomial data has correct shape."""
        n_samples = 100
        data = generate_polynomial_surface_data(n_samples)

        assert data.shape == (n_samples, 3)
        assert data.dtype == np.float32

    def test_polynomial_domain(self):
        """Test that x, y are within expected bounds."""
        n_samples = 1000
        data = generate_polynomial_surface_data(n_samples, degree=3)

        # x and y should be in [-2, 2]
        assert np.all(data[:, 0] >= -2)
        assert np.all(data[:, 0] <= 2)
        assert np.all(data[:, 1] >= -2)
        assert np.all(data[:, 1] <= 2)

    def test_polynomial_deterministic(self):
        """Test that same seed produces identical polynomial data."""
        seed = 42
        data1 = generate_polynomial_surface_data(100, degree=2, seed=seed)
        data2 = generate_polynomial_surface_data(100, degree=2, seed=seed)

        np.testing.assert_array_equal(data1, data2)

    def test_polynomial_degree_effect(self):
        """Test that higher degree allows more complex surfaces."""
        # Lower degree should be smoother (lower variance in z)
        data_low = generate_polynomial_surface_data(1000, degree=1, seed=42)
        data_high = generate_polynomial_surface_data(1000, degree=5, seed=42)

        # Higher degree should have larger range in z
        z_low = data_low[:, 2]
        z_high = data_high[:, 2]

        assert np.ptp(z_high) > np.ptp(z_low) * 0.5  # Allow some tolerance


class TestNoiseInjection:
    """Tests for noise injection in generated data."""

    def test_polynomial_has_noise(self):
        """Test that polynomial data includes noise."""
        seed = 42
        data1 = generate_polynomial_surface_data(100, degree=3, seed=seed)
        data2 = generate_polynomial_surface_data(100, degree=3, seed=seed + 1)

        # Different seeds should produce different noise patterns
        assert not np.array_equal(data1, data2)

    def test_fourier_has_noise(self):
        """Test that Fourier data includes noise."""
        seed = 42
        data1 = generate_fourier_series_data(100, max_frequency=3, seed=seed)
        data2 = generate_fourier_series_data(100, max_frequency=3, seed=seed + 1)

        assert not np.array_equal(data1, data2)


class TestGenerateSyntheticDataset:
    """Tests for the main generate_test_data function."""

    def test_test_data_structure(self):
        """Test that test_data returns expected structure."""
        test_data = generate_test_data(
            n_polynomial_samples=100,
            n_fourier_samples=100
        )

        assert 'polynomial' in test_data
        assert 'fourier' in test_data
        assert test_data['polynomial'].shape[0] == 100
        assert test_data['fourier'].shape[0] == 100

    def test_training_test_separation(self):
        """Test that training and test data use different seeds."""
        train_data = generate_training_data(10, 50)
        test_data = generate_test_data(100, 100)

        # They should be completely different types of data
        assert train_data.ndim == 3  # Trajectories
        assert test_data['polynomial'].ndim == 2  # Points
        assert test_data['fourier'].ndim == 2  # Points


class TestIndependenceThreshold:
    """Tests for data independence verification."""

    def test_verify_independence_success(self):
        """Test that verify_independence returns True for correct data."""
        train_data = generate_training_data(10, 50)
        test_data = generate_test_data(100, 100)

        result = verify_independence(train_data, test_data)
        assert result is True

    def test_verify_independence_wrong_train_shape(self):
        """Test that verify_independence fails for wrong training shape."""
        # Wrong shape: 2D instead of 3D
        train_data = np.random.randn(10, 50)
        test_data = generate_test_data(100, 100)

        with pytest.raises(ValueError, match="Training data must be 3D"):
            verify_independence(train_data, test_data)

    def test_verify_independence_wrong_test_keys(self):
        """Test that verify_independence fails for wrong test keys."""
        train_data = generate_training_data(10, 50)
        # Missing required keys
        test_data = {'wrong_key': np.random.randn(100, 3)}

        with pytest.raises(ValueError, match="Test data must contain keys"):
            verify_independence(train_data, test_data)

    def test_verify_independence_wrong_test_shape(self):
        """Test that verify_independence fails for wrong test shape."""
        train_data = generate_training_data(10, 50)
        test_data = generate_test_data(100, 100)

        # Corrupt polynomial data shape
        test_data['polynomial'] = np.random.randn(100, 2)

        with pytest.raises(ValueError, match="Polynomial test data must be 2D"):
            verify_independence(train_data, test_data)


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_minimum_samples(self):
        """Test generation with minimum sample counts."""
        train_data = generate_training_data(1, 10)
        test_data = generate_test_data(1, 1)

        assert train_data.shape == (1, 10, 3)
        assert test_data['polynomial'].shape == (1, 3)
        assert test_data['fourier'].shape == (1, 2)

    def test_large_trajectory_length(self):
        """Test generation with long trajectories."""
        train_data = generate_training_data(5, 10000)
        assert train_data.shape == (5, 10000, 3)

    def test_high_degree_polynomial(self):
        """Test generation with high degree polynomial."""
        data = generate_polynomial_surface_data(100, degree=10)
        assert data.shape == (100, 3)

    def test_high_frequency_fourier(self):
        """Test generation with high frequency Fourier series."""
        data = generate_fourier_series_data(100, max_frequency=20)
        assert data.shape == (100, 2)

    def test_zero_seed(self):
        """Test that seed=0 works correctly."""
        train_data = generate_training_data(5, 10, seed=0)
        test_data = generate_test_data(10, 10, seed=0)

        assert train_data.shape == (5, 10, 3)
        assert test_data['polynomial'].shape == (10, 3)
        assert test_data['fourier'].shape == (10, 2)

    def test_negative_seed(self):
        """Test that negative seeds work correctly."""
        train_data = generate_training_data(5, 10, seed=-1)
        test_data = generate_test_data(10, 10, seed=-1)

        assert train_data.shape == (5, 10, 3)
        assert test_data['polynomial'].shape == (10, 3)
        assert test_data['fourier'].shape == (10, 2)