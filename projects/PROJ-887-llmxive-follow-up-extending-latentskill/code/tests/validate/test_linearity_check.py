"""
Unit tests for src/validation/linearity_check.py
"""
import os
import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import numpy as np
import yaml

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.validation.linearity_check import (
    load_pairs,
    load_skill_index,
    get_vector_from_index,
    compute_distances,
    calculate_correlation,
    save_results,
    LINEARITY_THRESHOLD
)

class TestLoadPairs:
    def test_load_valid_pairs(self, tmp_path):
        pairs_data = [
            {"task_a_id": "t1", "task_b_id": "t2", "text_distance": 0.5},
            {"task_a_id": "t3", "task_b_id": "t4", "text_distance": 0.8}
        ]
        pairs_file = tmp_path / "pairs.yaml"
        with open(pairs_file, 'w') as f:
            yaml.dump(pairs_data, f)
        
        result = load_pairs(pairs_file)
        assert len(result) == 2
        assert result[0]['task_a_id'] == 't1'

    def test_load_missing_file(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_pairs(tmp_path / "nonexistent.yaml")

    def test_load_invalid_format(self, tmp_path):
        pairs_file = tmp_path / "pairs.yaml"
        with open(pairs_file, 'w') as f:
            f.write("not a list")
        
        with pytest.raises(ValueError):
            load_pairs(pairs_file)

class TestLoadSkillIndex:
    def test_load_index(self, tmp_path):
        index_file = tmp_path / "index.npz"
        # Create dummy vectors
        np.savez(index_file, t1_vector=np.array([1.0, 2.0]), t2_vector=np.array([3.0, 4.0]))
        
        result = load_skill_index(index_file)
        assert 't1_vector' in result
        assert np.array_equal(result['t1_vector'], np.array([1.0, 2.0]))

    def test_load_missing_file(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_skill_index(tmp_path / "missing.npz")

class TestGetVectorFromIndex:
    def test_exact_match(self):
        vectors = {"task_1": np.array([1, 2, 3])}
        result = get_vector_from_index(vectors, "task_1")
        assert np.array_equal(result, np.array([1, 2, 3]))

    def test_suffix_match(self):
        vectors = {"task_1_vector": np.array([1, 2, 3])}
        result = get_vector_from_index(vectors, "task_1")
        assert np.array_equal(result, np.array([1, 2, 3]))

    def test_missing_vector(self):
        vectors = {"other": np.array([1, 2, 3])}
        with pytest.raises(KeyError):
            get_vector_from_index(vectors, "missing_task")

class TestComputeDistances:
    def test_compute_distances_valid(self):
        pairs = [
            {"task_a_id": "t1", "task_b_id": "t2", "text_distance": 0.5}
        ]
        vectors = {
            "t1": np.array([1.0, 0.0]), # Normalized
            "t2": np.array([0.0, 1.0])  # Normalized, 90 degrees -> dist 1.0
        }
        
        text_d, weight_d = compute_distances(pairs, vectors)
        
        assert len(text_d) == 1
        assert len(weight_d) == 1
        assert np.isclose(weight_d[0], 1.0) # Cosine dist of orthogonal vectors
        assert text_d[0] == 0.5

    def test_compute_distances_mismatched_dims(self, caplog):
        pairs = [
            {"task_a_id": "t1", "task_b_id": "t2", "text_distance": 0.5}
        ]
        vectors = {
            "t1": np.array([1.0, 0.0]),
            "t2": np.array([0.0, 1.0, 0.0]) # Different dim
        }
        
        text_d, weight_d = compute_distances(pairs, vectors)
        
        assert len(text_d) == 0
        assert len(weight_d) == 0

class TestCalculateCorrelation:
    def test_perfect_correlation(self):
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 6, 8, 10])
        corr = calculate_correlation(x, y)
        assert np.isclose(corr, 1.0)

    def test_no_correlation(self):
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([5, 3, 1, 4, 2])
        # Not perfectly random, but low correlation
        corr = calculate_correlation(x, y)
        # Just check it returns a float
        assert isinstance(corr, float)
        assert -1.0 <= corr <= 1.0

    def test_insufficient_data(self):
        x = np.array([1])
        y = np.array([1])
        corr = calculate_correlation(x, y)
        assert corr == 0.0

class TestSaveResults:
    def test_save_results(self, tmp_path):
        output_file = tmp_path / "results.json"
        save_results(0.75, True, 10, output_file)
        
        assert output_file.exists()
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        assert data['correlation'] == 0.75
        assert data['validity_flag'] == True
        assert data['threshold'] == LINEARITY_THRESHOLD
        assert data['num_pairs'] == 10
