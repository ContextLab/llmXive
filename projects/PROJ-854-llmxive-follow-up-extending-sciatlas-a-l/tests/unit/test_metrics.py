"""
Unit tests for novelty calculation metrics.
Specifically tests the central distance logic for novelty scores.
"""
import pytest
import numpy as np
from typing import List, Dict, Any
from src.services.embeddings import compute_novelty_scores


def test_novelty_central_distance_unit():
    """
    Unit test for novelty logic: verifies the cosine distance calculation
    against known centroids.

    Logic:
    1. Verify that a node identical to its centroid has distance 0.0.
    2. Verify that a singleton node (cluster size 1) has distance 0.0.
    3. Verify that a node distinct from its centroid has a positive distance.
    """
    # Use a fixed seed for reproducibility in any random generation if needed
    np.random.seed(42)

    # Dimension of embeddings (standard for all-MiniLM-L6-v2 is 384)
    dim = 384

    # --- Case 1: Node identical to centroid ---
    # Create a centroid vector
    centroid_1 = np.random.randn(dim)
    centroid_1 = centroid_1 / np.linalg.norm(centroid_1)  # Normalize

    # Create a node vector identical to the centroid
    node_1 = centroid_1.copy()

    # Construct input data for Case 1
    # Structure: list of dicts with 'id', 'embedding', 'topic_cluster'
    data_case_1 = [
        {"id": "node_1", "embedding": node_1, "topic_cluster": 1},
    ]
    # Centroids map: cluster_id -> centroid vector
    centroids_case_1 = {1: centroid_1}

    # Compute novelty scores
    results_1 = compute_novelty_scores(data_case_1, centroids_case_1)

    # Assert distance is 0.0 (within floating point tolerance)
    assert len(results_1) == 1
    assert np.isclose(results_1[0]["novelty_score"], 0.0, atol=1e-7), \
        f"Expected 0.0 for identical node, got {results_1[0]['novelty_score']}"


    # --- Case 2: Singleton node ---
    # A singleton node is the only member of its cluster.
    # The centroid of a single-node cluster is the node itself.
    # Therefore, distance should be 0.0.
    centroid_2 = np.random.randn(dim)
    centroid_2 = centroid_2 / np.linalg.norm(centroid_2)
    node_2 = centroid_2.copy()  # The node IS the centroid

    data_case_2 = [
        {"id": "node_2", "embedding": node_2, "topic_cluster": 2},
    ]
    centroids_case_2 = {2: centroid_2}

    results_2 = compute_novelty_scores(data_case_2, centroids_case_2)

    assert len(results_2) == 1
    assert np.isclose(results_2[0]["novelty_score"], 0.0, atol=1e-7), \
        f"Expected 0.0 for singleton node, got {results_2[0]['novelty_score']}"


    # --- Case 3: Node distinct from centroid ---
    # Create a centroid
    centroid_3 = np.array([1.0, 0.0, 0.0])  # Simple unit vector
    centroid_3 = centroid_3 / np.linalg.norm(centroid_3)

    # Create a node orthogonal to the centroid (90 degrees)
    # Cosine similarity = 0, Cosine distance = 1.0
    node_3 = np.array([0.0, 1.0, 0.0])
    node_3 = node_3 / np.linalg.norm(node_3)

    data_case_3 = [
        {"id": "node_3", "embedding": node_3, "topic_cluster": 3},
    ]
    centroids_case_3 = {3: centroid_3}

    results_3 = compute_novelty_scores(data_case_3, centroids_case_3)

    assert len(results_3) == 1
    # Cosine distance between orthogonal vectors is 1.0
    assert np.isclose(results_3[0]["novelty_score"], 1.0, atol=1e-7), \
        f"Expected 1.0 for orthogonal node, got {results_3[0]['novelty_score']}"

    # --- Case 4: Multiple nodes in a cluster ---
    # Verify calculation holds when cluster has > 1 member
    centroid_4 = np.array([1.0, 0.0, 0.0])
    node_4a = np.array([1.0, 0.0, 0.0])  # Matches centroid -> 0.0
    node_4b = np.array([0.0, 1.0, 0.0])  # Orthogonal -> 1.0

    data_case_4 = [
        {"id": "node_4a", "embedding": node_4a, "topic_cluster": 4},
        {"id": "node_4b", "embedding": node_4b, "topic_cluster": 4},
    ]
    centroids_case_4 = {4: centroid_4}

    results_4 = compute_novelty_scores(data_case_4, centroids_case_4)

    assert len(results_4) == 2
    # Find results by ID to assert specific values
    res_4a = next(r for r in results_4 if r["id"] == "node_4a")
    res_4b = next(r for r in results_4 if r["id"] == "node_4b")

    assert np.isclose(res_4a["novelty_score"], 0.0, atol=1e-7), \
        f"Expected 0.0 for node_4a, got {res_4a['novelty_score']}"
    assert np.isclose(res_4b["novelty_score"], 1.0, atol=1e-7), \
        f"Expected 1.0 for node_4b, got {res_4b['novelty_score']}"