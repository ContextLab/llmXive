"""
Graph-theoretical network metrics calculation.

Implements Global Efficiency, Characteristic Path Length, Local Efficiency,
Clustering Coefficient, and Modularity based on connectivity matrices.

CRITICAL: Global and Local Efficiency are calculated as the reciprocal of
Characteristic Path Length to satisfy FR-003.
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union

import numpy as np
import networkx as nx

from config import get_config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def calculate_shortest_paths(adjacency_matrix: np.ndarray) -> np.ndarray:
    """
    Calculate the shortest path lengths between all pairs of nodes.

    Args:
        adjacency_matrix: Square matrix representing edge weights (connectivity strengths).

    Returns:
        Distance matrix where D[i, j] is the shortest path length from i to j.
        If no path exists, D[i, j] = np.inf.
    """
    n = adjacency_matrix.shape[0]
    dist_matrix = np.full((n, n), np.inf)
    np.fill_diagonal(dist_matrix, 0.0)

    # Floyd-Warshall algorithm for all-pairs shortest paths
    # Works for weighted graphs
    for k in range(n):
        for i in range(n):
            for j in range(n):
                if dist_matrix[i, k] + adjacency_matrix[k, j] < dist_matrix[i, j]:
                    dist_matrix[i, j] = dist_matrix[i, k] + adjacency_matrix[k, j]

    return dist_matrix


def calculate_characteristic_path_length(adjacency_matrix: np.ndarray) -> float:
    """
    Calculate the characteristic path length of the network.

    This is the average shortest path length between all pairs of nodes.

    Args:
        adjacency_matrix: Square matrix representing edge weights.

    Returns:
        The characteristic path length (average of shortest paths).
        Returns np.nan if the graph is disconnected or has no edges.
    """
    dist_matrix = calculate_shortest_paths(adjacency_matrix)
    n = dist_matrix.shape[0]

    # Sum all finite off-diagonal distances
    finite_distances = []
    for i in range(n):
        for j in range(n):
            if i != j and np.isfinite(dist_matrix[i, j]):
                finite_distances.append(dist_matrix[i, j])

    if not finite_distances:
        logger.warning("Graph is disconnected or has no edges. Returning NaN for path length.")
        return np.nan

    return np.mean(finite_distances)


def calculate_global_efficiency(adjacency_matrix: np.ndarray) -> float:
    """
    Calculate the global efficiency of the network.

    CRITICAL: Global Efficiency is calculated as the reciprocal of
    Characteristic Path Length to satisfy FR-003.

    Args:
        adjacency_matrix: Square matrix representing edge weights.

    Returns:
        Global efficiency (1.0 / characteristic_path_length).
        Returns 0.0 if path length is 0 or NaN.
    """
    path_length = calculate_characteristic_path_length(adjacency_matrix)

    if np.isnan(path_length) or path_length == 0.0:
        return 0.0

    return 1.0 / path_length


def calculate_local_efficiency(adjacency_matrix: np.ndarray) -> float:
    """
    Calculate the local efficiency of the network.

    CRITICAL: Local Efficiency is calculated as the reciprocal of
    Characteristic Path Length (of the neighborhood subgraph) to satisfy FR-003.

    For each node, we:
    1. Extract the subgraph of its neighbors
    2. Calculate the characteristic path length of that subgraph
    3. Take the reciprocal to get local efficiency for that node
    4. Average across all nodes

    Args:
        adjacency_matrix: Square matrix representing edge weights.

    Returns:
        Local efficiency (average of 1.0 / local_path_length across nodes).
    """
    n = adjacency_matrix.shape[0]
    local_efficiencies = []

    for i in range(n):
        # Find neighbors (nodes with non-zero connection to i)
        neighbors = np.where(adjacency_matrix[i, :] > 0)[0]

        if len(neighbors) < 2:
            # Cannot calculate path length with < 2 nodes
            local_efficiencies.append(0.0)
            continue

        # Create subgraph adjacency matrix for neighbors
        subgraph_matrix = adjacency_matrix[np.ix_(neighbors, neighbors)]

        # Calculate path length for subgraph
        subgraph_path_length = calculate_characteristic_path_length(subgraph_matrix)

        if np.isnan(subgraph_path_length) or subgraph_path_length == 0.0:
            local_efficiencies.append(0.0)
        else:
            local_efficiencies.append(1.0 / subgraph_path_length)

    if not local_efficiencies:
        return 0.0

    return np.mean(local_efficiencies)


def calculate_clustering_coefficient(adjacency_matrix: np.ndarray) -> float:
    """
    Calculate the average clustering coefficient of the network.

    The clustering coefficient for a node is the fraction of possible triangles
    that exist in its neighborhood.

    Args:
        adjacency_matrix: Square matrix representing edge weights (thresholded to binary).

    Returns:
        Average clustering coefficient across all nodes.
    """
    # Convert to binary adjacency (threshold non-zero as 1)
    binary_matrix = (adjacency_matrix > 0).astype(int)
    n = binary_matrix.shape[0]

    clustering_coeffs = []

    for i in range(n):
        neighbors = np.where(binary_matrix[i, :] == 1)[0]
        k = len(neighbors)

        if k < 2:
            clustering_coeffs.append(0.0)
            continue

        # Count edges between neighbors
        edges_between_neighbors = 0
        for j_idx in range(len(neighbors)):
            for l_idx in range(j_idx + 1, len(neighbors)):
                if binary_matrix[neighbors[j_idx], neighbors[l_idx]] == 1:
                    edges_between_neighbors += 1

        # Possible edges between k neighbors
        possible_edges = k * (k - 1) / 2

        if possible_edges > 0:
            clustering_coeffs.append(edges_between_neighbors / possible_edges)
        else:
            clustering_coeffs.append(0.0)

    return np.mean(clustering_coeffs)


def calculate_modularity(adjacency_matrix: np.ndarray, resolution: float = 1.0) -> float:
    """
    Calculate the modularity of the network using the Louvain algorithm.

    Modularity measures the strength of division of a network into modules (communities).

    Args:
        adjacency_matrix: Square matrix representing edge weights.
        resolution: Resolution parameter for the Louvain algorithm.

    Returns:
        Modularity value (typically between -1 and 1).
    """
    # Create a NetworkX graph from the adjacency matrix
    G = nx.from_numpy_array(adjacency_matrix)

    # Remove self-loops for community detection
    G.remove_edges_from(nx.selfloop_edges(G))

    # Use the Louvain community detection algorithm
    try:
        communities = nx.community.louvain_communities(G, resolution=resolution, seed=42)

        # Calculate modularity
        modularity = nx.community.modularity(G, communities)
        return modularity
    except Exception as e:
        logger.warning(f"Could not compute modularity: {e}. Returning 0.0.")
        return 0.0


def compute_all_metrics(connectivity_matrix: np.ndarray) -> Dict[str, float]:
    """
    Compute all graph-theoretical metrics for a given connectivity matrix.

    Args:
        connectivity_matrix: Square matrix representing edge weights (connectivity strengths).

    Returns:
        Dictionary containing:
        - global_efficiency
        - characteristic_path_length
        - local_efficiency
        - clustering_coefficient
        - modularity
    """
    metrics = {}

    # Calculate Characteristic Path Length first (needed for efficiency calculations)
    path_length = calculate_characteristic_path_length(connectivity_matrix)
    metrics['characteristic_path_length'] = path_length

    # Calculate efficiencies using the reciprocal of path length (FR-003)
    metrics['global_efficiency'] = calculate_global_efficiency(connectivity_matrix)
    metrics['local_efficiency'] = calculate_local_efficiency(connectivity_matrix)

    # Calculate other metrics
    metrics['clustering_coefficient'] = calculate_clustering_coefficient(connectivity_matrix)
    metrics['modularity'] = calculate_modularity(connectivity_matrix)

    return metrics


def process_subject_metrics(subject_id: str, connectivity_matrix: np.ndarray) -> Dict[str, Any]:
    """
    Process a single subject's connectivity matrix and compute all metrics.

    Args:
        subject_id: Identifier for the subject.
        connectivity_matrix: The connectivity matrix for the subject.

    Returns:
        Dictionary with subject_id and all computed metrics.
    """
    if connectivity_matrix is None or connectivity_matrix.size == 0:
        logger.warning(f"Empty connectivity matrix for subject {subject_id}")
        return {
            'subject_id': subject_id,
            'global_efficiency': np.nan,
            'characteristic_path_length': np.nan,
            'local_efficiency': np.nan,
            'clustering_coefficient': np.nan,
            'modularity': np.nan
        }

    # Validate matrix is square
    if connectivity_matrix.shape[0] != connectivity_matrix.shape[1]:
        raise ValueError(f"Connectivity matrix for {subject_id} is not square: {connectivity_matrix.shape}")

    metrics = compute_all_metrics(connectivity_matrix)
    metrics['subject_id'] = subject_id

    return metrics


def main():
    """
    Main entry point to process all connectivity matrices and generate network metrics.

    Reads connectivity matrices from data/processed/connectivity_matrices/
    and writes results to data/results/network_metrics.csv
    """
    config = get_config()
    input_dir = Path(config['paths']['processed_connectivity'])
    output_dir = Path(config['paths']['results'])
    output_file = output_dir / 'network_metrics.csv'

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Processing connectivity matrices from: {input_dir}")
    logger.info(f"Output will be written to: {output_file}")

    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory does not exist: {input_dir}")

    results = []
    matrix_files = list(input_dir.glob('*.npy'))

    if not matrix_files:
        logger.warning(f"No .npy files found in {input_dir}")
        return

    logger.info(f"Found {len(matrix_files)} connectivity matrices to process")

    for matrix_file in matrix_files:
        subject_id = matrix_file.stem
        logger.info(f"Processing: {subject_id}")

        try:
            connectivity_matrix = np.load(matrix_file)
            subject_metrics = process_subject_metrics(subject_id, connectivity_matrix)
            results.append(subject_metrics)
        except Exception as e:
            logger.error(f"Error processing {matrix_file}: {e}")
            # Still add a row with NaN values for this subject
            results.append({
                'subject_id': subject_id,
                'global_efficiency': np.nan,
                'characteristic_path_length': np.nan,
                'local_efficiency': np.nan,
                'clustering_coefficient': np.nan,
                'modularity': np.nan
            })

    # Write results to CSV
    import csv

    if results:
        fieldnames = ['subject_id', 'global_efficiency', 'characteristic_path_length',
                     'local_efficiency', 'clustering_coefficient', 'modularity']

        with open(output_file, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in results:
                writer.writerow(row)

        logger.info(f"Successfully wrote metrics for {len(results)} subjects to {output_file}")
    else:
        logger.warning("No results to write")


if __name__ == '__main__':
    main()
