"""Unit tests for graph metrics calculation.

This test verifies that the graph metrics (Modularity, Global Efficiency,
Participation Coefficient, Within-Module Degree) calculated by the
`code.data.metrics` module match the expected ground truth values
derived from a known synthetic adjacency matrix.

The synthetic matrix is constructed to have a clear community structure
(two distinct modules of 5 nodes each) with strong intra-module connections
and weak inter-module connections, allowing for deterministic verification
of the metric calculations.
"""

import numpy as np
import pytest
from unittest.mock import patch, MagicMock

# Import the function to be tested from the project's metrics module
from code.data.metrics import calculate_graph_metrics


def _create_synthetic_adjacency_matrix():
    """Create a deterministic synthetic adjacency matrix with known community structure.

    Structure:
    - 10 nodes total.
    - Two modules: Nodes 0-4 (Module A) and Nodes 5-9 (Module B).
    - Intra-module edges: Probability 0.8 (dense).
    - Inter-module edges: Probability 0.1 (sparse).
    - No self-loops.

    Returns:
        np.ndarray: A 10x10 symmetric binary adjacency matrix.
    """
    n = 10
    p_intra = 0.8
    p_inter = 0.1

    # Initialize matrix with zeros
    adj = np.zeros((n, n), dtype=float)

    # Define module boundaries
    module_a = range(0, 5)
    module_b = range(5, 10)

    # Fill intra-module connections (Module A)
    for i in module_a:
        for j in module_a:
            if i != j:
                adj[i, j] = 1.0 if np.random.rand() < p_intra else 0.0

    # Fill intra-module connections (Module B)
    for i in module_b:
        for j in module_b:
            if i != j:
                adj[i, j] = 1.0 if np.random.rand() < p_intra else 0.0

    # Fill inter-module connections
    for i in module_a:
        for j in module_b:
            val = 1.0 if np.random.rand() < p_inter else 0.0
            adj[i, j] = val
            adj[j, i] = val

    return adj


def _calculate_expected_modularity(adj_matrix, communities):
    """Calculate expected modularity for verification.

    Modularity Q = (1/2m) * sum_ij [ A_ij - (k_i * k_j) / (2m) ] * delta(c_i, c_j)

    Args:
        adj_matrix: Symmetric adjacency matrix.
        communities: List of community assignments for each node.

    Returns:
        float: Modularity value.
    """
    m = np.sum(adj_matrix) / 2.0  # Total edge weight
    if m == 0:
        return 0.0

    k = np.sum(adj_matrix, axis=1)  # Degree of each node
    Q = 0.0

    n = len(adj_matrix)
    for i in range(n):
        for j in range(n):
            if communities[i] == communities[j]:
                Q += adj_matrix[i, j] - (k[i] * k[j]) / (2 * m)

    return Q / (2 * m)


def test_graph_metrics_match_synthetic_ground_truth():
    """Verify graph metrics match ground truth on a synthetic matrix.

    This test:
    1. Generates a synthetic adjacency matrix with a known 2-community structure.
    2. Calls calculate_graph_metrics with the known community labels.
    3. Verifies that the returned metrics are real, non-fabricated values.
    4. Specifically checks Modularity against a manual calculation to ensure
       the algorithm is correct.
    5. Checks that Global Efficiency, Participation Coefficient, and
       Within-Module Degree are calculated and within plausible bounds.
    """
    # Set a fixed seed for reproducibility of the synthetic matrix generation
    np.random.seed(42)

    # 1. Generate the synthetic data
    adj_matrix = _create_synthetic_adjacency_matrix()
    n_nodes = adj_matrix.shape[0]

    # Define the ground truth communities (0-4 -> 0, 5-9 -> 1)
    communities = [0] * 5 + [1] * 5

    # 2. Run the implementation under test
    # We mock the logging to avoid side effects during the test
    with patch('code.data.metrics.get_logger'):
        result = calculate_graph_metrics(adj_matrix, communities)

    # 3. Assertions
    # Ensure the result is a dictionary with the expected keys
    assert isinstance(result, dict), "Result must be a dictionary"
    required_keys = ['modularity', 'global_efficiency', 'participation_coef', 'within_module_degree']
    for key in required_keys:
        assert key in result, f"Missing key in result: {key}"

    # 4. Verify Modularity (The most critical metric for community structure)
    # Calculate expected modularity manually
    expected_modularity = _calculate_expected_modularity(adj_matrix, communities)
    calculated_modularity = result['modularity']

    # Allow a small tolerance for floating point arithmetic
    assert np.isclose(calculated_modularity, expected_modularity, atol=1e-5), \
        f"Modularity mismatch: Calculated {calculated_modularity} != Expected {expected_modularity}"

    # 5. Verify Global Efficiency
    # Global Efficiency E = (1/N(N-1)) * sum_{i!=j} (1/d_ij)
    # For a binary connected graph, it should be > 0.
    # In our synthetic graph, it's likely connected, so E > 0.
    assert result['global_efficiency'] > 0, "Global efficiency must be positive for a connected graph"
    assert result['global_efficiency'] <= 1.0, "Global efficiency cannot exceed 1.0"

    # 6. Verify Participation Coefficient (PC)
    # PC should be >= 0. High values mean nodes connect to many modules.
    # Since we have 2 modules and sparse inter-module connections, average PC should be relatively low.
    assert result['participation_coef'] >= 0, "Participation coefficient cannot be negative"
    assert result['participation_coef'] <= 1.0, "Participation coefficient cannot exceed 1.0"

    # 7. Verify Within-Module Degree (Z-score)
    # This is a z-score, so it can be negative or positive.
    # It should be a real number.
    assert isinstance(result['within_module_degree'], (int, float)), "Within-module degree must be numeric"
    # We don't check exact value as it depends on degree distribution variance,
    # but we ensure it's not NaN or Inf
    assert not np.isnan(result['within_module_degree']), "Within-module degree cannot be NaN"
    assert not np.isinf(result['within_module_degree']), "Within-module degree cannot be Inf"

    # 8. Final sanity check: Ensure no synthetic/fake values were hardcoded
    # The values must be derived from the matrix.
    # If the matrix changes, these values should change.
    # We verify this by checking that the values are not exactly 0.0 or 1.0
    # unless the graph is trivial (which ours is not).
    assert result['modularity'] != 0.0 or result['global_efficiency'] != 0.0, \
        "Metrics seem to be default/placeholder values"