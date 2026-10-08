import numpy as np
import networkx as nx
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple

logger = logging.getLogger(__name__)

def calculate_global_efficiency(matrix: np.ndarray) -> float:
    """
    Calculate Global Efficiency (1/average shortest path length).
    Assumes matrix is symmetric and square.
    """
    n = matrix.shape[0]
    if n == 0:
        return 0.0

    # Create graph from matrix
    G = nx.from_numpy_array(matrix)

    # Calculate average shortest path
    try:
        lengths = nx.average_shortest_path_length(G)
        if lengths == 0:
            return 0.0
        return 1.0 / lengths
    except nx.NetworkXError:
        # Graph might be disconnected
        # Calculate efficiency as sum of 1/d_ij for all pairs
        total_eff = 0.0
        count = 0
        for i in range(n):
            for j in range(i+1, n):
                try:
                    d = nx.shortest_path_length(G, i, j)
                    if d > 0:
                        total_eff += 1.0 / d
                        count += 1
                except nx.NetworkXError:
                    continue
        return total_eff / count if count > 0 else 0.0

def calculate_local_efficiency(matrix: np.ndarray) -> float:
    """
    Calculate Local Efficiency (average local efficiency of nodes).
    Local efficiency of a node is the global efficiency of its neighborhood.
    """
    n = matrix.shape[0]
    if n == 0:
        return 0.0

    G = nx.from_numpy_array(matrix)
    local_efficiencies = []

    for i in range(n):
        # Get neighbors of node i
        neighbors = list(G.neighbors(i))
        if len(neighbors) < 2:
            local_efficiencies.append(0.0)
            continue

        # Create subgraph of neighbors
        subgraph = nx.subgraph(G, [i] + neighbors)
        try:
            eff = nx.global_efficiency(subgraph)
            local_efficiencies.append(eff)
        except nx.NetworkXError:
            local_efficiencies.append(0.0)

    return sum(local_efficiencies) / len(local_efficiencies) if local_efficiencies else 0.0

def calculate_modularity(matrix: np.ndarray, community_detection: Optional[nx.community.CommunityDetection] = None) -> float:
    """
    Calculate Modularity (Q) using Louvain algorithm.
    """
    n = matrix.shape[0]
    if n == 0:
        return 0.0

    G = nx.from_numpy_array(matrix)

    # If community detection is not provided, use Louvain
    if community_detection is None:
        try:
            partition = nx.community.louvain(G)
            return nx.modularity(G, partition)
        except nx.NetworkXError:
            return 0.0
    else:
        try:
            return nx.modularity(G, community_detection)
        except nx.NetworkXError:
            return 0.0

def apply_spatial_threshold(matrix: np.ndarray, sparsity: float = 0.1) -> np.ndarray:
    """
    Apply proportional sparsity thresholding to connectivity matrix.
    Keeps the top (sparsity * 100)% of connections by weight.
    Returns a binary adjacency matrix.

    Args:
        matrix: Input connectivity matrix (numpy array)
        sparsity: Proportion of connections to keep (e., 0.1 = 10%)

    Returns:
        Binary adjacency matrix with only the strongest connections retained
    """
    if not isinstance(matrix, np.ndarray):
        raise ValueError("Input must be a numpy array")

    if sparsity <= 0 or sparsity >= 1:
        raise ValueError("Sparsity must be between 0 and 1 (exclusive)")

    n = matrix.shape[0]
    total_possible_connections = n * (n - 1) / 2  # Upper triangle

    # Get upper triangle values (excluding diagonal)
    upper_triangle = matrix[np.triu_indices(n, k=1)]
    num_to_keep = int(np.ceil(sparsity * len(upper_triangle)))

    if num_to_keep == 0:
        logger.warning("Sparsity too low, no connections will be retained")
        return np.zeros_like(matrix)

    # Find threshold value
    threshold = np.sort(upper_triangle)[-num_to_keep]

    # Create binary matrix
    binary_matrix = np.zeros_like(matrix)
    binary_matrix[matrix >= threshold] = 1

    # Ensure diagonal is zero
    np.fill_diagonal(binary_matrix, 0)

    logger.info(f"Applied sparsity threshold: {sparsity:.2%}, threshold value: {threshold:.4f}, connections kept: {num_to_keep}")

    return binary_matrix

def compute_metrics_from_matrix(matrix: np.ndarray, sparsity: Optional[float] = None) -> Dict[str, float]:
    """
    Compute graph metrics from a connectivity matrix.
    Optionally applies sparsity thresholding before calculation.

    Args:
        matrix: Connectivity matrix (numpy array)
        sparsity: Optional sparsity threshold (e.g., 0.1 for 10%)

    Returns:
        Dictionary containing global efficiency, local efficiency, and modularity
    """
    if sparsity is not None:
        matrix = apply_spatial_threshold(matrix, sparsity)

    global_eff = calculate_global_efficiency(matrix)
    local_eff = calculate_local_efficiency(matrix)
    modularity = calculate_modularity(matrix)

    return {
        "global_efficiency": float(global_eff),
        "local_efficiency": float(local_eff),
        "modularity": float(modularity)
    }

def process_connectivity_matrices(
    matrices: List[Tuple[str, np.ndarray]],
    sparsity: float = 0.1
) -> List[Dict[str, Any]]:
    """
    Process a list of connectivity matrices with sparsity thresholding.

    Args:
        matrices: List of tuples (subject_id, matrix)
        sparsity: Sparsity threshold to apply

    Returns:
        List of dictionaries with subject_id and computed metrics
    """
    results = []

    for subject_id, matrix in matrices:
        try:
            metrics = compute_metrics_from_matrix(matrix, sparsity)
            results.append({
                "subject_id": subject_id,
                "metrics": metrics
            })
            logger.info(f"Processed {subject_id}: Global Eff={metrics['global_efficiency']:.4f}")
        except Exception as e:
            logger.error(f"Failed to process {subject_id}: {e}")
            results.append({
                "subject_id": subject_id,
                "error": str(e)
            })

    return results

def main():
    """
    Main function to demonstrate sparsity thresholding and metric calculation.
    This can be used for testing or batch processing.
    """
    logging.basicConfig(level=logging.INFO)

    # Example usage
    logger.info("Testing sparsity thresholding and graph metrics calculation")

    # Create a sample matrix
    n = 5
    sample_matrix = np.random.rand(n, n)
    sample_matrix = (sample_matrix + sample_matrix.T) / 2  # Make symmetric
    np.fill_diagonal(sample_matrix, 0)

    # Test without thresholding
    metrics_no_thresh = compute_metrics_from_matrix(sample_matrix, sparsity=None)
    logger.info(f"Metrics without thresholding: {metrics_no_thresh}")

    # Test with thresholding
    metrics_with_thresh = compute_metrics_from_matrix(sample_matrix, sparsity=0.3)
    logger.info(f"Metrics with 30% sparsity: {metrics_with_thresh}")

    # Process multiple matrices
    matrices = [
        ("sub-01", sample_matrix),
        ("sub-02", sample_matrix * 0.8),
    ]
    results = process_connectivity_matrices(matrices, sparsity=0.2)
    logger.info(f"Processed {len(results)} subjects")

    return results

if __name__ == "__main__":
    main()