"""
Integration tests for the ingestion pipeline.
Verifies that the full pipeline from raw weights to skill index generation
runs successfully on CPU without requiring GPU resources.
"""
import os
import sys
import tempfile
import shutil
import json
from pathlib import Path

import pytest
import numpy as np

# Add project root to path if not already present
PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.config import get_project_root, get_data_path, ensure_directories, set_seed
from src.ingestion.download_weights import process_dataset, save_weights
from src.ingestion.flatten_lora import flatten_and_normalize, validate_dimensions
from src.retrieval.vector_db import load_flattened_vectors, compute_index_structure, prepare_for_serialization, save_index


class TestIngestionPipeline:
    """Integration tests for the skill vector ingestion pipeline."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup test environment and cleanup after tests."""
        # Setup
        set_seed(42)
        self.project_root = get_project_root()
        self.data_path = get_data_path()
        
        # Create temporary directories for test artifacts
        self.test_dir = tempfile.mkdtemp(prefix="llmxive_test_")
        self.test_data_path = Path(self.test_dir) / "data"
        self.test_data_raw = self.test_data_path / "raw"
        self.test_data_processed = self.test_data_path / "processed"
        
        self.test_data_raw.mkdir(parents=True, exist_ok=True)
        self.test_data_processed.mkdir(parents=True, exist_ok=True)
        
        # Store original paths to restore later
        self._original_data_path = self.data_path
        
        # Mock config to use test paths
        # We'll pass paths explicitly to functions instead of relying on global config
        
        yield
        
        # Teardown
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_full_ingestion_pipeline_cpu(self):
        """
        Test the complete ingestion pipeline on CPU:
        1. Generate synthetic proxy weights (simulating T012)
        2. Flatten and normalize weights (T013)
        3. Build vector database index (T014c, T014d)
        4. Verify output file exists and contains valid data
        
        This test verifies the pipeline works end-to-end without GPU.
        """
        # Step 1: Generate synthetic proxy weights (simulating T012 output)
        # We create minimal synthetic weights to test the pipeline
        num_skills = 3
        in_features = 4096
        out_features = 1024
        
        synthetic_weights_path = self.test_data_raw / "test_weights.npz"
        
        # Create synthetic A and B matrices for multiple skills
        np.savez(
            str(synthetic_weights_path),
            skill_1_A=np.random.randn(in_features, out_features).astype(np.float32),
            skill_1_B=np.random.randn(out_features, in_features).astype(np.float32),
            skill_2_A=np.random.randn(in_features, out_features).astype(np.float32),
            skill_2_B=np.random.randn(out_features, in_features).astype(np.float32),
            skill_3_A=np.random.randn(in_features, out_features).astype(np.float32),
            skill_3_B=np.random.randn(out_features, in_features).astype(np.float32),
        )
        
        assert synthetic_weights_path.exists(), "Synthetic weights file not created"
        
        # Step 2: Flatten and normalize weights (T013 logic)
        flattened_vectors, metadata = flatten_and_normalize(
            str(synthetic_weights_path),
            data_dir=self.test_data_raw
        )
        
        # Verify flattening results
        assert len(flattened_vectors) == num_skills, f"Expected {num_skills} vectors, got {len(flattened_vectors)}"
        assert metadata is not None, "Metadata should not be None"
        assert "skill_ids" in metadata, "Metadata should contain skill_ids"
        assert len(metadata["skill_ids"]) == num_skills, "Metadata skill_ids count mismatch"
        
        # Verify dimensions
        expected_dim = in_features * out_features * 2  # A and B matrices
        for vec in flattened_vectors:
            assert vec.shape[0] == expected_dim, f"Vector dimension mismatch: expected {expected_dim}, got {vec.shape[0]}"
            # Verify L2 normalization
            norm = np.linalg.norm(vec)
            assert np.isclose(norm, 1.0, atol=1e-5), f"Vector not normalized: norm={norm}"
        
        # Step 3: Validate dimensions consistency (T015 logic)
        is_valid, error_msg = validate_dimensions(flattened_vectors)
        assert is_valid, f"Dimension validation failed: {error_msg}"
        
        # Step 4: Build vector database index (T014c, T014d logic)
        index_data = compute_index_structure(flattened_vectors, metadata)
        
        assert "vectors" in index_data, "Index data missing 'vectors' key"
        assert "metadata" in index_data, "Index data missing 'metadata' key"
        assert "checksum" in index_data, "Index data missing 'checksum' key"
        
        # Verify index structure
        assert index_data["vectors"].shape[0] == num_skills
        assert index_data["vectors"].shape[1] == expected_dim
        
        # Step 5: Serialize and save index (T014d)
        output_path = self.test_data_processed / "test_skill_index.npz"
        save_index(index_data, str(output_path))
        
        # Step 6: Verify output file exists and contains valid data
        assert output_path.exists(), f"Output index file not created at {output_path}"
        
        # Load and verify saved index
        loaded_index = np.load(str(output_path), allow_pickle=True)
        
        # Check required keys
        assert "vectors" in loaded_index.files, "Saved index missing 'vectors' array"
        assert "metadata" in loaded_index.files, "Saved index missing 'metadata' array"
        
        # Verify data integrity
        loaded_vectors = loaded_index["vectors"]
        assert loaded_vectors.shape[0] == num_skills, "Loaded vector count mismatch"
        assert loaded_vectors.shape[1] == expected_dim, "Loaded vector dimension mismatch"
        
        # Verify metadata
        loaded_metadata = loaded_index["metadata"].item()
        assert "skill_ids" in loaded_metadata, "Loaded metadata missing 'skill_ids'"
        assert len(loaded_metadata["skill_ids"]) == num_skills, "Loaded metadata skill count mismatch"
        
        # Verify checksum was computed
        assert "checksum" in loaded_metadata, "Loaded metadata missing 'checksum'"
        
        print(f"✓ Full ingestion pipeline completed successfully")
        print(f"  - Generated {num_skills} skill vectors")
        print(f"  - Vector dimension: {expected_dim}")
        print(f"  - Output file: {output_path}")
        print(f"  - File size: {output_path.stat().st_size} bytes")

    def test_pipeline_with_empty_weights(self):
        """Test pipeline behavior with empty or malformed weight files."""
        # Create an empty weights file
        empty_weights_path = self.test_data_raw / "empty_weights.npz"
        np.savez(str(empty_weights_path))
        
        # Verify the pipeline handles this gracefully
        # The flatten_and_normalize function should raise an error or handle empty data
        with pytest.raises((ValueError, KeyError, IndexError)):
            flatten_and_normalize(str(empty_weights_path), data_dir=self.test_data_raw)

    def test_pipeline_dimension_mismatch(self):
        """Test pipeline behavior when dimensions are inconsistent."""
        # Create weights with mismatched dimensions
        mismatched_path = self.test_data_raw / "mismatched_weights.npz"
        np.savez(
            str(mismatched_path),
            skill_1_A=np.random.randn(4096, 1024).astype(np.float32),
            skill_1_B=np.random.randn(1024, 4096).astype(np.float32),
            skill_2_A=np.random.randn(2048, 512).astype(np.float32),  # Different dimensions
            skill_2_B=np.random.randn(512, 2048).astype(np.float32),
        )
        
        flattened_vectors, _ = flatten_and_normalize(str(mismatched_path), data_dir=self.test_data_raw)
        
        # Dimension validation should catch this
        is_valid, error_msg = validate_dimensions(flattened_vectors)
        assert not is_valid, "Should detect dimension mismatch"
        assert "inconsistent" in error_msg.lower() or "dimension" in error_msg.lower()


if __name__ == "__main__":
    # Allow running the test directly
    pytest.main([__file__, "-v"])