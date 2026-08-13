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
sys.path.insert(0, str(project_root))

from src.validation.linearity_check import (
    load_pairs,
    load_skill_index,
    compute_distances,
    calculate_correlation,
    save_results,
    main
)

class TestLoadPairs:
    def test_load_pairs_success(self, tmp_path):
        pairs_data = [
            {"task_id_1": "A", "task_id_2": "B", "text_embedding_1": [0.1, 0.2], "text_embedding_2": [0.3, 0.4], "weight_vector_1": [1.0, 2.0], "weight_vector_2": [3.0, 4.0]},
            {"task_id_1": "C", "task_id_2": "D", "text_embedding_1": [0.5, 0.6], "text_embedding_2": [0.7, 0.8], "weight_vector_1": [5.0, 6.0], "weight_vector_2": [7.0, 8.0]}
        ]
        pairs_file = tmp_path / "pairs.yaml"
        with open(pairs_file, 'w') as f:
            yaml.dump(pairs_data, f)
        
        result = load_pairs(pairs_file)
        assert len(result) == 2
        assert result[0]['task_id_1'] == "A"

    def test_load_pairs_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_pairs(tmp_path / "non_existent.yaml")

class TestLoadSkillIndex:
    def test_load_skill_index_success(self, tmp_path):
        index_data = {"vectors": np.array([[1.0, 2.0], [3.0, 4.0]])}
        index_file = tmp_path / "index.npz"
        np.savez(index_file, **index_data)
        
        result = load_skill_index(index_file)
        assert result.shape == (2, 2)

    def test_load_skill_index_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_skill_index(tmp_path / "non_existent.npz")

class TestComputeDistances:
    def test_compute_distances(self):
        pairs = [
            {
                "text_embedding_1": np.array([1.0, 0.0]),
                "text_embedding_2": np.array([0.0, 1.0]),
                "weight_vector_1": np.array([1.0, 0.0]),
                "weight_vector_2": np.array([0.0, 1.0])
            }
        ]
        # Dummy index
        skill_index = np.array([[1.0, 0.0], [0.0, 1.0]])
        
        text_dists, weight_dists = compute_distances(pairs, skill_index)
        
        # Cosine distance between [1,0] and [0,1] is 1.0
        assert len(text_dists) == 1
        assert len(weight_dists) == 1
        assert np.isclose(text_dists[0], 1.0)
        assert np.isclose(weight_dists[0], 1.0)

class TestCalculateCorrelation:
    def test_calculate_correlation_perfect(self):
        # Perfect positive correlation
        text_dists = [1.0, 2.0, 3.0]
        weight_dists = [1.0, 2.0, 3.0]
        r, p = calculate_correlation(text_dists, weight_dists)
        assert np.isclose(r, 1.0)
        assert p < 0.05

    def test_calculate_correlation_zero(self):
        # No correlation
        text_dists = [1.0, 2.0, 3.0]
        weight_dists = [3.0, 1.0, 2.0] # Random permutation
        r, p = calculate_correlation(text_dists, weight_dists)
        # Should be close to 0
        assert abs(r) < 0.1

    def test_calculate_correlation_insufficient_data(self):
        with pytest.raises(ValueError):
            calculate_correlation([1.0], [1.0])

class TestSaveResults:
    def test_save_results(self, tmp_path):
        results = {"test": "data", "value": 42}
        output_file = tmp_path / "results.json"
        save_results(results, output_file)
        
        assert output_file.exists()
        with open(output_file, 'r') as f:
            loaded = json.load(f)
        assert loaded["test"] == "data"

class TestMain:
    @patch('src.validation.linearity_check.load_pairs')
    @patch('src.validation.linearity_check.load_skill_index')
    @patch('src.validation.linearity_check.compute_distances')
    @patch('src.validation.linearity_check.calculate_correlation')
    @patch('src.validation.linearity_check.save_results')
    def test_main_success(self, mock_save, mock_calc, mock_compute, mock_load_index, mock_load_pairs, tmp_path):
        # Mock data
        mock_load_pairs.return_value = [
            {"text_embedding_1": [1, 0], "text_embedding_2": [0, 1], "weight_vector_1": [1, 0], "weight_vector_2": [0, 1]}
        ]
        mock_load_index.return_value = np.array([[1, 0], [0, 1]])
        mock_compute.return_value = ([1.0], [1.0])
        mock_calc.return_value = (1.0, 0.01)
        
        # Mock project root
        with patch('src.validation.linearity_check.get_project_root', return_value=tmp_path):
            # Ensure output directory exists
            (tmp_path / "data" / "results").mkdir(parents=True, exist_ok=True)
            (tmp_path / "data" / "processed").mkdir(parents=True, exist_ok=True)
            
            # Create dummy input files
            pairs_file = tmp_path / "data" / "processed" / "known_composites_pairs.yaml"
            with open(pairs_file, 'w') as f:
                yaml.dump([{"test": "data"}], f)
            
            index_file = tmp_path / "data" / "processed" / "skill_index.npz"
            np.savez(index_file, vectors=np.array([[1, 0]]))
            
            main()
            
            mock_load_pairs.assert_called_once()
            mock_compute.assert_called_once()
            mock_calc.assert_called_once()
            mock_save.assert_called_once()