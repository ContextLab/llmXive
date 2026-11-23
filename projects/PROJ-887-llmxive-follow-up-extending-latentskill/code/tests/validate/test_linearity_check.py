import os
import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import numpy as np
import pytest

# Add code to path if running from root
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.validation.linearity_check import (
    load_pairs, load_skill_index, get_vector_from_index, 
    compute_distances, calculate_correlation, save_results
)

class TestLoadPairs:
    def test_load_pairs_valid_yaml(self, tmp_path):
        data = [
            {"composite_desc": "task A and B", "base_skill_ids": ["id1", "id2"]},
            {"composite_desc": "task C and D", "base_skill_ids": ["id3", "id4"]}
        ]
        file_path = tmp_path / "pairs.yaml"
        import yaml
        with open(file_path, 'w') as f:
            yaml.dump(data, f)
        
        result = load_pairs(file_path)
        assert len(result) == 2
        assert result[0]['base_skill_ids'] == ["id1", "id2"]

    def test_load_pairs_missing_file(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_pairs(tmp_path / "nonexistent.yaml")

class TestLoadSkillIndex:
    def test_load_skill_index_valid(self, tmp_path):
        vectors = np.random.rand(10, 128).astype(np.float32)
        metadata = {"ids": [f"id{i}" for i in range(10)]}
        
        file_path = tmp_path / "index.npz"
        np.savez(file_path, vectors=vectors, metadata=metadata)
        
        v, m = load_skill_index(file_path)
        assert v.shape == (10, 128)
        assert m['ids'] == [f"id{i}" for i in range(10)]

class TestGetVectorFromIndex:
    def test_get_vector_success(self):
        vectors = np.random.rand(5, 10).astype(np.float32)
        metadata = {"ids": ["a", "b", "c", "d", "e"]}
        
        vec = get_vector_from_index("c", vectors, metadata)
        assert np.array_equal(vec, vectors[2])

    def test_get_vector_key_error(self):
        vectors = np.random.rand(5, 10).astype(np.float32)
        metadata = {"ids": ["a", "b"]}
        
        with pytest.raises(StopIteration): # next() raises StopIteration if not found
            get_vector_from_index("z", vectors, metadata)

class TestComputeDistances:
    @patch('src.validation.linearity_check.SentenceTransformer')
    def test_compute_distances(self, mock_model_class, tmp_path):
        # Setup mock model
        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([[1.0, 0.0], [0.0, 1.0]]) # Orthogonal
        mock_model_class.return_value = mock_model

        pairs = [
            {"composite_desc": "test", "base_skill_ids": ["id1", "id2"]}
        ]
        
        # Vectors: id1 at index 0, id2 at index 1
        vectors = np.array([
            [1.0, 0.0, 0.0], # id1
            [0.0, 1.0, 0.0], # id2
        ], dtype=np.float32)
        
        metadata = {
            "ids": ["id1", "id2"],
            "task_descs": {
                "id1": "desc1",
                "id2": "desc2"
            }
        }
        
        text_dists, weight_dists = compute_distances(pairs, vectors, metadata)
        
        # Weight distance: (1,0,0) vs (0,1,0) -> cos_sim = 0 -> dist = 1
        assert len(weight_dists) == 1
        assert np.isclose(weight_dists[0], 1.0)
        
        # Text distance: mock returns orthogonal -> dist = 1
        assert len(text_dists) == 1
        assert np.isclose(text_dists[0], 1.0)

class TestCalculateCorrelation:
    def test_perfect_positive(self):
        x = [1, 2, 3, 4, 5]
        y = [2, 4, 6, 8, 10]
        r = calculate_correlation(x, y)
        assert np.isclose(r, 1.0)

    def test_perfect_negative(self):
        x = [1, 2, 3, 4, 5]
        y = [5, 4, 3, 2, 1]
        r = calculate_correlation(x, y)
        assert np.isclose(r, -1.0)

    def test_insufficient_data(self):
        r = calculate_correlation([1], [2])
        assert np.isnan(r)

class TestSaveResults:
    def test_save_results(self, tmp_path):
        output_path = tmp_path / "result.json"
        save_results(0.85, output_path)
        
        assert output_path.exists()
        with open(output_path, 'r') as f:
            data = json.load(f)
        assert data['linearity_correlation_coefficient'] == 0.85
