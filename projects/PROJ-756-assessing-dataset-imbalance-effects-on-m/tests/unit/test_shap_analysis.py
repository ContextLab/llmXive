import os
import sys
import json
import tempfile
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from shap_analysis import (
    load_descriptor_schema,
    generate_physics_inspired_weights,
    generate_synthetic_target,
    generate_synthetic_dataset,
    validate_weights,
    RANDOM_SEED,
    N_SAMPLES
)


class TestLoadDescriptorSchema:
    """Test loading of descriptor schema from T007b."""

    def test_load_existing_schema(self, tmp_path):
        """Test loading a valid schema file."""
        schema_path = tmp_path / "test_schema.json"
        test_schema = {
            "columns": ["feature_0", "feature_1", "feature_2"],
            "count": 3
        }
        
        with open(schema_path, 'w') as f:
            json.dump(test_schema, f)
        
        loaded_schema = load_descriptor_schema(schema_path)
        
        assert loaded_schema == test_schema
        assert "columns" in loaded_schema
        assert len(loaded_schema["columns"]) == 3

    def test_missing_schema_file(self, tmp_path):
        """Test that FileNotFoundError is raised for missing schema."""
        schema_path = tmp_path / "nonexistent.json"
        
        with pytest.raises(FileNotFoundError):
            load_descriptor_schema(schema_path)

    def test_schema_count_mismatch(self, tmp_path):
        """Test handling of schema count mismatch."""
        schema_path = tmp_path / "mismatch_schema.json"
        test_schema = {
            "columns": ["feature_0", "feature_1"],
            "count": 5  # Mismatch
        }
        
        with open(schema_path, 'w') as f:
            json.dump(test_schema, f)
        
        # This should not raise in load_descriptor_schema itself,
        # but generate_synthetic_dataset will validate later
        schema = load_descriptor_schema(schema_path)
        assert schema["count"] == 5
        assert len(schema["columns"]) == 2


class TestGeneratePhysicsInspiredWeights:
    """Test physics-inspired weight generation."""

    def test_weight_generation(self):
        """Test that weights are generated correctly."""
        feature_names = [f"feature_{i}" for i in range(20)]
        n_features = 20
        
        weights = generate_physics_inspired_weights(feature_names, n_features)
        
        assert len(weights) == n_features
        assert isinstance(weights, np.ndarray)
        
        # Check L2 normalization
        norm = np.linalg.norm(weights)
        assert np.isclose(norm, 1.0, atol=1e-6)

    def test_weight_range(self):
        """Test that weights are within reasonable range."""
        feature_names = [f"feature_{i}" for i in range(30)]
        n_features = 30
        
        weights = generate_physics_inspired_weights(feature_names, n_features)
        
        # Weights should be normalized, so max should be <= 1
        assert np.max(np.abs(weights)) <= 1.1  # Small tolerance for floating point
        assert np.min(weights) >= -1.1

    def test_deterministic_with_seed(self):
        """Test that weights are deterministic with fixed seed."""
        feature_names = [f"feature_{i}" for i in range(10)]
        n_features = 10
        
        weights1 = generate_physics_inspired_weights(feature_names, n_features)
        weights2 = generate_physics_inspired_weights(feature_names, n_features)
        
        np.testing.assert_array_equal(weights1, weights2)

    def test_feature_count_validation(self):
        """Test that weight count matches feature count."""
        for n_features in [5, 10, 20, 50]:
            feature_names = [f"feature_{i}" for i in range(n_features)]
            weights = generate_physics_inspired_weights(feature_names, n_features)
            assert len(weights) == n_features


class TestGenerateSyntheticTarget:
    """Test synthetic target generation with non-linear formula."""

    def test_target_generation(self):
        """Test that targets are generated correctly."""
        np.random.seed(RANDOM_SEED)
        n_samples = 100
        n_features = 10
        
        X = np.random.randn(n_samples, n_features)
        weights = np.random.randn(n_features)
        weights = weights / np.linalg.norm(weights)  # Normalize
        
        target = generate_synthetic_target(X, weights)
        
        assert target.shape == (n_samples,)
        assert not np.all(target == 0)

    def test_non_linear_components(self):
        """Test that non-linear components are included."""
        np.random.seed(RANDOM_SEED)
        n_samples = 50
        n_features = 5
        
        X = np.random.randn(n_samples, n_features)
        weights = np.ones(n_features) / np.sqrt(n_features)
        
        target = generate_synthetic_target(X, weights)
        
        # Target should not be purely linear (variance should be higher than linear term alone)
        linear_only = X @ weights
        assert not np.allclose(target, linear_only)

    def test_noise_addition(self):
        """Test that noise is added to targets."""
        np.random.seed(RANDOM_SEED)
        n_samples = 100
        n_features = 10
        
        X = np.random.randn(n_samples, n_features)
        weights = np.random.randn(n_features)
        weights = weights / np.linalg.norm(weights)
        
        target = generate_synthetic_target(X, weights)
        
        # Target should have some variance
        assert target.std() > 0


class TestGenerateSyntheticDataset:
    """Test full synthetic dataset generation."""

    def test_dataset_generation(self, tmp_path):
        """Test complete dataset generation."""
        # Create a temporary schema
        schema = {
            "columns": [f"feature_{i}" for i in range(15)],
            "count": 15
        }
        
        df = generate_synthetic_dataset(schema)
        
        # Check shape
        assert df.shape[0] == N_SAMPLES
        assert df.shape[1] == 15 + 2 + 15 + 2  # features + target + known_weights + metadata
        
        # Check columns
        expected_cols = schema["columns"] + ["target", "known_weights", "is_synthetic", "generation_seed"]
        expected_cols += [f"weight_{i}" for i in range(15)]
        
        for col in expected_cols:
            assert col in df.columns

    def test_target_column_exists(self, tmp_path):
        """Test that target column is present."""
        schema = {
            "columns": ["f1", "f2", "f3"],
            "count": 3
        }
        
        df = generate_synthetic_dataset(schema)
        
        assert "target" in df.columns
        assert not df["target"].isna().any()

    def test_metadata_columns(self, tmp_path):
        """Test that metadata columns are present."""
        schema = {
            "columns": ["f1", "f2"],
            "count": 2
        }
        
        df = generate_synthetic_dataset(schema)
        
        assert "is_synthetic" in df.columns
        assert "generation_seed" in df.columns
        assert all(df["is_synthetic"] == True)
        assert all(df["generation_seed"] == RANDOM_SEED)


class TestValidateWeights:
    """Test weight validation logic."""

    def test_valid_weights(self):
        """Test validation with correct weight count."""
        n_features = 10
        feature_names = [f"feature_{i}" for i in range(n_features)]
        
        # Create a mock DataFrame with correct weights
        df = pd.DataFrame({
            "target": np.random.randn(100),
            **{f"weight_{i}": np.random.randn(100) for i in range(n_features)}
        })
        
        assert validate_weights(df, feature_names) is True

    def test_invalid_weight_count(self):
        """Test validation with incorrect weight count."""
        n_features = 10
        feature_names = [f"feature_{i}" for i in range(n_features)]
        
        # Create a mock DataFrame with wrong weight count
        df = pd.DataFrame({
            "target": np.random.randn(100),
            **{f"weight_{i}": np.random.randn(100) for i in range(5)}  # Only 5 weights
        })
        
        with pytest.raises(ValueError, match="Weight count mismatch"):
            validate_weights(df, feature_names)


class TestIntegration:
    """Integration tests for the full pipeline."""

    def test_full_generation_pipeline(self, tmp_path):
        """Test the complete synthetic data generation pipeline."""
        # Create schema
        schema = {
            "columns": [f"magpie_feature_{i}" for i in range(20)],
            "count": 20
        }
        
        # Generate dataset
        df = generate_synthetic_dataset(schema)
        
        # Validate
        feature_names = schema["columns"]
        validate_weights(df, feature_names)
        
        # Check that we can extract known weights
        weight_cols = [col for col in df.columns if col.startswith("weight_")]
        assert len(weight_cols) == 20
        
        # Extract first sample's weights
        first_weights = df[weight_cols].iloc[0].values
        assert len(first_weights) == 20
        assert np.isclose(np.linalg.norm(first_weights), 1.0, atol=1e-5)

    def test_reproducibility(self, tmp_path):
        """Test that multiple runs produce the same results."""
        schema = {
            "columns": [f"feature_{i}" for i in range(10)],
            "count": 10
        }
        
        df1 = generate_synthetic_dataset(schema)
        df2 = generate_synthetic_dataset(schema)
        
        pd.testing.assert_frame_equal(df1, df2)