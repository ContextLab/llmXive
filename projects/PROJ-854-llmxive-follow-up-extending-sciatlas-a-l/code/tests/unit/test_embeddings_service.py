"""
Unit tests for the embeddings service.

Tests:
- Model loading
- Valid node filtering
- Batched embedding generation
- Novelty score computation
- Memory profiling
"""

import pytest
import numpy as np
from unittest.mock import patch, MagicMock

from src.services.embeddings import (
    load_embedding_model,
    filter_valid_nodes,
    generate_embeddings_batched,
    compute_novelty_scores,
    process_nodes_for_embeddings,
    log_memory_profile
)

@patch('src.services.embeddings.SentenceTransformer')
def test_load_embedding_model(mock_sentence_transformer):
    """Test that the embedding model is loaded correctly."""
    mock_model = MagicMock()
    mock_sentence_transformer.return_value = mock_model
    
    model = load_embedding_model()
    
    mock_sentence_transformer.assert_called_once_with(
        'sentence-transformers/all-MiniLM-L6-v2',
        device='cpu'
    )
    assert model == mock_model

def test_filter_valid_nodes():
    """Test filtering of nodes with valid titles."""
    nodes = [
        {'id': '1', 'title': 'Valid title'},
        {'id': '2', 'title': ''},
        {'id': '3', 'title': '   '},
        {'id': '4', 'title': 'Another valid title'},
        {'id': '5', 'title': None}
    ]
    
    valid_nodes, excluded_ids = filter_valid_nodes(nodes)
    
    assert len(valid_nodes) == 2
    assert valid_nodes[0]['id'] == '1'
    assert valid_nodes[1]['id'] == '4'
    assert len(excluded_ids) == 3
    assert '2' in excluded_ids
    assert '3' in excluded_ids
    assert '5' in excluded_ids

@patch('src.services.embeddings.SentenceTransformer')
def test_generate_embeddings_batched(mock_sentence_transformer):
    """Test batched embedding generation."""
    mock_model = MagicMock()
    mock_model.encode.return_value = np.random.rand(32, 384)
    mock_sentence_transformer.return_value = mock_model
    
    model = load_embedding_model()
    texts = ['text1'] * 50  # 50 texts, 2 batches (32 + 18)
    
    embeddings = generate_embeddings_batched(model, texts, batch_size=32)
    
    assert embeddings.shape == (50, 384)
    assert mock_model.encode.call_count == 2

def test_compute_novelty_scores():
    """Test novelty score computation."""
    # Create embeddings for 4 nodes
    embeddings = np.array([
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [1.0, 0.0, 0.0],  # Same as node 0
        [0.0, 0.0, 1.0]
    ])
    
    # Assign to 2 clusters
    topic_clusters = [0, 1, 0, 2]
    
    novelty_scores = compute_novelty_scores(embeddings, topic_clusters)
    
    assert len(novelty_scores) == 4
    assert all(0.0 <= score <= 2.0 for score in novelty_scores)  # Cosine distance range
    
    # Node 0 and 2 are identical and in same cluster, should have low novelty
    # Node 1 is in different cluster, should have higher novelty

def test_process_nodes_for_embeddings():
    """Test node processing for embeddings."""
    nodes = [
        {'id': '1', 'title': 'Valid title', 'topic_cluster': 0},
        {'id': '2', 'title': '', 'topic_cluster': 1},
        {'id': '3', 'title': 'Another valid', 'topic_cluster': 0}
    ]
    
    valid_nodes, titles, excluded_ids = process_nodes_for_embeddings(nodes)
    
    assert len(valid_nodes) == 2
    assert titles == ['Valid title', 'Another valid']
    assert len(excluded_ids) == 1
    assert excluded_ids[0] == '2'

def test_log_memory_profile():
    """Test memory profiling logging."""
    stats = log_memory_profile()
    
    # Should return a dict, possibly empty if psutil not available
    assert isinstance(stats, dict)
    if stats:
        assert 'rss_mb' in stats or 'vms_mb' in stats
