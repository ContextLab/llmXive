"""
Unit tests for data generation functions in benchmarks.py
"""
import pytest
import numpy as np
import os
import tempfile
from pathlib import Path

import sys
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.data.benchmarks import (
    generate_training_data,
    generate_polynomial_test_data,
    verify_independence,
    save_data,
    load_data
)

class TestPolynomialTestDataGeneration:
    """Tests for T008c: generate_polynomial_test_data"""

    def test_generate_polynomial_test_data_shape(self):
        """Test that output has correct shape"""
        data = generate_polynomial_test_data(seed=42, n=1000)
        assert data.shape == (1000, 2), f"Expected shape (1000, 2), got {data.shape}"

    def test_generate_polynomial_test_data_deterministic(self):
        """Test that generation is deterministic with same seed"""
        data1 = generate_polynomial_test_data(seed=42, n=100)
        data2 = generate_polynomial_test_data(seed=42, n=100)
        np.testing.assert_array_equal(data1, data2)

    def test_generate_polynomial_test_data_polynomial(self):
        """Test that Y values match polynomial x^2 - 1"""
        data = generate_polynomial_test_data(seed=42, n=10, coeffs=[1, 0, -1], noise_std=0.0)
        X = data[:, 0]
        Y = data[:, 1]
        expected_Y = X**2 - 1
        np.testing.assert_array_almost_equal(Y, expected_Y, decimal=5)

    def test_generate_polynomial_test_data_with_noise(self):
        """Test that noise is added correctly"""
        np.random.seed(42)
        data_no_noise = generate_polynomial_test_data(seed=42, n=100, coeffs=[1, 0, -1], noise_std=0.0)
        data_with_noise = generate_polynomial_test_data(seed=42, n=100, coeffs=[1, 0, -1], noise_std=1.0)
        
        # With noise, values should differ
        assert not np.allclose(data_no_noise, data_with_noise)

    def test_generate_polynomial_test_data_save_load(self):
        """Test save and load functionality"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Temporarily override DATA_RESULTS_DIR
            original_dir = None
            import src.data.benchmarks as benchmarks_module
            original_dir = benchmarks_module.DATA_RESULTS_DIR
            benchmarks_module.DATA_RESULTS_DIR = Path(tmpdir)
            
            try:
                data = generate_polynomial_test_data(seed=42, n=50)
                output_path = save_data(data, "test_save.npy")
                
                loaded_data = load_data("test_save.npy")
                np.testing.assert_array_equal(data, loaded_data)
            finally:
                if original_dir:
                    benchmarks_module.DATA_RESULTS_DIR = original_dir

class TestLorenzTrainingDataGeneration:
    """Tests for generate_training_data (Lorenz)"""

    def test_generate_training_data_shape(self):
        """Test that Lorenz output has correct shape"""
        data = generate_training_data(seed=42, n_samples=1000)
        assert data.shape == (1000, 3), f"Expected shape (1000, 3), got {data.shape}"

    def test_generate_training_data_deterministic(self):
        """Test that generation is deterministic with same seed"""
        data1 = generate_training_data(seed=42, n_samples=100)
        data2 = generate_training_data(seed=42, n_samples=100)
        np.testing.assert_array_equal(data1, data2)

class TestIndependenceVerification:
    """Tests for verify_independence"""

    def test_verify_independence_different_distributions(self):
        """Test that Lorenz and Polynomial data are verified as independent"""
        train_data = generate_training_data(seed=42, n_samples=1000)
        test_data = generate_polynomial_test_data(seed=42, n=1000)
        
        # Should not raise an exception
        result = verify_independence(train_data, test_data)
        assert result is True

    def test_verify_independence_same_distribution_fails(self):
        """Test that identical data fails independence check"""
        data = generate_training_data(seed=42, n_samples=1000)
        
        # Use same data for both (should fail)
        with pytest.raises(ValueError):
            verify_independence(data, data)
