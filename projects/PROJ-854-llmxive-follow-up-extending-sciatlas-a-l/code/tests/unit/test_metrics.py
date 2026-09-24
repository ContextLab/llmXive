import pytest
import numpy as np
from typing import List, Dict, Any
from src.services.embeddings import compute_novelty_scores

def test_novelty_central_distance_unit():
    """
    Unit test for novelty logic:
    1. Verify that a node identical to its centroid has distance 0.0.
    2. Verify that a singleton node has distance 0.0.
    3. Verify that a node far from its centroid has a positive distance.
    """
    # Define a fixed random seed for reproducibility if needed
    np.random.seed(42)

    # Case 1: Node identical to centroid
    # We create a scenario where the node's embedding IS the centroid.
    # This implies the cluster centroid is the mean of embeddings.
    # If we have one node, its centroid is itself.
    # If we have multiple identical nodes, their centroid is that value.
    
    # Scenario A: Single node (Singleton)
    # Embedding: [1.0, 0.0, 0.0]
    # Cluster ID: 1
    # Since it's the only node, centroid = [1.0, 0.0, 0.0]
    # Distance should be 0.0
    embeddings_singleton = np.array([[1.0, 0.0, 0.0]])
    cluster_ids_singleton = np.array([1])
    cluster_centroids_singleton = {1: np.array([1.0, 0.0, 0.0])}
    
    # We need to call the function that computes novelty scores.
    # The function signature in embeddings.py is:
    # compute_novelty_scores(embeddings: np.ndarray, cluster_ids: np.ndarray, centroids: Dict[int, np.ndarray]) -> np.ndarray
    
    scores_singleton = compute_novelty_scores(
        embeddings_singleton, 
        cluster_ids_singleton, 
        cluster_centroids_singleton
    )
    
    assert scores_singleton.shape == (1,), "Score shape mismatch for singleton"
    assert np.isclose(scores_singleton[0], 0.0, atol=1e-6), \
        f"Singleton node distance should be 0.0, got {scores_singleton[0]}"

    # Scenario B: Node identical to centroid (Multi-node cluster with identical embeddings)
    # Two nodes, both at [1.0, 0.0, 0.0]
    # Centroid = [1.0, 0.0, 0.0]
    # Distance for both should be 0.0
    embeddings_identical = np.array([
        [1.0, 0.0, 0.0],
        [1.0, 0.0, 0.0]
    ])
    cluster_ids_identical = np.array([2, 2])
    cluster_centroids_identical = {2: np.array([1.0, 0.0, 0.0])}
    
    scores_identical = compute_novelty_scores(
        embeddings_identical,
        cluster_ids_identical,
        cluster_centroids_identical
    )
    
    assert scores_identical.shape == (2,), "Score shape mismatch for identical nodes"
    assert np.allclose(scores_identical, 0.0, atol=1e-6), \
        f"Identical nodes distance should be 0.0, got {scores_identical}"

    # Scenario C: Node distinct from centroid (Sanity check)
    # Centroid at [0.0, 0.0, 0.0], Node at [1.0, 0.0, 0.0]
    # Cosine distance should be 1.0 (since vectors are orthogonal? No, [1,0,0] vs [0,0,0] is undefined)
    # Let's use valid non-zero vectors.
    # Centroid: [1, 0, 0], Node: [0, 1, 0] -> Cosine similarity 0 -> Distance 1.0
    embeddings_distinct = np.array([[0.0, 1.0, 0.0]])
    cluster_ids_distinct = np.array([3])
    cluster_centroids_distinct = {3: np.array([1.0, 0.0, 0.0])}
    
    scores_distinct = compute_novelty_scores(
        embeddings_distinct,
        cluster_ids_distinct,
        cluster_centroids_distinct
    )
    
    # Cosine similarity between (0,1,0) and (1,0,0) is 0.
    # Cosine distance = 1 - similarity = 1.0
    assert np.isclose(scores_distinct[0], 1.0, atol=1e-6), \
        f"Distinct node distance should be 1.0, got {scores_distinct[0]}"

    # Scenario D: Node slightly offset from centroid
    # Centroid: [1, 0, 0], Node: [1, 0.1, 0]
    embeddings_offset = np.array([[1.0, 0.1, 0.0]])
    cluster_ids_offset = np.array([4])
    # Centroid is mean of cluster. If only one node, centroid is the node.
    # To force a centroid different from the node, we need multiple nodes in the cluster
    # but we are testing the distance calculation logic directly.
    # Let's manually set a centroid that is NOT the node.
    cluster_centroids_offset = {4: np.array([1.0, 0.0, 0.0])}
    
    scores_offset = compute_novelty_scores(
        embeddings_offset,
        cluster_ids_offset,
        cluster_centroids_offset
    )
    
    # Vector A: [1, 0.1, 0], Vector B: [1, 0, 0]
    # Dot = 1.0
    # Norm A = sqrt(1 + 0.01) = sqrt(1.01) ~ 1.005
    # Norm B = 1.0
    # Sim = 1.0 / (1.005 * 1) ~ 0.995
    # Dist = 1 - 0.995 = 0.005
    expected_sim = 1.0 / (np.sqrt(1.0**2 + 0.1**2) * 1.0)
    expected_dist = 1.0 - expected_sim
    
    assert np.isclose(scores_offset[0], expected_dist, atol=1e-6), \
        f"Offset node distance mismatch. Expected {expected_dist}, got {scores_offset[0]}"

    print("All novelty unit tests passed.")