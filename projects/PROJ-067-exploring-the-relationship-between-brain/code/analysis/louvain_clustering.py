"""
Louvain Clustering Module for Dynamic Functional Connectivity.

Implements community detection on time-varying connectivity matrices
using the Louvain algorithm (via python-louvain).
"""

import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union

import numpy as np
import networkx as nx
from community import community_louvain

# Import config for window parameters if needed, though task focuses on clustering logic
try:
    from utils.config import get_config
except ImportError:
    # Fallback if running in isolation or path issue
    def get_config():
        return {"window_size": 30, "step_size": 10}

logger = logging.getLogger(__name__)

def run_louvain_clustering(
    correlation_matrices: np.ndarray,
    resolution: float = 1.0,
    random_state: int = 42
) -> np.ndarray:
    """
    Runs Louvain clustering on a sequence of correlation matrices.

    Args:
        correlation_matrices: Array of shape (n_windows, n_nodes, n_nodes)
            containing correlation matrices for each time window.
        resolution: Resolution parameter for the Louvain algorithm.
            Higher values lead to more communities.
        random_state: Random seed for reproducibility.

    Returns:
        communities: Array of shape (n_windows, n_nodes) containing
            the community assignment for each node in each window.
            Community IDs are integers starting from 0.
    """
    n_windows, n_nodes, _ = correlation_matrices.shape
    logger.info(f"Running Louvain clustering on {n_windows} windows with {n_nodes} nodes.")

    communities = np.zeros((n_windows, n_nodes), dtype=int)

    for w_idx in range(n_windows):
        # Extract the current window's connectivity matrix
        conn_matrix = correlation_matrices[w_idx]

        # Ensure symmetry and zero diagonal for graph construction
        # (Correlation matrices should already be symmetric, but we enforce it)
        conn_matrix = (conn_matrix + conn_matrix.T) / 2.0
        np.fill_diagonal(conn_matrix, 0.0)

        # Thresholding: Keep only positive correlations to ensure a valid graph
        # (Negative edges are often excluded in standard Louvain implementations
        # unless the algorithm supports signed graphs, which python-louvain does not directly)
        # We use a small threshold to avoid numerical noise, but keep all positive values as weights.
        # Alternatively, we could threshold by a percentile, but the task implies using the matrix directly.
        # Let's keep all positive correlations as edge weights.
        adj_matrix = np.maximum(conn_matrix, 0.0)

        # Construct NetworkX graph
        G = nx.from_numpy_array(adj_matrix)

        # Run Louvain algorithm
        # partition is a dict: {node_id: community_id}
        try:
            partition = community_louvain.best_partition(
                G,
                weight='weight',
                resolution=resolution,
                random_state=random_state + w_idx  # Slight variation per window if needed, or fixed
            )
        except Exception as e:
            # Fallback for disconnected graphs or other issues
            logger.warning(f"Clustering failed for window {w_idx}: {e}. Assigning all to community 0.")
            partition = {i: 0 for i in range(n_nodes)}

        # Convert partition dict to array
        # Ensure all nodes 0..n_nodes-1 are present
        for node_id in range(n_nodes):
            if node_id in partition:
                communities[w_idx, node_id] = partition[node_id]
            else:
                # Should not happen if graph has all nodes, but safety check
                communities[w_idx, node_id] = 0

        if w_idx % 10 == 0:
            logger.debug(f"Processed window {w_idx}/{n_windows}")

    return communities

def calculate_state_transitions(
    communities: np.ndarray
) -> np.ndarray:
    """
    Calculates the number of community state transitions for each node.

    Args:
        communities: Array of shape (n_windows, n_nodes).

    Returns:
        transitions: Array of shape (n_nodes) containing the count of
            state changes for each node across windows.
    """
    n_windows, n_nodes = communities.shape
    transitions = np.zeros(n_nodes, dtype=int)

    for node_id in range(n_nodes):
        node_sequence = communities[:, node_id]
        # Count changes: compare current window with previous
        # Transitions occur where community ID changes
        changes = np.diff(node_sequence) != 0
        transitions[node_id] = np.sum(changes)

    return transitions

def calculate_flexibility(
    communities: np.ndarray,
    time_window_duration: float = 30.0  # seconds or TRs depending on data
) -> np.ndarray:
    """
    Calculates flexibility (transitions per unit time) for each node.

    Args:
        communities: Array of shape (n_windows, n_nodes).
        time_window_duration: Duration of a single window in time units.

    Returns:
        flexibility: Array of shape (n_nodes) with flexibility values.
    """
    transitions = calculate_state_transitions(communities)
    # Total time = (n_windows - 1) * window_duration? Or just n_windows?
    # Flexibility is usually transitions / (total_time - window_duration) or similar.
    # Standard definition: number of times a node changes community / (total time - duration of first window)
    # Let's normalize by the number of possible transitions (n_windows - 1)
    # Then multiply by 1/window_duration if we want per-unit-time, but usually it's just per window or normalized.
    # The task asks for "state transitions per unit time".
    # Total duration of the dynamic process is (n_windows * window_duration).
    # However, transitions happen *between* windows. There are n_windows - 1 intervals.
    # Let's calculate transitions per interval, then scale by 1/window_duration.

    n_windows = communities.shape[0]
    if n_windows <= 1:
        return np.zeros(communities.shape[1])

    # Flexibility = Transitions / (Number of intervals)
    # But "per unit time" implies dividing by the duration of those intervals.
    # Let's assume the standard metric: Flexibility = (Number of changes) / (Total Time - Window Duration)
    # Or simply: Changes / (N_windows - 1) * (1 / window_duration)
    
    # Simpler interpretation often used: Changes / (N_windows - 1)
    # If "per unit time" is strict:
    flexibility = transitions / (n_windows - 1)
    if time_window_duration > 0:
        flexibility = flexibility / time_window_duration
    
    return flexibility

def process_subject_louvain(
    correlation_matrices: np.ndarray,
    output_dir: str,
    subject_id: str,
    resolution: float = 1.0
) -> Dict[str, Any]:
    """
    Orchestrates Louvain clustering and metric calculation for a subject.

    Args:
        correlation_matrices: Precomputed sliding window correlations (n_windows, n_nodes, n_nodes).
        output_dir: Directory to save results.
        subject_id: Identifier for the subject.
        resolution: Louvain resolution parameter.

    Returns:
        Dictionary containing flexibility and transition counts.
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    results = {}

    # Run Clustering
    communities = run_louvain_clustering(correlation_matrices, resolution=resolution)

    # Calculate Transitions
    transitions = calculate_state_transitions(communities)

    # Calculate Flexibility
    config = get_config()
    window_size = config.get("window_size", 30) # Assuming this is in TRs or seconds
    flexibility = calculate_flexibility(communities, time_window_duration=window_size)

    # Save Community Partitions (Optional but useful for debugging)
    # Save as JSON or CSV? JSON is easier for nested structures.
    # We'll save the full partition matrix for verification.
    partition_path = Path(output_dir) / f"{subject_id}_partitions.npy"
    np.save(str(partition_path), communities)
    logger.info(f"Saved community partitions to {partition_path}")

    # Save Summary Metrics
    results["subject_id"] = subject_id
    results["transitions"] = transitions.tolist()
    results["flexibility"] = flexibility.tolist()
    results["n_windows"] = len(communities)
    results["resolution"] = resolution

    # Save to JSON
    metrics_path = Path(output_dir) / f"{subject_id}_louvain_metrics.json"
    with open(metrics_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Saved Louvain metrics to {metrics_path}")

    return results

def main():
    """
    Entry point for running Louvain clustering on preprocessed data.
    This function expects correlation matrices to be available (from T027).
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Example usage simulation (In real pipeline, this would be called by process_subject in metrics.py)
    # Since T028 is a module implementation, we ensure it's callable.
    logger.info("Louvain Clustering module loaded successfully.")
    logger.info("To run: call process_subject_louvain(correlation_matrices, output_dir, subject_id)")

if __name__ == "__main__":
    main()