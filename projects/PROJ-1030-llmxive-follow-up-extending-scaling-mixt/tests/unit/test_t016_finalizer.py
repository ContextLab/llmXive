"""
Unit tests for T016: extract_features_finalizer.py

Tests verify:
1. Metadata generation logic
2. Feature consolidation logic
3. SHA-256 calculation
4. Error handling for missing data
"""
import os
import sys
import json
import tempfile
from pathlib import Path
import numpy as np
import pytest
from datetime import datetime

# Add project root
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.extract_features_finalizer import (
    calculate_sha256, 
    save_metadata_json, 
    consolidate_and_save_features
)
from code.utils.logging_config import fail_loudly

class TestT016Finalizer:
    
    def test_calculate_sha256(self):
        """Test SHA-256 calculation on a temporary file."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"test data for hashing")
            tmp_path = Path(tmp.name)
        
        try:
            hash_val = calculate_sha256(tmp_path)
            assert len(hash_val) == 64  # SHA-256 hex length
            assert isinstance(hash_val, str)
        finally:
            tmp_path.unlink()

    def test_save_metadata_json(self):
        """Test metadata JSON generation."""
        with tempfile.TemporaryDirectory() as tmp_dir:
          output_dir = Path(tmp_dir)
          features_path = output_dir / "dummy.npy"
          features_path.touch()  # Create dummy file
          
          config = {"test": "value"}
          
          metadata_path = save_metadata_json(output_dir, features_path, config)
          
          assert metadata_path.exists()
          assert metadata_path.name == "features_metadata.json"
          
          with open(metadata_path, "r") as f:
              metadata = json.load(f)
          
          assert "created_at" in metadata
          assert metadata["artifact_type"] == "feature_extraction_batch"
          assert metadata["feature_file"] == "dummy.npy"
          assert "sha256" in metadata["feature_file_sha256"]

    def test_consolidate_and_save_features_valid(self):
        """Test successful consolidation of features."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "features.npy"
            
            # Create dummy data
            latent = np.random.rand(10, 128)
            masks = np.random.randint(0, 2, (10, 32))
            
            features_data = {
                "latent_vectors": latent,
                "expert_masks": masks,
                "clip_ids": [f"clip_{i}" for i in range(10)],
                "chunk_indices": list(range(10))
            }
            
            stats = consolidate_and_save_features(features_data, output_path)
            
            assert output_path.exists()
            assert stats["num_samples"] == 10
            assert stats["latent_dim"] == 128
            assert stats["expert_dim"] == 32
            assert stats["sha256"] is not None
            
            # Verify content
            loaded = np.load(output_path, allow_pickle=True).item()
            assert np.array_equal(loaded["latent_vectors"], latent)
            assert np.array_equal(loaded["expert_masks"], masks)
            assert len(loaded["clip_ids"]) == 10

    def test_consolidate_dimension_mismatch(self):
        """Test that dimension mismatch raises an error."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "features.npy"
            
            latent = np.random.rand(10, 128)
            masks = np.random.randint(0, 2, (5, 32))  # Mismatched N
            
            features_data = {
                "latent_vectors": latent,
                "expert_masks": masks,
                "clip_ids": [],
                "chunk_indices": []
            }
            
            with pytest.raises(Exception) as exc_info:
                consolidate_and_save_features(features_data, output_path)
            
            assert "Dimension mismatch" in str(exc_info.value)

    def test_consolidate_missing_latent(self):
        """Test that missing latent vectors raise an error."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "features.npy"
            
            features_data = {
                "expert_masks": np.random.randint(0, 2, (5, 32)),
                "clip_ids": [],
                "chunk_indices": []
            }
            
            with pytest.raises(Exception) as exc_info:
                consolidate_and_save_features(features_data, output_path)
            
            assert "Missing 'latent_vectors'" in str(exc_info.value)

    def test_consolidate_missing_masks(self):
        """Test that missing expert masks raise an error."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "features.npy"
            
            features_data = {
                "latent_vectors": np.random.rand(5, 128),
                "clip_ids": [],
                "chunk_indices": []
            }
            
            with pytest.raises(Exception) as exc_info:
                consolidate_and_save_features(features_data, output_path)
            
            assert "Missing 'expert_masks'" in str(exc_info.value)