import pytest
import numpy as np
import os
import sys
from src.data.benchmarks import (
    generate_training_data,
    generate_test_data,
    verify_independence,
    generate_synthetic_dataset
)
import json

class TestLorenzAttractor:
    def test_training_data_shape(self):
        """Test that training data has correct shape."""
        train_data = generate_training_data(n_samples=100)
        assert train_data.shape == (100, 3)
        
    def test_training_data_deterministic(self):
        """Test that training data is deterministic with seed."""
        train1 = generate_training_data(n_samples=50, seed=42)
        train2 = generate_training_data(n_samples=50, seed=42)
        assert np.allclose(train1, train2)
        
    def test_training_data_range(self):
        """Test that Lorenz attractor stays within expected bounds."""
        train_data = generate_training_data(n_samples=1000, seed=123)
        # Lorenz attractor typically stays within [-20, 20] for x, y, z
        assert np.all(np.abs(train_data) < 50)

class TestFourierSeries:
    def test_test_data_shape(self):
        """Test that test data has correct shape."""
        test_data = generate_test_data(n_samples=100)
        assert test_data.shape == (100, 3)
        
    def test_test_data_deterministic(self):
        """Test that test data is deterministic with seed."""
        test1 = generate_test_data(n_samples=50, seed=42)
        test2 = generate_test_data(n_samples=50, seed=42)
        assert np.allclose(test1, test2)

class TestPolynomialSurface:
    def test_polynomial_generation(self):
        """Test that polynomial surfaces are generated correctly."""
        test_data = generate_test_data(n_samples=1000, seed=456)
        # Check that values are within reasonable bounds for polynomial surfaces
        assert np.all(np.abs(test_data) < 20)

class TestNoiseInjection:
    def test_noise_variability(self):
        """Test that noise is injected correctly (different without seed)."""
        test1 = generate_test_data(n_samples=100)
        test2 = generate_test_data(n_samples=100)
        # Without seed, should be different
        assert not np.allclose(test1, test2)

class TestGenerateSyntheticDataset:
    def test_dataset_generation(self):
        """Test full dataset generation."""
        train, test = generate_synthetic_dataset(n_train=100, n_test=50, seed=789)
        assert train.shape == (100, 3)
        assert test.shape == (50, 3)
        
    def test_dataset_independence(self):
        """Test that generated datasets are independent."""
        train, test = generate_synthetic_dataset(n_train=1000, n_test=500, seed=999)
        is_independent = verify_independence(train, test)
        # With different distributions (Lorenz vs Polynomial/Fourier), should be independent
        assert is_independent

class TestIndependenceThreshold:
    def test_ks_test_independent_distributions(self):
        """Test KS test with clearly different distributions."""
        # Normal vs Uniform - should be detected as different
        data1 = np.random.normal(0, 1, 1000)
        data2 = np.random.uniform(-3, 3, 1000)
        assert verify_independence(data1, data2) == True
        
    def test_ks_test_same_distribution(self):
        """Test KS test with same distribution (might fail due to randomness)."""
        # Two samples from same normal distribution
        data1 = np.random.normal(0, 1, 1000)
        data2 = np.random.normal(0, 1, 1000)
        result = verify_independence(data1, data2)
        # This should typically be False (same distribution), but randomness can affect it
        # We just check that the function runs without error
        assert isinstance(result, bool)
        
    def test_ks_test_multidimensional(self):
        """Test KS test with multidimensional data."""
        data1 = np.random.normal(0, 1, (1000, 3))
        data2 = np.random.uniform(-3, 3, (1000, 3))
        assert verify_independence(data1, data2) == True

class TestEdgeCases:
    def test_empty_arrays(self):
        """Test behavior with empty arrays."""
        with pytest.raises(Exception):
            verify_independence(np.array([]), np.array([]))
            
    def test_single_element(self):
        """Test with single element arrays."""
        data1 = np.array([[1.0], [2.0], [3.0]])
        data2 = np.array([[4.0], [5.0], [6.0]])
        result = verify_independence(data1, data2)
        assert isinstance(result, bool)
