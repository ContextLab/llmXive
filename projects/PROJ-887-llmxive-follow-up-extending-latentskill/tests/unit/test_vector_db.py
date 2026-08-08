"""
Unit tests for src.retrieval.vector_db module.

Tests:
- build_skill_index creates the correct file structure.
- build_skill_index handles empty input gracefully (raises error).
- build_skill_index validates dimensions.
"""

import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import numpy as np

# Import the function to test
from src.retrieval.vector_db import build_skill_index


def test_build_index_success():
    """Test successful construction of the index."""
    # Mock data
    mock_vectors = [
        np.array([1.0, 2.0, 3.0]),
        np.array([4.0, 5.0, 6.0]),
        np.array([7.0, 8.0, 9.0])
    ]
    mock_names = ["skill_a", "skill_b", "skill_c"]
    mock_metadata = {"source": "test_data"}

    mock_data = {
        "vectors": mock_vectors,
        "names": mock_names,
        "metadata": mock_metadata
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = os.path.join(tmpdir, "test_index.npz")
        meta_file = os.path.join(tmpdir, "test_meta.json")

        with patch('src.retrieval.vector_db.load_flattened_vectors', return_value=mock_data):
            metrics = build_skill_index(
                output_dir=tmpdir,
                output_filename="test_index.npz",
                metadata_filename="test_meta.json"
            )

        # Assertions
        assert os.path.exists(output_file), "Index file not created"
        assert os.path.exists(meta_file), "Metadata file not created"

        # Verify content
        loaded = np.load(output_file)
        assert 'vectors' in loaded.files
        assert loaded['vectors'].shape == (3, 3)
        assert np.allclose(loaded['vectors'][0], mock_vectors[0])

        with open(meta_file, 'r') as f:
            saved_meta = json.load(f)
        
        assert saved_meta['num_skills'] == 3
        assert saved_meta['dimension'] == 3
        assert saved_meta['skill_names'] == mock_names
        assert saved_meta['construction_time_sec'] > 0


def test_build_index_dimension_mismatch():
    """Test that dimension mismatch raises ValueError."""
    mock_vectors = [
        np.array([1.0, 2.0]),
        np.array([4.0, 5.0, 6.0])  # Mismatch
    ]
    mock_names = ["skill_a", "skill_b"]
    mock_data = {
        "vectors": mock_vectors,
        "names": mock_names,
        "metadata": {}
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        with patch('src.retrieval.vector_db.load_flattened_vectors', return_value=mock_data):
            try:
                build_skill_index(
                    output_dir=tmpdir,
                    output_filename="test_index.npz",
                    metadata_filename="test_meta.json"
                )
                assert False, "Expected ValueError for dimension mismatch"
            except ValueError as e:
                assert "Inconsistent vector dimension" in str(e)


def test_build_index_empty_input():
    """Test that empty input raises ValueError."""
    mock_data = {
        "vectors": [],
        "names": [],
        "metadata": {}
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        with patch('src.retrieval.vector_db.load_flattened_vectors', return_value=mock_data):
            try:
                build_skill_index(
                    output_dir=tmpdir,
                    output_filename="test_index.npz",
                    metadata_filename="test_meta.json"
                )
                assert False, "Expected ValueError for empty input"
            except ValueError as e:
                assert "No vectors found" in str(e)