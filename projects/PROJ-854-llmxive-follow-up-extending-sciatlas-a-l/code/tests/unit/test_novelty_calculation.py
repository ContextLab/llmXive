import numpy as np
import pytest
from src.services.embeddings import compute_novelty_scores

def test_novelty_scores_basic():
    """
    Test that novelty scores are positive for non-singleton nodes.
    """
    # Create 3 nodes in same cluster, distinct embeddings
    embeddings = np.array([
        [1.0, 0.0],
        [0.0, 1.0],
        [0.5, 0.5]
    ])
    cluster_ids = np.array([0, 0, 0])
    
    # Centroid will be mean of these
    # Centroid = [(1+0+0.5)/3, (0+1+0.5)/3] = [0.5, 0.5]
    # Node 0: [1, 0] vs [0.5, 0.5] -> dist > 0
    # Node 1: [0, 1] vs [0.5, 0.5] -> dist > 0
    # Node 2: [0.5, 0.5] vs [0.5, 0.5] -> dist = 0 (perfect match)
    
    centroids = np.array([[0.5, 0.5]])
    
    scores = compute_novelty_scores(embeddings, cluster_ids, centroids)
    
    assert len(scores) == 3
    assert all(s >= 0.0 for s in scores), "Scores must be non-negative"
    # Node 2 is the centroid, so score should be 0
    assert scores[2] == 0.0, "Node at centroid should have 0 novelty"
    assert scores[0] > 0.0, "Node 0 should have positive novelty"
    assert scores[1] > 0.0, "Node 1 should have positive novelty"

def test_novelty_scores_identical_nodes():
    """
    Test that identical nodes have 0 novelty (distance to centroid is 0).
    """
    embeddings = np.array([
        [1.0, 0.0],
        [1.0, 0.0],
        [1.0, 0.0]
    ])
    cluster_ids = np.array([0, 0, 0])
    centroids = np.array([[1.0, 0.0]])
    
    scores = compute_novelty_scores(embeddings, cluster_ids, centroids)
    
    assert all(s == 0.0 for s in scores), "Identical nodes to centroid should have 0 novelty"

def test_novelty_scores_empty_input():
    """
    Test handling of empty input.
    """
    embeddings = np.array([]).reshape(0, 2)
    cluster_ids = np.array([])
    centroids = np.array([]).reshape(0, 2)
    
    scores = compute_novelty_scores(embeddings, cluster_ids, centroids)
    assert len(scores) == 0

def test_novelty_scores_single_node_cluster():
    """
    Test that singleton clusters get novelty_score = 0.0.
    """
    embeddings = np.array([
        [1.0, 0.0],
        [0.0, 1.0]
    ])
    # Different clusters, so each is a singleton
    cluster_ids = np.array([0, 1])
    # Centroids are just the embeddings themselves
    centroids = np.array([
        [1.0, 0.0],
        [0.0, 1.0]
    ])
    
    scores = compute_novelty_scores(embeddings, cluster_ids, centroids)
    
    # Both should be 0.0 because they are singletons
    assert scores[0] == 0.0, "Singleton node 0 should have 0.0 novelty"
    assert scores[1] == 0.0, "Singleton node 1 should have 0.0 novelty"

def test_novelty_scores_mixed_clusters():
    """
    Test a mix of singleton and multi-node clusters.
    """
    embeddings = np.array([
        [1.0, 0.0], # Cluster 0 (singleton)
        [0.0, 1.0], # Cluster 1 (multi)
        [0.0, 0.0]  # Cluster 1 (multi)
    ])
    cluster_ids = np.array([0, 1, 1])
    # Centroid for Cluster 0 is [1, 0]
    # Centroid for Cluster 1 is [0, 0.5]
    centroids = np.array([
        [1.0, 0.0],
        [0.0, 0.5]
    ])
    
    scores = compute_novelty_scores(embeddings, cluster_ids, centroids)
    
    # Node 0: Singleton -> 0.0
    assert scores[0] == 0.0, "Singleton should be 0.0"
    
    # Node 1: [0, 1] vs [0, 0.5]. Cosine sim < 1 -> dist > 0
    # Node 2: [0, 0] vs [0, 0.5]. Cosine sim < 1 -> dist > 0
    assert scores[1] > 0.0, "Non-singleton should be > 0.0"
    assert scores[2] > 0.0, "Non-singleton should be > 0.0"
