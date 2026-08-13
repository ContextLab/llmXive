"""
Unit tests for src/retrieval/query.py

Tests for FR-002: Query vector generation with latency measurement.
"""

import os
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from src.retrieval.query import (
    load_embedding_model,
    generate_query_embeddings,
    get_query_vector,
    save_query_results,
    DEFAULT_MODEL,
    MODEL_DIMENSION
)


class TestLoadEmbeddingModel:
    """Tests for load_embedding_model function."""

    def test_load_model_success(self):
        """Test that model loads successfully."""
        # Mock the SentenceTransformer to avoid actual download
        with patch('src.retrieval.query.SentenceTransformer') as mock_model_class:
            mock_instance = MagicMock()
            mock_instance.get_sentence_embedding_dimension.return_value = MODEL_DIMENSION
            mock_model_class.return_value = mock_instance

            model = load_embedding_model(DEFAULT_MODEL)

            mock_model_class.assert_called_once_with(DEFAULT_MODEL)
            assert model == mock_instance

    def test_load_model_failure(self):
        """Test that exception is raised when model loading fails."""
        with patch('src.retrieval.query.SentenceTransformer') as mock_model_class:
            mock_model_class.side_effect = Exception("Model not found")

            with pytest.raises(Exception, match="Model not found"):
                load_embedding_model(DEFAULT_MODEL)


class TestGenerateQueryEmbeddings:
    """Tests for generate_query_embeddings function."""

    def test_empty_input(self):
        """Test handling of empty input list."""
        with patch('src.retrieval.query.SentenceTransformer') as mock_model_class:
            mock_instance = MagicMock()
            mock_model_class.return_value = mock_instance

            model = load_embedding_model()
            embeddings, latency = generate_query_embeddings(model, [])

            assert embeddings.shape == (0,)
            assert latency == 0.0

    def test_single_query(self):
        """Test embedding generation for a single query."""
        with patch('src.retrieval.query.SentenceTransformer') as mock_model_class:
            mock_instance = MagicMock()
            # Return 2D array even for single input
            mock_instance.encode.return_value = np.random.rand(1, MODEL_DIMENSION)
            mock_model_class.return_value = mock_instance

            model = load_embedding_model()
            embeddings, latency = generate_query_embeddings(model, ["test query"])

            assert embeddings.shape == (1, MODEL_DIMENSION)
            assert latency >= 0.0

    def test_multiple_queries(self):
        """Test embedding generation for multiple queries."""
        num_queries = 10
        with patch('src.retrieval.query.SentenceTransformer') as mock_model_class:
            mock_instance = MagicMock()
            mock_instance.encode.return_value = np.random.rand(num_queries, MODEL_DIMENSION)
            mock_model_class.return_value = mock_instance

            model = load_embedding_model()
            queries = [f"query {i}" for i in range(num_queries)]
            embeddings, latency = generate_query_embeddings(model, queries)

            assert embeddings.shape == (num_queries, MODEL_DIMENSION)
            assert latency >= 0.0

    def test_latency_measurement(self):
        """Test that latency is actually measured."""
        with patch('src.retrieval.query.SentenceTransformer') as mock_model_class:
            mock_instance = MagicMock()
            mock_instance.encode.return_value = np.random.rand(5, MODEL_DIMENSION)
            mock_model_class.return_value = mock_instance

            model = load_embedding_model()
            _, latency = generate_query_embeddings(model, ["test"] * 5)

            # Latency should be a non-negative float
            assert isinstance(latency, float)
            assert latency >= 0.0


class TestGetQueryVector:
    """Tests for get_query_vector function."""

    def test_single_vector_shape(self):
        """Test that single query returns 1D vector."""
        with patch('src.retrieval.query.SentenceTransformer') as mock_model_class:
            mock_instance = MagicMock()
            mock_instance.encode.return_value = np.random.rand(1, MODEL_DIMENSION)
            mock_model_class.return_value = mock_instance

            model = load_embedding_model()
            vector, latency = get_query_vector(model, "test query")

            assert vector.shape == (MODEL_DIMENSION,)
            assert latency >= 0.0


class TestSaveQueryResults:
    """Tests for save_query_results function."""

    def test_save_with_embeddings(self):
        """Test saving embeddings and latencies to disk."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "test_results.npz"
            embeddings = np.random.rand(5, MODEL_DIMENSION)
            latencies = [0.1, 0.2, 0.3, 0.4, 0.5]
            query_texts = ["q1", "q2", "q3", "q4", "q5"]

            save_query_results(embeddings, latencies, output_path, query_texts)

            assert output_path.exists()

            # Load and verify
            loaded = np.load(output_path, allow_pickle=True)
            assert 'embeddings' in loaded
            assert 'latencies' in loaded
            assert 'metadata' in loaded

            np.testing.assert_array_equal(loaded['embeddings'], embeddings)

    def test_save_without_query_texts(self):
        """Test saving without query texts."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "test_results.npz"
            embeddings = np.random.rand(3, MODEL_DIMENSION)
            latencies = [0.1, 0.2, 0.3]

            save_query_results(embeddings, latencies, output_path)

            assert output_path.exists()
            loaded = np.load(output_path, allow_pickle=True)
            assert 'embeddings' in loaded
            assert 'latencies' in loaded


class TestQueryIntegration:
    """Integration-style tests for the query module."""

    def test_full_pipeline_mock(self):
        """Test the full pipeline with mocked model."""
        with patch('src.retrieval.query.SentenceTransformer') as mock_model_class:
            mock_instance = MagicMock()
            mock_instance.get_sentence_embedding_dimension.return_value = MODEL_DIMENSION
            mock_instance.encode.return_value = np.random.rand(10, MODEL_DIMENSION)
            mock_model_class.return_value = mock_instance

            # Load model
            model = load_embedding_model()

            # Generate embeddings
            queries = [f"query {i}" for i in range(10)]
            embeddings, total_latency = generate_query_embeddings(model, queries)

            # Verify shapes
            assert embeddings.shape == (10, MODEL_DIMENSION)
            assert total_latency >= 0.0

            # Get single vector
            single_vector, single_latency = get_query_vector(model, "single query")
            assert single_vector.shape == (MODEL_DIMENSION,)
            assert single_latency >= 0.0