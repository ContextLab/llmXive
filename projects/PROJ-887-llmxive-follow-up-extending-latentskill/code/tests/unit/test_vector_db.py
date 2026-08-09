"""
Unit tests for src/retrieval/vector_db.py
"""
import os
import sys
import tempfile
import numpy as np
import pytest
from pathlib import Path

# Add code/src to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

from retrieval.vector_db import (
    load_flattened_vectors,
    compute_index_structure,
    prepare_for_serialization,
    save_index
)


class TestLoadFlattenedVectors:
    def test_load_flattened_vectors_empty_dir(self, tmp_path):
        """Test that load_flattened_vectors raises FileNotFoundError for empty dir."""
        with pytest.raises(FileNotFoundError):
            load_flattened_vectors(tmp_path)

    def test_load_flattened_vectors_invalid_files(self, tmp_path):
        """Test that load_flattened_vectors skips invalid files."""
        # Create a dummy txt file
        (tmp_path / "dummy.txt").write_text("hello")
        
        with pytest.raises(FileNotFoundError):
            load_flattened_vectors(tmp_path)

    def test_load_flattened_vectors_valid(self, tmp_path):
        """Test loading valid .npz files."""
        # Create a valid .npz file
        vectors = np.random.rand(10, 5).astype(np.float32)
        names = [f"adapter_{i}" for i in range(10)]
        metadata = {"is_proxy": True}
        
        np.savez_compressed(
            tmp_path / "test_weights.npz",
            vectors=vectors,
            names=names,
            metadata=metadata
        )
        
        loaded_vectors, loaded_names, loaded_metadata = load_flattened_vectors(tmp_path)
        
        assert loaded_vectors.shape == (10, 5)
        assert len(loaded_names) == 10
        assert loaded_metadata["total_adapters"] == 10
        assert loaded_metadata["is_proxy"] is True


class TestComputeIndexStructure:
    def test_compute_index_structure_cosine(self):
        """Test compute_index_structure with cosine metric."""
        vectors = np.random.rand(5, 10).astype(np.float32)
        names = [f"adapter_{i}" for i in range(5)]
        
        index_data = compute_index_structure(vectors, names, metric='cosine')
        
        assert index_data['vectors'].shape == (5, 10)
        assert index_data['metric'] == 'cosine'
        assert index_data['count'] == 5
        
        # Verify normalization (norm should be 1)
        norms = np.linalg.norm(index_data['vectors'], axis=1)
        assert np.allclose(norms, 1.0, atol=1e-5)

    def test_compute_index_structure_euclidean(self):
        """Test compute_index_structure with euclidean metric."""
        vectors = np.random.rand(5, 10).astype(np.float32)
        names = [f"adapter_{i}" for i in range(5)]
        
        index_data = compute_index_structure(vectors, names, metric='euclidean')
        
        assert index_data['vectors'].shape == (5, 10)
        assert index_data['metric'] == 'euclidean'
        # Vectors should not be normalized for euclidean
        norms = np.linalg.norm(index_data['vectors'], axis=1)
        assert not np.allclose(norms, 1.0)


class TestPrepareForSerialization:
    def test_prepare_for_serialization(self):
        """Test prepare_for_serialization converts lists to arrays."""
        vectors = np.random.rand(5, 10).astype(np.float64)
        names = [f"adapter_{i}" for i in range(5)]
        
        index_data = {
            'vectors': vectors,
            'adapter_names': names,
            'metric': 'cosine',
            'dimension': 10,
            'count': 5,
            'index_type': 'flat_cpu'
        }
        
        serialized_data = prepare_for_serialization(index_data)
        
        assert isinstance(serialized_data['adapter_names'], np.ndarray)
        assert serialized_data['vectors'].dtype == np.float32


class TestSaveIndex:
    def test_save_index(self, tmp_path):
        """Test save_index creates a valid .npz file."""
        vectors = np.random.rand(5, 10).astype(np.float32)
        names = [f"adapter_{i}" for i in range(5)]
        
        index_data = {
            'vectors': vectors,
            'adapter_names': np.array(names),
            'metric': 'cosine',
            'dimension': 10,
            'count': 5,
            'index_type': 'flat_cpu'
        }
        
        output_path = tmp_path / "skill_index.npz"
        save_index(index_data, output_path)
        
        assert output_path.exists()
        
        # Verify content
        loaded = np.load(output_path)
        assert 'vectors' in loaded
        assert 'adapter_names' in loaded
        assert loaded['vectors'].shape == (5, 10)