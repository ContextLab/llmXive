"""
Unit tests for T025: Save processed feature matrix.

Tests verify that:
1. Embeddings are loaded correctly from embeddings.npy
2. Feature matrix is loaded/extracted correctly
3. Merging works with participant_id
4. Output CSV is saved with correct structure
5. Metadata is saved alongside the CSV
"""
import os
import tempfile
import json
from pathlib import Path

import pytest
import pandas as pd
import numpy as np

from save_features import (
    load_embeddings,
    load_feature_matrix,
    merge_features_with_metadata,
    save_feature_matrix,
    main
)
from config import get_path, ensure_dirs


class TestLoadEmbeddings:
    """Tests for load_embeddings function."""

    def test_load_embeddings_success(self, tmp_path):
        """Test loading embeddings from a valid .npy file."""
        # Create test embeddings
        n_samples = 10
        n_features = 384
        embeddings = np.random.rand(n_samples, n_features).astype(np.float32)
        
        embeddings_path = tmp_path / "embeddings.npy"
        np.save(embeddings_path, embeddings)
        
        # Load embeddings
        df = load_embeddings(str(embeddings_path))
        
        # Verify structure
        assert isinstance(df, pd.DataFrame)
        assert df.shape == (n_samples, n_features)
        assert "participant_id" not in df.columns  # participant_id added later
        
        # Verify column names
        expected_cols = [f"embedding_{i}" for i in range(n_features)]
        assert list(df.columns) == expected_cols

    def test_load_embeddings_missing_file(self):
        """Test that missing embeddings file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_embeddings("/nonexistent/path/embeddings.npy")

    def test_load_embeddings_invalid_shape(self, tmp_path):
        """Test that 1D embeddings raise ValueError."""
        embeddings = np.random.rand(10).astype(np.float32)
        embeddings_path = tmp_path / "embeddings_1d.npy"
        np.save(embeddings_path, embeddings)
        
        with pytest.raises(ValueError):
            load_embeddings(str(embeddings_path))


class TestMergeFeaturesWithMetadata:
    """Tests for merge_features_with_metadata function."""

    def test_merge_success(self):
        """Test successful merge of features and embeddings."""
        # Create test data
        features_df = pd.DataFrame({
            "participant_id": [f"P{i}" for i in range(5)],
            "ttr": np.random.rand(5),
            "mtld": np.random.rand(5)
        })
        
        embeddings_df = pd.DataFrame({
            "participant_id": [f"P{i}" for i in range(5)],
            "embedding_0": np.random.rand(5),
            "embedding_1": np.random.rand(5)
        })
        
        # Merge
        combined = merge_features_with_metadata(features_df, embeddings_df)
        
        # Verify
        assert combined.shape[0] == 5
        assert "participant_id" in combined.columns
        assert "ttr" in combined.columns
        assert "embedding_0" in combined.columns

    def test_merge_missing_participant_id_features(self):
        """Test error when features_df missing participant_id."""
        features_df = pd.DataFrame({
            "ttr": np.random.rand(5)
        })
        
        embeddings_df = pd.DataFrame({
            "participant_id": [f"P{i}" for i in range(5)],
            "embedding_0": np.random.rand(5)
        })
        
        with pytest.raises(ValueError, match="Feature DataFrame must contain"):
            merge_features_with_metadata(features_df, embeddings_df)

    def test_merge_missing_participant_id_embeddings(self):
        """Test error when embeddings_df missing participant_id."""
        features_df = pd.DataFrame({
            "participant_id": [f"P{i}" for i in range(5)],
            "ttr": np.random.rand(5)
        })
        
        embeddings_df = pd.DataFrame({
            "embedding_0": np.random.rand(5)
        })
        
        with pytest.raises(ValueError, match="Embeddings DataFrame must contain"):
            merge_features_with_metadata(features_df, embeddings_df)


class TestSaveFeatureMatrix:
    """Tests for save_feature_matrix function."""

    def test_save_with_metadata(self, tmp_path):
        """Test saving CSV with metadata."""
        # Create test data
        df = pd.DataFrame({
            "participant_id": [f"P{i}" for i in range(3)],
            "ttr": np.random.rand(3),
            "embedding_0": np.random.rand(3)
        })
        
        metadata = {
            "total_features": 3,
            "total_participants": 3,
            "test": "value"
        }
        
        output_path = str(tmp_path / "features.csv")
        
        # Save
        saved_path = save_feature_matrix(df, output_path, metadata)
        
        # Verify CSV
        assert os.path.exists(saved_path)
        saved_df = pd.read_csv(saved_path)
        assert saved_df.shape == df.shape
        
        # Verify metadata
        metadata_path = saved_path.replace(".csv", "_metadata.json")
        assert os.path.exists(metadata_path)
        with open(metadata_path) as f:
            saved_metadata = json.load(f)
        assert saved_metadata["test"] == "value"

    def test_save_creates_directories(self, tmp_path):
        """Test that save creates necessary directories."""
        df = pd.DataFrame({
            "participant_id": ["P1"],
            "ttr": [0.5]
        })
        
        output_path = str(tmp_path / "subdir" / "features.csv")
        save_feature_matrix(df, output_path)
        
        assert os.path.exists(output_path)


class TestIntegration:
    """Integration tests for the full save_features pipeline."""

    def test_full_pipeline(self, tmp_path):
        """Test the full feature saving pipeline."""
        # Create mock embeddings
        n_samples = 5
        n_features = 10  # Reduced for test speed
        embeddings = np.random.rand(n_samples, n_features).astype(np.float32)
        
        embeddings_path = tmp_path / "embeddings.npy"
        np.save(embeddings_path, embeddings)
        
        # Create mock features
        features_df = pd.DataFrame({
            "participant_id": [f"P{i}" for i in range(n_samples)],
            "ttr": np.random.rand(n_samples),
            "mtld": np.random.rand(n_samples),
            "mean_clause_length": np.random.rand(n_samples),
            "t_unit_count": np.random.rand(n_samples)
        })
        
        # Save features to temp location
        features_temp_path = tmp_path / "features_temp.csv"
        features_df.to_csv(features_temp_path, index=False)
        
        # Mock the get_path function to use tmp_path
        import save_features
        original_get_path = save_features.get_path
        
        def mock_get_path(key, filename=None):
            if key == "data_processed":
                return tmp_path
            return tmp_path
        
        save_features.get_path = mock_get_path
        
        try:
            # Run the main function
            output_path = save_features.main()
            
            # Verify output
            assert os.path.exists(output_path)
            saved_df = pd.read_csv(output_path)
            
            # Verify structure
            assert len(saved_df) == n_samples
            assert "participant_id" in saved_df.columns
            assert "ttr" in saved_df.columns
            assert "embedding_0" in saved_df.columns
            
        finally:
            save_features.get_path = original_get_path
