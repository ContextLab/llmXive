"""
Unit tests for code/simulation/engine.py

Tests cover:
- VIF calculation correctness
- Synthetic data generation
- Dataset instance serialization
"""
import pytest
import numpy as np
import os
import tempfile
import json

from simulation.config import SimulationConfig
from simulation.engine import (
    calculate_vif,
    generate_synthetic_data,
    DatasetInstance,
    save_dataset_instance,
    load_dataset_instance
)


class TestCalculateVIF:
    """Tests for the calculate_vif function."""

    def test_vif_independent_features(self):
        """VIF should be 1 for independent features (identity correlation)."""
        np.random.seed(42)
        X = np.random.normal(size=(100, 3))
        vif_scores = calculate_vif(X)
        # VIF should be close to 1 for uncorrelated features
        for vif in vif_scores.values():
            assert 0.9 <= vif <= 1.1, f"VIF {vif} expected ~1.0 for independent features"

    def test_vif_highly_correlated(self):
        """VIF should be high for highly correlated features."""
        # Create two perfectly correlated columns
        x1 = np.random.normal(size=100)
        x2 = x1 + np.random.normal(scale=1e-6, size=100) # Almost perfect
        x3 = np.random.normal(size=100)
        X = np.column_stack([x1, x2, x3])

        vif_scores = calculate_vif(X)

        # First two features should have very high VIF
        assert vif_scores[0] > 10, f"Expected high VIF for correlated feature 0, got {vif_scores[0]}"
        assert vif_scores[1] > 10, f"Expected high VIF for correlated feature 1, got {vif_scores[1]}"
        # Third feature should be low
        assert vif_scores[2] < 2, f"Expected low VIF for independent feature 2, got {vif_scores[2]}"

    def test_vif_single_feature_error(self):
        """VIF should raise error for single feature."""
        X = np.random.normal(size=(100, 1))
        with pytest.raises(ValueError, match="at least 2 features"):
            calculate_vif(X)

    def test_vif_perfect_collinearity(self):
        """VIF should return infinity for perfect collinearity."""
        x1 = np.random.normal(size=100)
        x2 = 2 * x1 + 3 # Perfect linear relationship
        X = np.column_stack([x1, x2])

        vif_scores = calculate_vif(X)
        assert vif_scores[0] == float('inf')
        assert vif_scores[1] == float('inf')


class TestGenerateSyntheticData:
    """Tests for the generate_synthetic_data function."""

    def test_generation_basic(self):
        """Test basic data generation."""
        config = SimulationConfig(
            N=50,
            predictors=3,
            rho=0.5,
            noise_std=1.0,
            true_coefficients=[1.0, 2.0, 3.0]
        )
        instance = generate_synthetic_data(config, seed=42)

        assert instance.X.shape == (50, 3)
        assert instance.y.shape == (50,)
        assert instance.beta_true.shape == (3,)
        assert np.allclose(instance.beta_true, [1.0, 2.0, 3.0])
        assert len(instance.vif_scores) == 3

    def test_generation_random_coefficients(self):
        """Test generation with random coefficients."""
        config = SimulationConfig(
            N=100,
            predictors=5,
            rho=0.0,
            noise_std=0.5
        )
        instance = generate_synthetic_data(config, seed=123)

        assert instance.X.shape == (100, 5)
        assert instance.y.shape == (100,)
        assert instance.beta_true.shape == (5,)
        # Coefficients should be non-zero (randomly generated)
        assert not np.allclose(instance.beta_true, 0)

    def test_generation_seed_reproducibility(self):
        """Test that same seed produces same results."""
        config = SimulationConfig(
            N=30,
            predictors=2,
            rho=0.2,
            noise_std=1.0
        )
        instance1 = generate_synthetic_data(config, seed=999)
        instance2 = generate_synthetic_data(config, seed=999)

        assert np.allclose(instance1.X, instance2.X)
        assert np.allclose(instance1.y, instance2.y)
        assert np.allclose(instance1.beta_true, instance2.beta_true)

    def test_generation_sample_size_check(self):
        """Test that N <= predictors raises error."""
        config = SimulationConfig(
            N=5,
            predictors=10,
            rho=0.0,
            noise_std=1.0
        )
        with pytest.raises(ValueError, match="Sample size N"):
            generate_synthetic_data(config, seed=42)

    def test_generation_vif_scores(self):
        """Test that VIF scores are calculated and reasonable."""
        config = SimulationConfig(
            N=100,
            predictors=3,
            rho=0.8, # High correlation
            noise_std=1.0
        )
        instance = generate_synthetic_data(config, seed=42)

        # With rho=0.8, VIF should be > 1
        # Theoretical VIF for compound symmetry: 1 / (1 - rho)
        expected_vif = 1 / (1 - 0.8)
        for vif in instance.vif_scores.values():
            assert vif > 1.0
            # Allow some variance due to sampling, but should be in the ballpark
            assert vif < expected_vif * 2, f"VIF {vif} seems too high for rho=0.8"


class TestDatasetInstance:
    """Tests for the DatasetInstance dataclass."""

    def test_to_dict_and_from_dict(self):
        """Test serialization and deserialization."""
        config = SimulationConfig(N=20, predictors=2, rho=0.0, noise_std=1.0)
        original = generate_synthetic_data(config, seed=42)
        original.config_params['test_key'] = 'test_value'

        data = original.to_dict()
        restored = DatasetInstance.from_dict(data)

        assert np.allclose(original.X, restored.X)
        assert np.allclose(original.y, restored.y)
        assert np.allclose(original.beta_true, restored.beta_true)
        assert original.vif_scores == restored.vif_scores
        assert original.seed == restored.seed
        assert original.config_params == restored.config_params

    def test_to_dict_numeric_keys(self):
        """Test that integer keys in vif_scores are converted to strings for JSON."""
        config = SimulationConfig(N=20, predictors=2, rho=0.0, noise_std=1.0)
        instance = generate_synthetic_data(config, seed=42)
        data = instance.to_dict()

        # JSON keys must be strings
        for key in data['vif_scores'].keys():
            assert isinstance(key, str)


class TestSaveAndLoadDatasetInstance:
    """Tests for save and load functions."""

    def test_save_and_load_roundtrip(self):
        """Test saving and loading a dataset instance."""
        config = SimulationConfig(N=20, predictors=2, rho=0.0, noise_std=1.0)
        original = generate_synthetic_data(config, seed=42)

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, 'test_instance.json')
            save_dataset_instance(original, filepath)

            # Verify file exists
            assert os.path.exists(filepath)

            # Load and compare
            restored = load_dataset_instance(filepath)

            assert np.allclose(original.X, restored.X)
            assert np.allclose(original.y, restored.y)
            assert np.allclose(original.beta_true, restored.beta_true)

    def test_save_creates_directories(self):
        """Test that save creates parent directories if they don't exist."""
        config = SimulationConfig(N=20, predictors=2, rho=0.0, noise_std=1.0)
        instance = generate_synthetic_data(config, seed=42)

        with tempfile.TemporaryDirectory() as tmpdir:
            nested_path = os.path.join(tmpdir, 'subdir1', 'subdir2', 'test.json')
            save_dataset_instance(instance, nested_path)
            assert os.path.exists(nested_path)