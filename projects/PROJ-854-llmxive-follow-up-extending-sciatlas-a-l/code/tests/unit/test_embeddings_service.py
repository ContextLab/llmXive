"""
Unit tests for the embeddings service.
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
    log_memory_profile,
    save_excluded_nodes,
    compute_cluster_centroids
)
import pandas as pd
import os
import tempfile

@patch('src.services.embeddings.SentenceTransformer')
def test_load_embedding_model(mock_transformer):
    """Test that the model is loaded correctly."""
    mock_model = MagicMock()
    mock_transformer.return_value = mock_model

    model = load_embedding_model("test-model")

    mock_transformer.assert_called_once_with("test-model")
    assert model == mock_model

def test_filter_valid_nodes():
    """Test filtering of nodes with valid and invalid titles."""
    nodes = [
        {'id': '1', 'title': 'Valid Title'},
        {'id': '2', 'title': ''},
        {'id': '3', 'title': None},
        {'id': '4', 'title': '   '},
        {'id': '5', 'title': 'Another Valid Title'},
        {'id': '6'}  # Missing title key
    ]

    valid_nodes, excluded_ids = filter_valid_nodes(nodes)

    assert len(valid_nodes) == 2
    assert valid_nodes[0]['id'] == '1'
    assert valid_nodes[1]['id'] == '5'

    assert len(excluded_ids) == 4
    assert '2' in excluded_ids
    assert '3' in excluded_ids
    assert '4' in excluded_ids
    assert '6' in excluded_ids

def test_save_excluded_nodes():
    """Test saving excluded nodes to CSV."""
    excluded_ids = ['1', '2', '3']

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, 'excluded.csv')
        save_excluded_nodes(excluded_ids, output_path)

        assert os.path.exists(output_path)
        df = pd.read_csv(output_path)
        assert len(df) == 3
        assert list(df['node_id']) == ['1', '2', '3']

def test_save_excluded_nodes_empty():
    """Test saving empty excluded nodes list."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, 'excluded.csv')
        save_excluded_nodes([], output_path)

        # Should not create file if no excluded nodes
        assert not os.path.exists(output_path)

@patch('src.services.embeddings.SentenceTransformer')
def test_generate_embeddings_batched(mock_transformer):
    """Test batched embedding generation."""
    mock_model = MagicMock()
    mock_transformer.return_value = mock_model

    # Mock encode to return random embeddings
    mock_model.encode.return_value = np.random.rand(32, 384)

    texts = ['Text 1', 'Text 2', 'Text 3'] * 10  # 30 texts
    embeddings = generate_embeddings_batched(mock_model, texts, batch_size=10)

    assert embeddings.shape == (30, 384)
    assert mock_model.encode.call_count == 3  # 3 batches

def test_compute_cluster_centroids():
    """Test computation of cluster centroids."""
    embeddings = np.array([
        [1.0, 0.0],
        [0.0, 1.0],
        [1.0, 0.0],
        [0.0, 1.0]
    ])
    cluster_labels = [0, 1, 0, 1]

    centroids = compute_cluster_centroids(embeddings, cluster_labels)

    assert 0 in centroids
    assert 1 in centroids
    assert np.allclose(centroids[0], [1.0, 0.0])
    assert np.allclose(centroids[1], [0.0, 1.0])

def test_compute_novelty_scores():
    """Test novelty score computation."""
    embeddings = np.array([
        [1.0, 0.0],  # On centroid
        [0.9, 0.1],  # Slightly off
        [0.0, 1.0],  # On other centroid
    ])
    cluster_labels = [0, 0, 1]

    scores = compute_novelty_scores(embeddings, cluster_labels)

    assert len(scores) == 3
    assert scores[0] >= 0
    assert scores[2] >= 0
    # Node 0 should have lower novelty than node 1 (closer to centroid)
    assert scores[0] <= scores[1]

def test_process_nodes_for_embeddings():
    """Test node processing for embeddings."""
    nodes = [
        {'id': '1', 'title': 'Valid'},
        {'id': '2', 'title': ''},
        {'id': '3', 'title': 'Also Valid'},
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = os.path.join(tmpdir, 'excluded.csv')
        valid_nodes, node_ids, texts = process_nodes_for_embeddings(nodes, log_path)

        assert len(valid_nodes) == 2
        assert node_ids == ['1', '3']
        assert texts == ['Valid', 'Also Valid']

        assert os.path.exists(log_path)
        df = pd.read_csv(log_path)
        assert len(df) == 1
        assert df['node_id'].iloc[0] == '2'

def test_log_memory_profile():
    """Test memory profiling logging."""
    # This should not raise any errors
    log_memory_profile("test_stage")