import pytest
import numpy as np
import os
import sys
from src.data.benchmarks import (
    generate_lorenz_attractor,
    generate_fourier_series,
    generate_polynomial_surface,
    generate_synthetic_dataset,
    add_noise
)

class TestLorenzAttractor:
    """Contract test for Lorenz Attractor distribution and determinism."""

    def test_deterministic_seeding(self):
        """Verify that same seed produces identical output."""
        data1 = generate_lorenz_attractor(n_points=100, seed=42)
        data2 = generate_lorenz_attractor(n_points=100, seed=42)
        np.testing.assert_array_almost_equal(data1, data2)

    def test_shape_consistency(self):
        """Verify output shape matches (n_points, 3) for x, y, z."""
        n = 250
        data = generate_lorenz_attractor(n_points=n)
        assert data.shape == (n, 3)

    def test_independent_test_set_distribution(self):
        """
        Contract test: Verify the independent test set distribution properties.
        The test set must be statistically distinct from the training set
        while maintaining the same underlying dynamical system properties.
        """
        # Generate training set
        train_data = generate_lorenz_attractor(n_points=1000, seed=123)
        
        # Generate independent test set with different seed
        test_data = generate_lorenz_attractor(n_points=1000, seed=456)
        
        # Verify they are not identical (different seeds)
        assert not np.array_equal(train_data, test_data)
        
        # Verify both share similar statistical properties of the Lorenz attractor
        # (mean, variance should be roughly in the same ballpark for chaotic attractor)
        train_mean = np.mean(train_data, axis=0)
        test_mean = np.mean(test_data, axis=0)
        
        # The Lorenz attractor has a known mean near [0, 0, 0] in centered coordinates
        # or specific values depending on parameters. We check for consistency.
        assert np.allclose(train_mean, test_mean, rtol=0.1), \
            f"Train mean {train_mean} and test mean {test_mean} differ significantly"

        # Verify variance consistency (chaotic attractor properties)
        train_var = np.var(train_data, axis=0)
        test_var = np.var(test_data, axis=0)
        assert np.allclose(train_var, test_var, rtol=0.1), \
            f"Train var {train_var} and test var {test_var} differ significantly"

        # Ensure the test set covers the attractor's range
        # (Lorenz attractor typically spans roughly -20 to 20 in x, y)
        assert np.min(train_data) < -5, "Train set does not cover expected range"
        assert np.max(train_data) > 5, "Train set does not cover expected range"
        assert np.min(test_data) < -5, "Test set does not cover expected range"
        assert np.max(test_data) > 5, "Test set does not cover expected range"


class TestFourierSeries:
    """Contract test for Fourier Series generation and distribution."""

    def test_deterministic_seeding(self):
        """Verify that same seed produces identical output."""
        data1 = generate_fourier_series(n_points=100, seed=42)
        data2 = generate_fourier_series(n_points=100, seed=42)
        np.testing.assert_array_almost_equal(data1, data2)

    def test_shape_consistency(self):
        """Verify output shape matches (n_points, 2) for x, y."""
        n = 250
        data = generate_fourier_series(n_points=n)
        assert data.shape == (n, 2)

    def test_independent_test_set_distribution(self):
        """
        Contract test: Verify independent test set distribution for Fourier series.
        Test set must represent the same frequency components as training set
        but with different phase shifts or time windows.
        """
        train_data = generate_fourier_series(n_points=1000, seed=123)
        test_data = generate_fourier_series(n_points=1000, seed=456)

        assert not np.array_equal(train_data, test_data)

        # Verify periodicity properties are preserved
        # Check that the range of y-values is similar (amplitude consistency)
        train_y_range = np.ptp(train_data[:, 1])
        test_y_range = np.ptp(test_data[:, 1])
        assert np.isclose(train_y_range, test_y_range, rtol=0.1), \
            f"Amplitude mismatch: train {train_y_range} vs test {test_y_range}"

        # Verify x-range consistency (time domain)
        train_x_range = np.ptp(train_data[:, 0])
        test_x_range = np.ptp(test_data[:, 0])
        assert np.isclose(train_x_range, test_x_range, rtol=0.1), \
            f"Time domain mismatch: train {train_x_range} vs test {test_x_range}"


class TestPolynomialSurface:
    """Contract test for Polynomial Surface generation and distribution."""

    def test_deterministic_seeding(self):
        """Verify that same seed produces identical output."""
        data1 = generate_polynomial_surface(n_points=100, seed=42)
        data2 = generate_polynomial_surface(n_points=100, seed=42)
        np.testing.assert_array_almost_equal(data1, data2)

    def test_shape_consistency(self):
        """Verify output shape matches (n_points, 3) for x, y, z."""
        n = 250
        data = generate_polynomial_surface(n_points=n)
        assert data.shape == (n, 3)

    def test_independent_test_set_distribution(self):
        """
        Contract test: Verify independent test set distribution for polynomial surfaces.
        Test set must sample the same polynomial function over a disjoint domain
        or with different noise realizations.
        """
        train_data = generate_polynomial_surface(n_points=1000, seed=123)
        test_data = generate_polynomial_surface(n_points=1000, seed=456)

        assert not np.array_equal(train_data, test_data)

        # Verify that the polynomial relationship (z ~ f(x,y)) holds for both
        # We check the variance of z relative to x and y
        train_z_var = np.var(train_data[:, 2])
        test_z_var = np.var(test_data[:, 2])
        assert np.isclose(train_z_var, test_z_var, rtol=0.15), \
            f"Output variance mismatch: train {train_z_var} vs test {test_z_var}"


class TestNoiseInjection:
    """Contract test for noise injection mechanism."""

    def test_noise_addition(self):
        """Verify noise is actually added and changes the data."""
        clean_data = np.array([[1.0, 2.0], [3.0, 4.0]])
        noisy_data = add_noise(clean_data, noise_level=0.1, seed=42)
        
        # Noise must change the values
        assert not np.array_equal(clean_data, noisy_data)
        
        # Noise must be bounded by the noise_level parameter
        diff = np.abs(noisy_data - clean_data)
        assert np.all(diff <= noise_level * np.max(np.abs(clean_data)) * 1.1), \
            "Noise exceeds expected bounds"

    def test_deterministic_noise(self):
        """Verify noise is deterministic with seed."""
        clean_data = np.array([[1.0, 2.0], [3.0, 4.0]])
        noisy1 = add_noise(clean_data, noise_level=0.1, seed=42)
        noisy2 = add_noise(clean_data, noise_level=0.1, seed=42)
        
        np.testing.assert_array_almost_equal(noisy1, noisy2)


class TestGenerateSyntheticDataset:
    """Contract test for the full synthetic dataset generation pipeline."""

    def test_full_dataset_structure(self):
        """Verify the full dataset generation returns correct structure."""
        dataset = generate_synthetic_dataset(
            task_type="lorenz",
            train_size=100,
            test_size=50,
            seed=42
        )

        assert "train" in dataset
        assert "test" in dataset
        assert "metadata" in dataset

        assert dataset["train"].shape[0] == 100
        assert dataset["test"].shape[0] == 50

    def test_independent_test_set_contract(self):
        """
        High-level contract test: Verify the generated test set is independent
        and follows the same distribution as the training set, as required
        for valid model evaluation in US1.
        """
        dataset = generate_synthetic_dataset(
            task_type="fourier",
            train_size=500,
            test_size=200,
            seed=999
        )

        train = dataset["train"]
        test = dataset["test"]

        # 1. Independence: Seeds must produce different data
        assert not np.array_equal(train, test)

        # 2. Distribution Consistency: Mean and Variance should be close
        train_mean = np.mean(train, axis=0)
        test_mean = np.mean(test, axis=0)
        
        # Allow 10% tolerance for chaotic/stochastic systems
        assert np.allclose(train_mean, test_mean, rtol=0.1), \
            "Test set mean deviates significantly from training set"

        train_var = np.var(train, axis=0)
        test_var = np.var(test, axis=0)
        assert np.allclose(train_var, test_var, rtol=0.1), \
            "Test set variance deviates significantly from training set"

        # 3. Metadata integrity
        assert dataset["metadata"]["task_type"] == "fourier"
        assert dataset["metadata"]["train_size"] == 500
        assert dataset["metadata"]["test_size"] == 200
        assert dataset["metadata"]["seed"] == 999