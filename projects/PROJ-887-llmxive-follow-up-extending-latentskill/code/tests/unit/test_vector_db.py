import os
import sys
import tempfile
import numpy as np
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.retrieval.vector_db import load_flattened_vectors, compute_index_structure, prepare_for_serialization, save_index

class TestLoadFlattenedVectors:
    def test_load_flattened_vectors_success(self, tmp_path):
        # Create mock raw data
        raw_dir = tmp_path / "raw"
        raw_dir.mkdir()
        
        # Create mock npz files
        alfworld_data = {"layer1": np.random.rand(10, 10).astype(np.float32)}
        searchqa_data = {"layer2": np.random.rand(10, 10).astype(np.float32)}
        
        np.savez(raw_dir / "alfworld_weights.npz", **alfworld_data)
        np.savez(raw_dir / "searchqa_weights.npz", **searchqa_data)
        
        vectors, metadata = load_flattened_vectors(raw_dir)
        
        assert vectors.shape[0] == 2
        assert vectors.shape[1] == 100  # 10*10 flattened
        assert len(metadata) == 2
        assert metadata[0]["source"] == "alfworld"
        assert metadata[1]["source"] == "searchqa"

    def test_load_flattened_vectors_missing_file(self, tmp_path):
        raw_dir = tmp_path / "raw"
        raw_dir.mkdir()
        
        # Only create one file
        np.savez(raw_dir / "alfworld_weights.npz", layer1=np.random.rand(10, 10))
        
        with pytest.raises(FileNotFoundError):
            load_flattened_vectors(raw_dir)

class TestComputeIndexStructure:
    def test_compute_index_structure(self):
        vectors = np.random.rand(5, 100)
        metadata = [{"source": "test", "layer": "l1", "dim": 100} for _ in range(5)]
        
        structure = compute_index_structure(vectors, metadata)
        
        assert structure["num_vectors"] == 5
        assert structure["vector_dim"] == 100
        assert "test" in structure["sources"]
        assert "checksum" in structure

class TestPrepareForSerialization:
    def test_prepare_for_serialization(self):
        vectors = np.random.rand(3, 50)
        metadata = [{"source": "a"}, {"source": "b"}, {"source": "c"}]
        
        vectors_out, meta_dict = prepare_for_serialization(vectors, metadata)
        
        assert vectors_out.shape == vectors.shape
        assert "num_vectors" in meta_dict["structure"]

class TestSaveIndex:
    def test_save_index(self, tmp_path):
        output_path = tmp_path / "skill_index.npz"
        vectors = np.random.rand(2, 10)
        meta = {"num_vectors": 2, "vector_dim": 10, "sources": ["a"], "checksum": "abc"}
        
        save_index(vectors, meta, output_path)
        
        assert output_path.exists()
        
        # Verify content
        data = np.load(output_path, allow_pickle=True)
        assert "vectors" in data.files
        assert "metadata" in data.files