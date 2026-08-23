import pytest
import numpy as np
import os
import sys
from pathlib import Path
import tempfile
import json

from src.data.benchmarks import (
    generate_polynomial_test_data,
    generate_training_data,
    generate_fourier_test_data,
    verify_independence
)


class TestPolynomialSurface:
    """Test polynomial surface generation for T008c"""

    def test_polynomial_generation_basic(self, tmp_path):
        """Test basic polynomial test data generation"""
        output_path = tmp_path / "test_poly.npy"
        data = generate_polynomial_test_data(
            n_samples=100,
            n_features=3,
            degree=2,
            seed=42,
            output_path=str(output_path)
        )

        # Check file was created
        assert output_path.exists()

        # Check shape
        assert data.shape == (100, 4)  # 3 features + 1 target

        # Check data loaded correctly
        loaded = np.load(output_path)
        assert np.allclose(data, loaded)

    def test_polynomial_independence_from_lorenz(self, tmp_path):
        """Verify polynomial data is independent from Lorenz by design"""
        # Generate both datasets
        train_data = generate_training_data(n_samples=100, seed=123)
        test_data = generate_polynomial_test_data(n_samples=100, seed=42)

        # Verify independence function works
        assert verify_independence(train_data, test_data) is True

    def test_polynomial_degree_variety(self, tmp_path):
        """Test different polynomial degrees produce different data"""
        data_deg2 = generate_polynomial_test_data(n_samples=50, degree=2, seed=42)
        data_deg3 = generate_polynomial_test_data(n_samples=50, degree=3, seed=42)

        # Different degrees should produce different distributions
        assert not np.allclose(data_deg2, data_deg3)

    def test_reproducibility(self, tmp_path):
        """Test that same seed produces identical results"""
        output1 = tmp_path / "test1.npy"
        output2 = tmp_path / "test2.npy"

        data1 = generate_polynomial_test_data(n_samples=50, seed=12345, output_path=str(output1))
        data2 = generate_polynomial_test_data(n_samples=50, seed=12345, output_path=str(output2))

        assert np.allclose(data1, data2)


class TestLorenzAttractor:
    """Test Lorenz attractor training data generation"""

    def test_lorenz_generation(self, tmp_path):
        """Test Lorenz data generation"""
        output_path = tmp_path / "lorenz.npy"
        data = generate_training_data(n_samples=100, seed=123, output_path=str(output_path))

        assert output_path.exists()
        assert data.shape == (100, 3)

    def test_lorenz_bounded(self):
        """Lorenz attractor should be bounded within reasonable limits"""
        data = generate_training_data(n_samples=1000, seed=123)
        # Lorenz attractor stays within roughly [-20, 20] for standard parameters
        assert np.all(np.abs(data) < 30)


class TestFourierSeries:
    """Test Fourier series test data generation"""

    def test_fourier_generation(self, tmp_path):
        """Test Fourier data generation"""
        output_path = tmp_path / "fourier.npy"
        data = generate_fourier_test_data(n_samples=50, seed=43, output_path=str(output_path))

        assert output_path.exists()
        assert data.shape == (50, 4)  # 3 features + 1 target


class TestNoiseInjection:
    """Test noise injection in data generation"""

    def test_noise_addition(self):
        """Verify noise is added to polynomial data"""
        data1 = generate_polynomial_test_data(n_samples=100, seed=42)
        data2 = generate_polynomial_test_data(n_samples=100, seed=42)

        # Same seed should give same noise
        assert np.allclose(data1, data2)

        # Different seed should give different noise
        data3 = generate_polynomial_test_data(n_samples=100, seed=43)
        assert not np.allclose(data1, data3)


class TestGenerateSyntheticDataset:
    """Test overall dataset generation workflow"""

    def test_full_generation_pipeline(self, tmp_path):
        """Test complete generation of all datasets"""
        data_dir = tmp_path / "results"
        data_dir.mkdir()

        # Generate all three datasets
        train = generate_training_data(100, seed=123)
        poly_test = generate_polynomial_test_data(50, seed=42)
        fourier_test = generate_fourier_test_data(50, seed=43)

        # Verify shapes
        assert train.shape[1] == 3
        assert poly_test.shape[1] == 6  # 5 features + 1 target (default)
        assert fourier_test.shape[1] == 4  # 3 features + 1 target (default)


class TestIndependenceThreshold:
    """Test independence verification logic"""

    def test_independent_generators(self):
        """Test that different generators pass independence check"""
        train = generate_training_data(100, seed=123)
        test = generate_polynomial_test_data(100, seed=42)

        assert verify_independence(train, test) is True

    def test_identical_data_fails(self):
        """Test that identical data fails independence check"""
        data = generate_training_data(100, seed=123)

        # Same data should fail (ranges will be identical)
        # Note: This is a simplified check - in practice we expect different generators
        result = verify_independence(data, data)
        # The function returns False when ranges are identical
        assert result is False


class TestEdgeCases:
    """Test edge cases in data generation"""

    def test_single_sample(self, tmp_path):
        """Test generation with single sample"""
        output = tmp_path / "single.npy"
        data = generate_polynomial_test_data(n_samples=1, seed=42, output_path=str(output))
        assert data.shape == (1, 6)  # 5 features + 1 target

    def test_high_degree_polynomial(self, tmp_path):
        """Test high degree polynomial generation"""
        output = tmp_path / "high_deg.npy"
        data = generate_polynomial_test_data(n_samples=10, degree=5, seed=42, output_path=str(output))
        assert data.shape == (10, 6)

    def test_large_feature_space(self, tmp_path):
        """Test with many features"""
        output = tmp_path / "many_feat.npy"
        data = generate_polynomial_test_data(n_samples=10, n_features=10, seed=42, output_path=str(output))
        assert data.shape == (10, 11)  # 10 features + 1 target