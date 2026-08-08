"""
Unit tests for src/retrieval/query.py.
"""
import numpy as np
import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock

from src.retrieval.query import generate_query_embeddings, query_skill_db


@pytest.fixture
def mock_model():
    """Mock the SentenceTransformer to avoid downloading the real model during unit tests."""
    mock_instance = MagicMock()
    # Return a deterministic dummy embedding of shape (1, 384)
    dummy_emb = np.random.RandomState(42).rand(1, 384).astype(np.float32)
    mock_instance.encode.return_value = dummy_emb
    return mock_instance


def test_generate_query_embeddings_empty_list():
    """Test that an empty list raises ValueError."""
    with pytest.raises(ValueError, match="Input texts list cannot be empty"):
        generate_query_embeddings([])


@patch('src.retrieval.query.SentenceTransformer')
def test_generate_query_embeddings_calls_model(mock_sentence_transformer, mock_model):
    """Test that the model is called correctly."""
    mock_sentence_transformer.return_value = mock_model
    
    texts = ["Task A", "Task B"]
    embeddings, latency = generate_query_embeddings(texts)
    
    mock_model.encode.assert_called_once()
    assert embeddings.shape == (2, 384)
    assert latency >= 0


@patch('src.retrieval.query.SentenceTransformer')
def test_generate_query_embeddings_latency_logging(mock_sentence_transformer, mock_model, caplog):
    """Test that latency is logged."""
    mock_sentence_transformer.return_value = mock_model
    
    texts = ["Single Task"]
    with caplog.at_level("INFO"):
        generate_query_embeddings(texts)
    
    assert "completed in" in caplog.text


def test_query_skill_db_with_mocked_embedding():
    """Test the full query pipeline with a mocked embedding generator."""
    # Create a temporary index file
    with tempfile.NamedTemporaryFile(suffix='.npz', delete=False) as tmp:
        # Create dummy skill vectors (L2 normalized)
        num_skills = 10
        dim = 384
        rng = np.random.RandomState(123)
        vectors = rng.rand(num_skills, dim).astype(np.float32)
        vectors = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)
        
        np.savez(tmp.name, vectors=vectors)
        index_path = tmp.name

    try:
        # Mock the embedding generation to return a specific vector
        mock_query_vec = np.array([[1.0] + [0.0] * 383], dtype=np.float32)
        mock_query_vec = mock_query_vec / np.linalg.norm(mock_query_vec)
        
        with patch('src.retrieval.query.generate_query_embeddings') as mock_gen:
            mock_gen.return_value = (mock_query_vec, 0.01) # (embeddings, latency)
            
            indices, similarities, total_latency = query_skill_db(
                task_description="Test query",
                index_path=index_path,
                top_k=3
            )
        
        assert len(indices) == 3
        assert len(similarities) == 3
        assert total_latency >= 0.01 # Should be at least the mocked embedding latency
        
        # Verify that the indices correspond to the highest dot products
        # Since our mock query is [1, 0...], the vector with the highest first component should be top
        expected_top = np.argmax(vectors[:, 0])
        assert expected_top in indices
        
    finally:
        os.unlink(index_path)
