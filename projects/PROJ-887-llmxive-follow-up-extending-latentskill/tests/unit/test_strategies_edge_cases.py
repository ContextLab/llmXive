"""
Unit tests for src.retrieval.strategies edge cases.
Specifically tests the graceful handling of empty result sets (T048).
"""
import os
import sys
import tempfile
import numpy as np
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path if running standalone
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.retrieval.strategies import (
    load_skill_index,
    unweighted_mean,
    cosine_weighted_average,
    single_nearest_neighbor
)


class TestEmptyResultSets:
    """Tests for handling empty or insufficient result sets in strategies."""

    @pytest.fixture
    def mock_skill_index(self, tmp_path):
        """Create a temporary skill index file for testing."""
        index_path = tmp_path / "skill_index.npz"
        # Create a small dummy index
        vectors = np.array([
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0]
        ], dtype=np.float32)
        ids = np.array(["skill_1", "skill_2", "skill_3"])
        np.savez(index_path, vectors=vectors, ids=ids)
        return index_path

    @pytest.fixture
    def empty_index_path(self, tmp_path):
        """Create an empty skill index file."""
        index_path = tmp_path / "empty_index.npz"
        # Create an empty index with correct structure but no data
        vectors = np.array([], dtype=np.float32).reshape(0, 3)
        ids = np.array([], dtype='<U10')
        np.savez(index_path, vectors=vectors, ids=ids)
        return index_path

    def test_unweighted_mean_empty_list(self):
        """Test that unweighted_mean handles an empty list of vectors gracefully."""
        vectors = []
        with pytest.raises(ValueError) as exc_info:
            unweighted_mean(vectors)
        assert "Empty vector list" in str(exc_info.value)

    def test_unweighted_mean_insufficient_vectors(self, mock_skill_index):
        """Test that unweighted_mean handles k > available vectors."""
        # Load index
        index_data = np.load(mock_skill_index)
        vectors = [index_data['vectors'][0]]  # Only 1 vector available

        # Request 5 neighbors but only 1 available
        result = unweighted_mean(vectors, k=5)

        # Should proceed with available items (1 vector)
        assert isinstance(result, np.ndarray)
        assert result.shape == (3,)
        # Should be equal to the single available vector
        np.testing.assert_array_almost_equal(result, vectors[0])

    def test_cosine_weighted_average_empty_list(self):
        """Test that cosine_weighted_average handles an empty list."""
        vectors = []
        similarities = []
        with pytest.raises(ValueError) as exc_info:
            cosine_weighted_average(vectors, similarities)
        assert "Empty vector list" in str(exc_info.value)

    def test_cosine_weighted_average_insufficient_vectors(self, mock_skill_index):
        """Test that cosine_weighted_average handles k > available vectors."""
        index_data = np.load(mock_skill_index)
        vectors = [index_data['vectors'][0]]
        similarities = [0.9]

        # Request 5 neighbors but only 1 available
        result = cosine_weighted_average(vectors, similarities, k=5)

        # Should proceed with available items
        assert isinstance(result, np.ndarray)
        assert result.shape == (3,)
        np.testing.assert_array_almost_equal(result, vectors[0])

    def test_single_nearest_neighbor_empty_index(self, empty_index_path):
        """Test that single_nearest_neighbor handles an empty index."""
        query_vector = np.array([1.0, 0.0, 0.0], dtype=np.float32)

        with pytest.raises(ValueError) as exc_info:
            single_nearest_neighbor(query_vector, empty_index_path, k=1)
        assert "No vectors available in index" in str(exc_info.value)

    def test_single_nearest_neighbor_insufficient_neighbors(self, mock_skill_index):
        """Test that single_nearest_neighbor handles k > available vectors."""
        query_vector = np.array([1.0, 0.0, 0.0], dtype=np.float32)

        # Request 10 neighbors but only 3 available
        result = single_nearest_neighbor(query_vector, mock_skill_index, k=10)

        # Should return the single nearest neighbor
        assert isinstance(result, dict)
        assert 'vector' in result
        assert 'id' in result
        assert 'similarity' in result
        assert result['id'] == 'skill_1'  # First vector is identical to query

    @patch('src.retrieval.strategies.load_skill_index')
    def test_unweighted_mean_warning_logging(self, mock_load, mock_skill_index, caplog):
        """Test that a warning is logged when k > available vectors."""
        import logging

        # Setup mock to return only 2 vectors
        mock_data = MagicMock()
        mock_data['vectors'] = np.array([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32)
        mock_data['ids'] = np.array(['a', 'b'])
        mock_load.return_value = mock_data

        # Request 5 neighbors
        with caplog.at_level(logging.WARNING):
            result = unweighted_mean([], k=5)

        # Check that a warning was logged
        assert any("Insufficient neighbors retrieved" in record.message for record in caplog.records)

    @patch('src.retrieval.strategies.load_skill_index')
    def test_cosine_weighted_average_warning_logging(self, mock_load, mock_skill_index, caplog):
        """Test that a warning is logged when k > available vectors for weighted average."""
        import logging

        # Setup mock
        mock_data = MagicMock()
        mock_data['vectors'] = np.array([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32)
        mock_data['ids'] = np.array(['a', 'b'])
        mock_load.return_value = mock_data

        vectors = [np.array([1.0, 0.0], dtype=np.float32)]
        similarities = [0.9]

        # Request 5 neighbors
        with caplog.at_level(logging.WARNING):
            result = cosine_weighted_average(vectors, similarities, k=5)

        # Check that a warning was logged
        assert any("Insufficient neighbors retrieved" in record.message for record in caplog.records)

    def test_edge_case_single_vector(self, mock_skill_index):
        """Test that strategies work correctly with exactly one vector."""
        index_data = np.load(mock_skill_index)
        vectors = [index_data['vectors'][0]]
        similarities = [1.0]

        # Unweighted mean with single vector
        result_mean = unweighted_mean(vectors)
        np.testing.assert_array_almost_equal(result_mean, vectors[0])

        # Cosine weighted average with single vector
        result_weighted = cosine_weighted_average(vectors, similarities)
        np.testing.assert_array_almost_equal(result_weighted, vectors[0])