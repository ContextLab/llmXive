"""
Graph metrics calculation module for brain network analysis.

Calculates global efficiency, modularity, participation coefficient,
and network-specific metrics using bctpy and networkx.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
import numpy as np
import networkx as nx
from bct import efficiency_wei, modularity_gh, participation_coef, community_louvain
import warnings

from src.utils.logging import get_logger, log_preprocessing_step

# Suppress bct warnings about negative weights if needed
warnings.filterwarnings("ignore", category=UserWarning)

logger = get_logger(__name__)


def validate_connectivity_matrix(matrix: np.ndarray, tol: float = 1e-6) -> bool:
    """
    Validate that a connectivity matrix is symmetric and has valid values.
    
    Args:
        matrix: 2D numpy array representing the connectivity matrix
        tol: Tolerance for symmetry check
        
    Returns:
        True if valid, raises ValueError otherwise
        
    Raises:
        ValueError: If matrix is not symmetric, not 2D, or contains invalid values
    """
    if matrix.ndim != 2:
        raise ValueError(f"Matrix must be 2D, got {matrix.ndim}D")
    
    if matrix.shape[0] != matrix.shape[1]:
        raise ValueError(f"Matrix must be square, got shape {matrix.shape}")
    
    if not np.allclose(matrix, matrix.T, atol=tol):
        raise ValueError("Matrix is not symmetric")
    
    if not np.all(np.abs(matrix) <= 1 + tol):
        raise ValueError("Matrix values must be in range [-1, 1]")
    
    if not np.allclose(np.diag(matrix), 1.0, atol=tol):
        logger.warning("Diagonal values are not exactly 1.0, normalizing...")
        # Normalize diagonal to 1.0
        np.fill_diagonal(matrix, 1.0)
    
    return True


def calculate_global_efficiency(matrix: np.ndarray) -> float:
    """
    Calculate global efficiency of the network.
    
    Global efficiency is the average inverse shortest path length in the network.
    Higher values indicate more efficient information transfer.
    
    Args:
        matrix: Symmetric connectivity matrix (N x N)
        
    Returns:
        Global efficiency value (float)
    """
    validate_connectivity_matrix(matrix)
    
    try:
        # bct efficiency_wei expects a weighted adjacency matrix
        # Returns a single scalar for global efficiency
        eff = efficiency_wei(matrix)
        return float(eff)
    except Exception as e:
        logger.error(f"Error calculating global efficiency: {e}")
        raise


def calculate_modularity(matrix: np.ndarray, resolution: float = 1.0) -> Tuple[float, List[int]]:
    """
    Calculate modularity and community structure using Louvain algorithm.
    
    Modularity measures the strength of division of a network into modules
    (communities). Higher values indicate stronger community structure.
    
    Args:
        matrix: Symmetric connectivity matrix (N x N)
        resolution: Resolution parameter for Louvain algorithm
        
    Returns:
        Tuple of (modularity_score, community_assignments)
        - modularity_score: float
        - community_assignments: List of community labels for each node
    """
    validate_connectivity_matrix(matrix)
    
    try:
        # Use bct's modularity_gh for weighted graphs
        # Returns (Q, communities)
        # Note: bct modularity_gh returns a tuple (Q, communities)
        # communities is a list of lists, each inner list is a module
        # We need to convert to node assignments
        
        # Alternative: Use networkx for more straightforward community detection
        G = nx.from_numpy_array(matrix)
        communities = community_louvain.best_partition(G, resolution=resolution)
        
        # Calculate modularity score
        modularity = nx.community.modularity(G, communities)
        
        # Convert community dict to list of assignments
        n_nodes = len(communities)
        assignments = [communities[i] for i in range(n_nodes)]
        
        return float(modularity), assignments
    except Exception as e:
        logger.error(f"Error calculating modularity: {e}")
        raise


def calculate_participation_coefficient(matrix: np.ndarray, communities: List[int]) -> np.ndarray:
    """
    Calculate participation coefficient for each node.
    
    The participation coefficient measures how evenly a node's connections
    are distributed across different communities. High values indicate
    nodes that connect to many communities (hubs).
    
    Args:
        matrix: Symmetric connectivity matrix (N x N)
        communities: List of community assignments for each node
        
    Returns:
        Array of participation coefficients (N,)
    """
    validate_connectivity_matrix(matrix)
    
    if len(communities) != matrix.shape[0]:
        raise ValueError("Community assignments length must match matrix size")
    
    try:
        # Use bct participation_coef
        # Input: adjacency matrix, community vector
        # Output: participation coefficient for each node
        pc = participation_coef(matrix, np.array(communities))
        return pc
    except Exception as e:
        logger.error(f"Error calculating participation coefficient: {e}")
        raise


def calculate_network_specific_efficiencies(
    matrix: np.ndarray,
    network_labels: np.ndarray,
    network_names: List[str]
) -> Dict[str, float]:
    """
    Calculate efficiency for specific networks (DMN, Salience, Visual, etc.).
    
    Args:
        matrix: Symmetric connectivity matrix (N x N)
        network_labels: Array of network assignments for each node
        network_names: List of network names to calculate efficiency for
        
    Returns:
        Dictionary mapping network name to efficiency value
    """
    validate_connectivity_matrix(matrix)
    
    if len(network_labels) != matrix.shape[0]:
        raise ValueError("Network labels length must match matrix size")
    
    results = {}
    
    for net_name in network_names:
        # Get indices of nodes belonging to this network
        net_indices = np.where(network_labels == net_name)[0]
        
        if len(net_indices) < 2:
            logger.warning(f"Network {net_name} has fewer than 2 nodes, skipping")
            results[net_name] = 0.0
            continue
        
        # Extract submatrix for this network
        submatrix = matrix[np.ix_(net_indices, net_indices)]
        
        # Calculate efficiency for this subnetwork
        try:
            eff = efficiency_wei(submatrix)
            results[net_name] = float(eff)
        except Exception as e:
            logger.warning(f"Could not calculate efficiency for {net_name}: {e}")
            results[net_name] = 0.0
    
    return results


def extract_edge_strengths(matrix: np.ndarray) -> Dict[str, Any]:
    """
    Extract all edge-level connectivity strengths from the matrix.
    
    Args:
        matrix: Symmetric connectivity matrix (N x N)
        
    Returns:
        Dictionary containing edge strengths in a serializable format
    """
    validate_connectivity_matrix(matrix)
    
    n = matrix.shape[0]
    edges = []
    
    # Extract upper triangle (including diagonal) to avoid duplicates
    for i in range(n):
        for j in range(i, n):
            edges.append({
                "node_i": int(i),
                "node_j": int(j),
                "strength": float(matrix[i, j])
            })
    
    return {
        "n_nodes": n,
        "n_edges": len(edges),
        "edges": edges
    }


def compute_all_metrics(
    matrix: np.ndarray,
    network_labels: Optional[np.ndarray] = None,
    network_names: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Compute all graph metrics for a given connectivity matrix.
    
    Args:
        matrix: Symmetric connectivity matrix (N x N)
        network_labels: Optional array of network assignments for each node
        network_names: Optional list of network names to calculate specific efficiencies
        
    Returns:
        Dictionary containing all computed metrics
    """
    validate_connectivity_matrix(matrix)
    
    metrics = {}
    
    # Global metrics
    logger.info("Calculating global efficiency...")
    metrics["global_efficiency"] = calculate_global_efficiency(matrix)
    
    logger.info("Calculating modularity and community structure...")
    modularity, communities = calculate_modularity(matrix)
    metrics["modularity"] = modularity
    metrics["community_assignments"] = communities
    
    # Participation coefficient
    logger.info("Calculating participation coefficient...")
    pc = calculate_participation_coefficient(matrix, communities)
    metrics["participation_coefficient"] = pc.tolist()
    
    # Network-specific efficiencies
    if network_labels is not None and network_names is not None:
        logger.info("Calculating network-specific efficiencies...")
        net_efficiencies = calculate_network_specific_efficiencies(
            matrix, network_labels, network_names
        )
        metrics["network_efficiency"] = net_efficiencies
    
    # Edge-level strengths
    logger.info("Extracting edge-level strengths...")
    edge_data = extract_edge_strengths(matrix)
    metrics["edge_strength"] = edge_data["edges"]
    
    return metrics


def save_metrics_to_json(metrics: Dict[str, Any], output_path: Path) -> None:
    """
    Save computed metrics to a JSON file.
    
    Args:
        metrics: Dictionary of computed metrics
        output_path: Path to output JSON file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Metrics saved to {output_path}")


def main():
    """
    Main entry point for graph metrics calculation.
    
    This function is designed to be called from a script that loads
    connectivity matrices and computes graph metrics.
    
    Expected usage:
        python -m src.analysis.graph_metrics --input data/connectivity/subject_001.json \
                                             --output data/metrics/subject_001.json
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Calculate graph metrics from connectivity matrices")
    parser.add_argument("--input", "-i", required=True, help="Input connectivity matrix JSON file")
    parser.add_argument("--output", "-o", required=True, help="Output metrics JSON file")
    parser.add_argument("--networks", "-n", nargs="+", default=None, help="Network names to analyze")
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    # Load connectivity matrix
    logger.info(f"Loading connectivity matrix from {input_path}")
    with open(input_path, 'r') as f:
        data = json.load(f)
    
    matrix = np.array(data["connectivity_matrix"])
    n_nodes = matrix.shape[0]
    
    logger.info(f"Loaded matrix of shape {matrix.shape}")
    
    # Load network labels if available
    network_labels = None
    network_names = args.networks
    
    # Try to load Schaefer atlas labels if not provided
    if network_labels is None:
        try:
            from src.analysis.connectivity import load_schaefer_atlas
            atlas_data = load_schaefer_atlas(n_nodes)
            network_labels = atlas_data.get("network_labels")
            if network_names is None:
                network_names = atlas_data.get("network_names")
        except Exception as e:
            logger.warning(f"Could not load Schaefer atlas: {e}. Skipping network-specific metrics.")
            network_labels = None
            network_names = None
    
    # Compute metrics
    logger.info("Computing graph metrics...")
    metrics = compute_all_metrics(matrix, network_labels, network_names)
    
    # Save results
    save_metrics_to_json(metrics, output_path)
    
    logger.info("Graph metrics calculation complete")


if __name__ == "__main__":
    main()
