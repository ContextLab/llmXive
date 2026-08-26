import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
import numpy as np
import networkx as nx
from config import get_config_summary

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def calculate_shortest_paths(adjacency_matrix: np.ndarray) -> np.ndarray:
    """
    Calculate the shortest path lengths between all pairs of nodes.
    
    Args:
        adjacency_matrix: NxN symmetric adjacency matrix (weighted or binary).
        
    Returns:
        NxN matrix of shortest path lengths. Infinite values indicate 
        disconnected nodes.
    """
    n = adjacency_matrix.shape[0]
    # Convert to NetworkX graph
    G = nx.from_numpy_array(adjacency_matrix)
    
    # Compute all-pairs shortest paths
    try:
        lengths = dict(nx.all_pairs_dijkstra_path_length(G))
    except nx.NetworkXError:
        # Fallback for disconnected components if needed, though dijkstra handles it
        lengths = dict(nx.all_pairs_shortest_path_length(G))
        
    # Construct matrix
    path_matrix = np.full((n, n), np.inf)
    for i in range(n):
        for j, dist in lengths[i].items():
            path_matrix[i, j] = dist
            
    # Distance to self is 0
    np.fill_diagonal(path_matrix, 0)
    
    return path_matrix

def calculate_characteristic_path_length(adjacency_matrix: np.ndarray) -> float:
    """
    Calculate Characteristic Path Length (L).
    Defined as the average of the shortest path lengths between all pairs of nodes.
    Only finite paths are considered (disconnected pairs are excluded from the average).
    
    Args:
        adjacency_matrix: NxN symmetric adjacency matrix.
        
    Returns:
        Characteristic path length (float). Returns np.inf if no finite paths exist.
    """
    path_matrix = calculate_shortest_paths(adjacency_matrix)
    
    # Exclude diagonal (self) and infinite (disconnected) values
    finite_paths = path_matrix[np.isfinite(path_matrix) & (path_matrix > 0)]
    
    if len(finite_paths) == 0:
        logger.warning("No finite paths found between distinct nodes.")
        return np.inf
        
    return float(np.mean(finite_paths))

def calculate_global_efficiency(adjacency_matrix: np.ndarray) -> float:
    """
    Calculate Global Efficiency (E_glob).
    Defined as the average of the inverse shortest path lengths.
    E_glob = (1/(N*(N-1))) * sum(1/d_ij) for i != j
    
    This is NOT simply 1 / Characteristic Path Length.
    It handles disconnected nodes gracefully (1/inf = 0).
    
    Args:
        adjacency_matrix: NxN symmetric adjacency matrix.
        
    Returns:
        Global efficiency (float).
    """
    path_matrix = calculate_shortest_paths(adjacency_matrix)
    
    n = path_matrix.shape[0]
    if n <= 1:
        return 0.0
        
    # Inverse path lengths (1/inf is 0)
    inv_paths = np.zeros_like(path_matrix)
    finite_mask = np.isfinite(path_matrix) & (path_matrix > 0)
    inv_paths[finite_mask] = 1.0 / path_matrix[finite_mask]
    
    # Sum over all pairs i != j
    # Set diagonal to 0 to exclude self-loops
    np.fill_diagonal(inv_paths, 0)
    
    total_inv = np.sum(inv_paths)
    norm_factor = n * (n - 1)
    
    if norm_factor == 0:
        return 0.0
        
    return float(total_inv / norm_factor)

def calculate_local_efficiency(adjacency_matrix: np.ndarray) -> float:
    """
    Calculate Local Efficiency (E_loc).
    Defined as the average of the global efficiencies of the subgraphs 
    defined by the neighbors of each node.
    
    E_loc = (1/N) * sum(E_glob(G_i)) where G_i is the subgraph of neighbors of node i.
    
    CRITICAL: This must be calculated via subgraph path lengths, NOT as 
    the inverse of the global characteristic path length.
    
    Args:
        adjacency_matrix: NxN symmetric adjacency matrix.
        
    Returns:
        Local efficiency (float).
    """
    n = adjacency_matrix.shape[0]
    if n <= 1:
        return 0.0
        
    local_efficiencies = []
    
    # Create a graph object once for neighbor extraction
    G = nx.from_numpy_array(adjacency_matrix)
    
    for i in range(n):
        # Get neighbors of node i
        neighbors = list(G.neighbors(i))
        
        if len(neighbors) < 2:
            # Cannot form a connected subgraph with < 2 nodes
            # Local efficiency is 0 for isolated or leaf nodes in this context
            # Or technically undefined, we treat as 0
            local_efficiencies.append(0.0)
            continue
        
        # Create subgraph induced by neighbors
        subgraph = G.subgraph(neighbors)
        
        # Calculate global efficiency of the subgraph
        # We need the adjacency matrix of the subgraph
        sub_adj = nx.to_numpy_array(subgraph, nodelist=sorted(neighbors))
        
        # Calculate global efficiency for this subgraph
        # Reusing the logic but on the smaller matrix
        sub_path_matrix = calculate_shortest_paths(sub_adj)
        m = sub_adj.shape[0]
        
        if m <= 1:
            local_efficiencies.append(0.0)
            continue
            
        inv_paths = np.zeros_like(sub_path_matrix)
        finite_mask = np.isfinite(sub_path_matrix) & (sub_path_matrix > 0)
        inv_paths[finite_mask] = 1.0 / sub_path_matrix[finite_mask]
        
        np.fill_diagonal(inv_paths, 0)
        total_inv = np.sum(inv_paths)
        norm_factor = m * (m - 1)
        
        if norm_factor == 0:
            local_efficiencies.append(0.0)
        else:
            local_efficiencies.append(total_inv / norm_factor)
    
    return float(np.mean(local_efficiencies))

def calculate_clustering_coefficient(adjacency_matrix: np.ndarray) -> float:
    """
    Calculate the average Clustering Coefficient (C).
    C_i = (2 * number of triangles) / (k_i * (k_i - 1))
    C = (1/N) * sum(C_i)
    
    Args:
        adjacency_matrix: NxN symmetric adjacency matrix (binary or weighted).
        For weighted networks, we use the standard binary clustering coefficient
        based on the presence of edges.
        
    Returns:
        Average clustering coefficient (float).
    """
    # Convert to binary adjacency matrix for clustering coefficient calculation
    binary_adj = (adjacency_matrix > 0).astype(float)
    G = nx.from_numpy_array(binary_adj)
    
    # NetworkX provides local clustering coefficients
    local_coeffs = nx.clustering(G)
    
    # Average them
    if not local_coeffs:
        return 0.0
        
    return float(np.mean(list(local_coeffs.values())))

def calculate_modularity(adjacency_matrix: np.ndarray) -> float:
    """
    Calculate Modularity (Q).
    Measures the strength of division of a network into modules (communities).
    Uses the Louvain method for community detection and then calculates Q.
    
    Args:
        adjacency_matrix: NxN symmetric adjacency matrix.
        
    Returns:
        Modularity value (float). Returns -1.0 if community detection fails.
    """
    G = nx.from_numpy_array(adjacency_matrix)
    
    try:
        # Use Louvain community detection
        import community
        partitions = community.best_partition(G)
        
        # Calculate modularity
        modularity = community.modularity(partitions, G)
        return float(modularity)
    except ImportError:
        logger.warning("python-louvain not installed. Using alternative method.")
        try:
            # Fallback: use NetworkX's greedy modularity communities
            communities = nx.community.greedy_modularity_communities(G)
            modularity = nx.community.modularity(G, communities)
            return float(modularity)
        except Exception as e:
            logger.error(f"Modularity calculation failed: {e}")
            return -1.0
    except Exception as e:
        logger.error(f"Community detection failed: {e}")
        return -1.0

def compute_all_metrics(adjacency_matrix: np.ndarray) -> Dict[str, float]:
    """
    Compute all graph-theoretical metrics for a given adjacency matrix.
    
    Args:
        adjacency_matrix: NxN symmetric adjacency matrix.
        
    Returns:
        Dictionary containing:
        - characteristic_path_length
        - global_efficiency
        - local_efficiency
        - clustering_coefficient
        - modularity
    """
    # Ensure matrix is symmetric and handle potential NaNs
    if np.any(np.isnan(adjacency_matrix)):
        logger.warning("NaN values detected in adjacency matrix. Replacing with 0.")
        adjacency_matrix = np.nan_to_num(adjacency_matrix, nan=0.0)
        
    # Ensure symmetry
    adjacency_matrix = (adjacency_matrix + adjacency_matrix.T) / 2.0
    
    metrics = {
        "characteristic_path_length": calculate_characteristic_path_length(adjacency_matrix),
        "global_efficiency": calculate_global_efficiency(adjacency_matrix),
        "local_efficiency": calculate_local_efficiency(adjacency_matrix),
        "clustering_coefficient": calculate_clustering_coefficient(adjacency_matrix),
        "modularity": calculate_modularity(adjacency_matrix)
    }
    
    return metrics

def process_subject_metrics(subject_id: str, adjacency_matrix: np.ndarray, output_dir: Path) -> Dict[str, Any]:
    """
    Process metrics for a single subject and save results.
    
    Args:
        subject_id: Unique identifier for the subject.
        adjacency_matrix: NxN connectivity matrix.
        output_dir: Directory to save results.
        
    Returns:
        Dictionary with computed metrics and status.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        metrics = compute_all_metrics(adjacency_matrix)
        metrics["subject_id"] = subject_id
        
        # Save individual subject metrics
        output_file = output_dir / f"{subject_id}_metrics.json"
        with open(output_file, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        logger.info(f"Computed metrics for subject {subject_id}")
        return {"status": "success", "metrics": metrics, "file": str(output_file)}
        
    except Exception as e:
        logger.error(f"Failed to compute metrics for subject {subject_id}: {e}")
        return {"status": "failed", "error": str(e), "subject_id": subject_id}

def main():
    """
    Main entry point to process all connectivity matrices and compute network metrics.
    Reads from data/processed/connectivity_matrices/ and writes to data/results/network_metrics.csv
    """
    config = get_config_summary()
    connectivity_dir = Path(config["paths"]["processed"]) / "connectivity_matrices"
    output_dir = Path(config["paths"]["results"])
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / "network_metrics.csv"
    
    if not connectivity_dir.exists():
        logger.error(f"Connectivity directory not found: {connectivity_dir}")
        # Create empty file with headers to indicate failure state
        pd.DataFrame(columns=["subject_id", "characteristic_path_length", "global_efficiency", 
                              "local_efficiency", "clustering_coefficient", "modularity"]).to_csv(output_file, index=False)
        return
    
    import pandas as pd
    results = []
    
    # Process each subject
    for conn_file in sorted(connectivity_dir.glob("*.npy")):
        subject_id = conn_file.stem
        try:
            adj_matrix = np.load(conn_file)
            metrics = compute_all_metrics(adj_matrix)
            metrics["subject_id"] = subject_id
            results.append(metrics)
            logger.info(f"Processed {subject_id}")
        except Exception as e:
            logger.error(f"Error processing {conn_file}: {e}")
            # Append row with NaNs for failed subjects
            failed_row = {
                "subject_id": subject_id,
                "characteristic_path_length": np.nan,
                "global_efficiency": np.nan,
                "local_efficiency": np.nan,
                "clustering_coefficient": np.nan,
                "modularity": np.nan
            }
            results.append(failed_row)
    
    if not results:
        logger.warning("No results to save.")
        pd.DataFrame(columns=["subject_id", "characteristic_path_length", "global_efficiency", 
                              "local_efficiency", "clustering_coefficient", "modularity"]).to_csv(output_file, index=False)
        return
    
    df = pd.DataFrame(results)
    df.to_csv(output_file, index=False)
    logger.info(f"Saved metrics to {output_file}")

if __name__ == "__main__":
    main()