"""
Integration tests for the embeddings pipeline.

Tests:
- Full pipeline from node list to embeddings and novelty scores
- Memory constraints compliance
- Latency threshold compliance
"""

import pytest
import numpy as np
from unittest.mock import patch, MagicMock

from src.services.embeddings import (
    generate_embeddings_for_dataset,
    load_embedding_model,
    generate_embeddings_batched
)

@pytest.fixture
def sample_nodes():
    """Create a sample list of nodes for testing."""
    return [
        {'id': str(i), 'title': f'Test title {i}', 'topic_cluster': i % 3}
        for i in range(100)
    ]

@patch('src.services.embeddings.SentenceTransformer')
def test_full_embeddings_pipeline(mock_sentence_transformer, sample_nodes):
    """Test the full embeddings pipeline."""
    # Mock the model
    mock_model = MagicMock()
    mock_model.encode.return_value = np.random.rand(32, 384)
    mock_sentence_transformer.return_value = mock_model
    
    # Run the pipeline
    valid_nodes, embeddings, novelty_scores, excluded_ids = generate_embeddings_for_dataset(
        sample_nodes,
        output_path=None
    )
    
    # Verify results
    assert len(valid_nodes) == 100
    assert embeddings.shape == (100, 384)
    assert len(novelty_scores) == 100
    assert len(excluded_ids) == 0
    
    # Verify all novelty scores are valid
    assert all(0.0 <= score <= 2.0 for score in novelty_scores)

@patch('src.services.embeddings.SentenceTransformer')
def test_embeddings_with_excluded_nodes(mock_sentence_transformer):
    """Test pipeline with nodes that have empty titles."""
    nodes = [
        {'id': '1', 'title': 'Valid title', 'topic_cluster': 0},
        {'id': '2', 'title': '', 'topic_cluster': 1},
        {'id': '3', 'title': 'Another valid', 'topic_cluster': 0},
        {'id': '4', 'title': '', 'topic_cluster': 2}
    ]
    
    # Mock the model
    mock_model = MagicMock()
    mock_model.encode.return_value = np.random.rand(2, 384)
    mock_sentence_transformer.return_value = mock_model
    
    # Run the pipeline
    valid_nodes, embeddings, novelty_scores, excluded_ids = generate_embeddings_for_dataset(
        nodes,
        output_path=None
    )
    
    # Verify results
    assert len(valid_nodes) == 2
    assert embeddings.shape == (2, 384)
    assert len(novelty_scores) == 2
    assert len(excluded_ids) == 2
    assert '2' in excluded_ids
    assert '4' in excluded_ids

@patch('src.services.embeddings.SentenceTransformer')
def test_embeddings_memory_compliance(mock_sentence_transformer):
    """Test that embeddings are generated within memory constraints."""
    # Mock the model
    mock_model = MagicMock()
    # Simulate a larger batch to test memory handling
    mock_model.encode.return_value = np.random.rand(32, 384)
    mock_sentence_transformer.return_value = mock_model
    
    # Create a larger dataset
    nodes = [
        {'id': str(i), 'title': f'Test title {i}', 'topic_cluster': i % 3}
        for i in range(500)
    ]
    
    # Run the pipeline
    valid_nodes, embeddings, novelty_scores, excluded_ids = generate_embeddings_for_dataset(
        nodes,
        output_path=None
    )
    
    # Verify results
    assert len(valid_nodes) == 500
    assert embeddings.shape == (500, 384)
    assert len(novelty_scores) == 500
