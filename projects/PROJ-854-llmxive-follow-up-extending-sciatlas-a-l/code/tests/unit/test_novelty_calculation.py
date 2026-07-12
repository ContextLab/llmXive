import numpy as np
import pytest
from src.services.embeddings import compute_novelty_scores

def test_novelty_scores_basic():
    """
    Test basic novelty score calculation.
    """
    embeddings = np.array([
        [1.0, 0.0],
        [0.0, 1.0],
        [1.0, 0.0] # Same as first
    ])
    clusters = [0, 1, 0]
    
    scores = compute_novelty_scores(embeddings, clusters)
    
    assert len(scores) == 3
    assert all(isinstance(s, float) for s in scores)

def test_novelty_scores_identical_nodes():
    """
    Test that nodes with identical embeddings in the same cluster have low/zero novelty.
    """
    embeddings = np.array([
        [1.0, 0.0],
        [1.0, 0.0],
        [1.0, 0.0]
    ])
    clusters = [0, 0, 0]
    
    scores = compute_novelty_scores(embeddings, clusters)
    
    # All identical to centroid -> distance ~ 0
    assert all(s < 1e-5 for s in scores)

def test_novelty_scores_empty_input():
    """
    Test handling of empty input.
    """
    embeddings = np.array([]).reshape(0, 2)
    clusters = []
    
    scores = compute_novelty_scores(embeddings, clusters)
    assert len(scores) == 0

def test_novelty_scores_single_node_cluster():
    """
    Test novelty score for a cluster with a single node.
    """
    embeddings = np.array([[1.0, 0.0]])
    clusters = [0]
    
    scores = compute_novelty_scores(embeddings, clusters)
    # Distance to itself is 0
    assert scores[0] == 0.0
