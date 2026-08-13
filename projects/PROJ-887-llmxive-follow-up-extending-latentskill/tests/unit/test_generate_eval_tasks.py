"""
Unit tests for src/validation/generate_eval_tasks.py
"""

import os
import sys
import tempfile
import numpy as np
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path if needed
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.validation.generate_eval_tasks import (
    load_pairs_metadata,
    generate_held_out_pairs,
    synthesize_true_weights,
    save_results
)

class TestGenerateEvalTasks:

    @pytest.fixture
    def mock_index_data(self, tmp_path):
        """Create a mock skill index file for testing."""
        index_path = tmp_path / "skill_index.npz"
        
        # Create mock vectors: 4 skills, dimension 10
        vectors = np.random.rand(4, 10).astype(np.float32)
        # Normalize
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        vectors = vectors / norms
        
        metadata = [
            {"id": "skill_1", "task_desc": "Task 1"},
            {"id": "skill_2", "task_desc": "Task 2"},
            {"id": "skill_3", "task_desc": "Task 3"},
            {"id": "skill_4", "task_desc": "Task 4"}
        ]
        
        np.savez(index_path, vectors=vectors, metadata=metadata)
        return index_path

    def test_load_pairs_metadata(self, mock_index_data):
        """Test loading metadata from the index."""
        metadata = load_pairs_metadata(mock_index_data)
        assert len(metadata) == 4
        assert metadata[0]["id"] == "skill_1"

    def test_load_pairs_metadata_missing_file(self, tmp_path):
        """Test error handling when index file is missing."""
        missing_path = tmp_path / "nonexistent.npz"
        with pytest.raises(FileNotFoundError):
            load_pairs_metadata(missing_path)

    def test_generate_held_out_pairs(self, mock_index_data):
        """Test generation of held-out pairs."""
        metadata = load_pairs_metadata(mock_index_data)
        pairs = generate_held_out_pairs(metadata, seed=42)
        
        assert len(pairs) > 0
        for skill_a, skill_b, alpha in pairs:
            assert "id" in skill_a
            assert "id" in skill_b
            assert 0.2 <= alpha <= 0.8

    def test_generate_held_out_pairs_insufficient_skills(self, tmp_path):
        """Test error handling when less than 2 skills are available."""
        index_path = tmp_path / "small_index.npz"
        vectors = np.random.rand(1, 10)
        metadata = [{"id": "skill_1"}]
        np.savez(index_path, vectors=vectors, metadata=metadata)
        
        metadata_loaded = load_pairs_metadata(index_path)
        with pytest.raises(ValueError):
            generate_held_out_pairs(metadata_loaded)

    def test_synthesize_true_weights(self, mock_index_data):
        """Test synthesis of true weights."""
        pairs = [
            ({"id": "skill_1"}, {"id": "skill_2"}, 0.5),
            ({"id": "skill_3"}, {"id": "skill_4"}, 0.3)
        ]
        
        weights_data = synthesize_true_weights(pairs, mock_index_data, strategy="cosine_weighted")
        
        assert "vectors" in weights_data
        assert "pair_info" in weights_data
        assert weights_data["vectors"].shape[0] == 2
        assert weights_data["vectors"].shape[1] == 10  # Dimension matches index

    def test_synthesize_true_weights_invalid_strategy(self, mock_index_data):
        """Test error handling for invalid strategy."""
        pairs = [({"id": "skill_1"}, {"id": "skill_2"}, 0.5)]
        with pytest.raises(ValueError):
            synthesize_true_weights(pairs, mock_index_data, strategy="invalid_strategy")

    def test_save_results(self, mock_index_data, tmp_path):
        """Test saving results to disk."""
        pairs = [({"id": "skill_1"}, {"id": "skill_2"}, 0.5)]
        weights_data = synthesize_true_weights(pairs, mock_index_data, strategy="cosine_weighted")
        
        output_weights = tmp_path / "weights.npz"
        output_pairs = tmp_path / "pairs.yaml"
        
        save_results(weights_data, pairs, output_weights, output_pairs)
        
        assert output_weights.exists()
        assert output_pairs.exists()
        
        # Verify content
        loaded_weights = np.load(output_weights, allow_pickle=True)
        assert "vectors" in loaded_weights
        assert "pair_info" in loaded_weights

    def test_save_results_creates_directories(self, mock_index_data, tmp_path):
        """Test that save_results creates directories if they don't exist."""
        pairs = [({"id": "skill_1"}, {"id": "skill_2"}, 0.5)]
        weights_data = synthesize_true_weights(pairs, mock_index_data, strategy="cosine_weighted")
        
        deep_path = tmp_path / "deep" / "nested" / "dir"
        output_weights = deep_path / "weights.npz"
        output_pairs = deep_path / "pairs.yaml"
        
        save_results(weights_data, pairs, output_weights, output_pairs)
        
        assert output_weights.exists()
        assert output_pairs.exists()