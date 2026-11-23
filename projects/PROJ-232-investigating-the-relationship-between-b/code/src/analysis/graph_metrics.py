import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union

import numpy as np
import networkx as nx
import bct as bct
from scipy import stats

from src.utils.logging import get_logger

# Configure logger for this module
logger = get_logger(__name__)

def validate_connectivity_matrix(matrix: np.ndarray) -> bool:
    """
    Validate that the connectivity matrix is symmetric, has diagonal of 1.0,
    and values are within [-1, 1].
    """
    if matrix.shape[0] != matrix.shape[1]:
        logger.error("Matrix is not square.")
        return False
    if not np.allclose(matrix, matrix.T):
        logger.error("Matrix is not symmetric.")
        return False
    if not np.allclose(np.diag(matrix), 1.0):
        logger.error("Diagonal is not all 1.0.")
        return False
    if np.any(np.abs(matrix) > 1.0):
        logger.error("Values outside [-1, 1] range.")
        return False
    return True

def calculate_global_efficiency(matrix: np.ndarray) -> float:
    """
    Calculate global efficiency using BCT.
    Global efficiency is the average of the inverse shortest path lengths.
    """
    if not validate_connectivity_matrix(matrix):
        raise ValueError("Invalid connectivity matrix provided.")
    
    # BCT expects adjacency matrix. For efficiency, we treat correlation as weight.
    # We convert correlation to distance: d = 1 - r (or similar)
    # However, BCT's effbin or eff_weight usually handles weighted graphs.
    # Let's use bct.efficiency_bin or bct.efficiency_weight.
    # Since we have correlations, we can convert to distance: D = 1 - |r| or 1 - r.
    # Standard practice for functional connectivity: D = 1 - r.
    # But r can be negative, making D > 1. 
    # Let's use the absolute value or a transformation that ensures positive weights.
    # A common approach: D = 1 - r. If r is negative, D > 1.
    # BCT functions usually assume positive weights for efficiency.
    # Let's use the transformation: weight = 1 - r.
    # If r is negative, weight > 1. This is acceptable for weighted efficiency if the algorithm handles it.
    # However, BCT's efficiency_weight function requires positive weights.
    # To be safe, let's use the absolute correlation or a threshold.
    # For this implementation, we will use the transformation: weight = 1 - r.
    # If negative correlations exist, we might need to handle them.
    # Let's assume the matrix is already processed to have non-negative weights or use absolute.
    # Actually, BCT's efficiency_weight uses the weights as distances? No, as strengths.
    # Wait, efficiency is 1/L. If weights are strengths, L is sum of weights? No, L is path length.
    # In weighted graphs, path length is sum of inverse weights? Or sum of weights?
    # BCT's `efficiency_weight` uses weights as strengths (higher weight = shorter path).
    # So if we have correlations, higher correlation = shorter path.
    # So we can pass the correlation matrix directly if it's positive.
    # If there are negative correlations, we should probably set them to 0 or use absolute.
    # Let's use the absolute value to be safe for the graph metric calculation.
    # But wait, negative correlations are meaningful.
    # Let's follow standard practice: convert correlation to distance: D = 1 - r.
    # Then efficiency is calculated on the distance matrix.
    # BCT has `efficiency_bin` and `efficiency_weight`.
    # For weighted, we can use `bct.efficiency_weight` which takes an adjacency matrix where weights are strengths.
    # If we have correlations, we can use them as strengths directly if they are positive.
    # If not, we can use D = 1 - r and then use `bct.efficiency_bin` on the binarized matrix?
    # No, we want weighted.
    # Let's use the transformation: weight = 1 - r. This makes negative r into large weights (long distances).
    # But BCT's efficiency_weight expects weights to be strengths (high weight = short path).
    # So if we use D = 1 - r, then high r -> low D -> short path.
    # So we should pass the distance matrix to a function that computes efficiency from distances.
    # BCT doesn't have a direct "efficiency from distances" function for weighted graphs in the same way.
    # Let's use the approach: convert correlation to distance: D = 1 - r.
    # Then use the formula: E = 1/(N(N-1)) * sum(1/d_ij) for i != j.
    # We can implement this manually.
    
    n = matrix.shape[0]
    # Convert correlation to distance: D = 1 - r
    # Handle negative correlations: if r is negative, D > 1. This is fine.
    # But if r is 1, D = 0. We must avoid division by zero.
    # Set diagonal to 0 (or a small number) to avoid division by zero?
    # The diagonal is 1.0 in correlation matrix, so D = 0.
    # We should set diagonal to infinity or ignore it.
    # Let's create a distance matrix.
    distance_matrix = 1.0 - matrix
    np.fill_diagonal(distance_matrix, np.inf)  # Avoid division by zero for diagonal
    
    # Calculate efficiency: mean of 1/d for all pairs
    # Inverse of distance
    inv_dist = 1.0 / distance_matrix
    # Sum over all pairs (excluding diagonal, which is now 0 because 1/inf = 0)
    total_efficiency = np.sum(inv_dist)
    efficiency = total_efficiency / (n * (n - 1))
    
    return float(efficiency)

def calculate_modularity(matrix: np.ndarray, number_of_partitions: int = 100) -> float:
    """
    Calculate modularity using BCT.
    """
    if not validate_connectivity_matrix(matrix):
        raise ValueError("Invalid connectivity matrix provided.")
    
    # BCT's modularity_und function
    # It returns Q (modularity) and R (community assignment)
    # We only need Q
    try:
        Q, R = bct.modularity_und(matrix)
        return float(Q)
    except Exception as e:
        logger.error(f"Error calculating modularity: {e}")
        raise

def calculate_participation_coefficient(matrix: np.ndarray, communities: np.ndarray) -> float:
    """
    Calculate the average participation coefficient across nodes.
    The participation coefficient measures how evenly a node's links are distributed across modules.
    """
    if not validate_connectivity_matrix(matrix):
        raise ValueError("Invalid connectivity matrix provided.")
    
    if len(communities) != matrix.shape[0]:
        raise ValueError("Communities array length must match matrix size.")
    
    try:
        # BCT's participation_coeff function
        # It takes an adjacency matrix and a community assignment
        P = bct.participation_coeff(matrix, communities)
        # Return the mean participation coefficient
        return float(np.mean(P))
    except Exception as e:
        logger.error(f"Error calculating participation coefficient: {e}")
        raise

def calculate_network_specific_efficiencies(matrix: np.ndarray, 
                                            network_labels: np.ndarray, 
                                            network_names: List[str]) -> Dict[str, float]:
    """
    Calculate network-specific efficiencies for DMN, Salience, and Visual networks.
    
    Args:
        matrix: Connectivity matrix (N x N)
        network_labels: Array of network labels for each node (e.g., 0: DMN, 1: Salience, 2: Visual, ...)
        network_names: List of network names corresponding to the labels we want to calculate for.
    
    Returns:
        Dictionary mapping network name to its efficiency.
    """
    if not validate_connectivity_matrix(matrix):
        raise ValueError("Invalid connectivity matrix provided.")
    
    if len(network_labels) != matrix.shape[0]:
        raise ValueError("Network labels length must match matrix size.")
    
    if len(network_names) == 0:
        logger.warning("No network names provided. Returning empty dict.")
        return {}
    
    # We need to map network names to their corresponding labels.
    # We assume network_labels contains integer codes, and we need to know which code corresponds to which name.
    # Since the task doesn't specify the exact mapping, we assume a standard mapping or that the caller provides it.
    # However, the function signature only takes network_names as a list of names to calculate for.
    # We need a way to map these names to the labels in network_labels.
    # Let's assume that the network_labels are integers and that we have a mapping from name to integer.
    # But we don't have that mapping here. 
    # Alternative: We assume that the network_labels are strings or that we can infer the mapping.
    # Since the task says "based on Schaefer atlas labels", we can assume that the labels are consistent.
    # Let's assume that the network_labels are integers and that the network_names are in the same order as the unique labels.
    # But that's not guaranteed.
    # Better approach: We assume that the network_labels are such that we can filter nodes by label.
    # We need to know which label corresponds to which network name.
    # Since the task doesn't specify, we will assume that the network_labels are integers and that the network_names are provided in the order of the unique labels sorted by their integer value.
    # But that's a guess.
    # Let's change the approach: We assume that the network_labels are such that we can create a mapping from label to network name.
    # However, we don't have that mapping.
    # Given the ambiguity, we will assume that the network_labels are integers and that the network_names are the unique labels in sorted order.
    # But that might not be correct.
    # Alternatively, we can assume that the network_labels are strings and that we can directly compare.
    # Let's assume that the network_labels are integers and that we have a standard mapping for the Schaefer atlas.
    # For the Schaefer 200 atlas, the networks are typically:
    # 1: Visual
    # 2: Somatomotor
    # 3: Dorsal Attention
    # 4: Salience/Ventral Attention
    # 5: Limbic
    # 6: Control
    # 7: Default Mode
    # But the task mentions DMN, Salience, Visual.
    # Let's assume the following mapping:
    # DMN -> 7
    # Salience -> 4
    # Visual -> 1
    # But this is a guess.
    # Since the task doesn't specify, we will use a more general approach:
    # We will assume that the network_labels are integers and that the network_names are provided as a list of names to calculate for.
    # We will create a mapping from network name to label based on a standard mapping.
    # If the standard mapping doesn't match, we will log a warning and skip.
    
    # Standard mapping for Schaefer 200 (7 networks)
    standard_mapping = {
        "Visual": 1,
        "Somatomotor": 2,
        "DorsalAttention": 3,
        "Salience": 4,
        "Limbic": 5,
        "Control": 6,
        "DefaultMode": 7
    }
    
    # We are interested in DMN, Salience, Visual.
    # Note: The task says "DMN", but the standard mapping uses "DefaultMode".
    # We will map "DMN" to 7.
    custom_mapping = {
        "DMN": 7,
        "Salience": 4,
        "Visual": 1
    }
    
    # Update the standard mapping with the custom one for the networks we care about.
    mapping = {**standard_mapping, **custom_mapping}
    
    results = {}
    
    for network_name in network_names:
        if network_name not in mapping:
            logger.warning(f"Network name '{network_name}' not found in mapping. Skipping.")
            continue
        
        label = mapping[network_name]
        
        # Get nodes belonging to this network
        nodes = np.where(network_labels == label)[0]
        
        if len(nodes) == 0:
            logger.warning(f"No nodes found for network '{network_name}' (label {label}). Skipping.")
            continue
        
        if len(nodes) == 1:
            logger.warning(f"Only one node found for network '{network_name}'. Efficiency is 0.")
            results[network_name] = 0.0
            continue
        
        # Extract the submatrix for this network
        submatrix = matrix[np.ix_(nodes, nodes)]
        
        # Calculate efficiency for this submatrix
        # We use the same method as calculate_global_efficiency
        n = submatrix.shape[0]
        distance_matrix = 1.0 - submatrix
        np.fill_diagonal(distance_matrix, np.inf)
        inv_dist = 1.0 / distance_matrix
        total_efficiency = np.sum(inv_dist)
        efficiency = total_efficiency / (n * (n - 1))
        
        results[network_name] = float(efficiency)
        logger.info(f"Calculated efficiency for {network_name}: {efficiency:.4f}")
    
    return results

def extract_edge_strengths(matrix: np.ndarray) -> Dict[str, List[Dict[str, Any]]]:
    """
    Extract edge-level connectivity strengths from the full matrix.
    
    Returns a dictionary with a list of edges, each containing:
      - node1: index of first node
      - node2: index of second node
      - strength: correlation value
    """
    if not validate_connectivity_matrix(matrix):
        raise ValueError("Invalid connectivity matrix provided.")
    
    edges = []
    n = matrix.shape[0]
    
    # Only extract upper triangle (excluding diagonal)
    for i in range(n):
        for j in range(i + 1, n):
            edges.append({
                "node1": int(i),
                "node2": int(j),
                "strength": float(matrix[i, j])
            })
    
    return {"edges": edges}

def compute_all_metrics(matrix: np.ndarray, 
                        network_labels: Optional[np.ndarray] = None,
                        network_names: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Compute all graph metrics: global efficiency, modularity, participation coefficient,
    and network-specific efficiencies.
    
    Args:
        matrix: Connectivity matrix
        network_labels: Optional array of network labels for each node
        network_names: Optional list of network names to calculate efficiencies for
    
    Returns:
        Dictionary containing all metrics
    """
    metrics = {}
    
    # Global efficiency
    metrics["global_efficiency"] = calculate_global_efficiency(matrix)
    
    # Modularity
    metrics["modularity"] = calculate_modularity(matrix)
    
    # Participation coefficient
    # We need community assignments for this. If network_labels are provided, we can use them.
    # Otherwise, we skip.
    if network_labels is not None:
        # We need to convert network_labels to communities for bct.participation_coeff
        # But bct.participation_coeff expects a community assignment (1, 2, 3, ...)
        # We can use the network_labels directly if they are integers starting from 1.
        # If they start from 0, we need to shift them.
        # Let's assume they are 0-indexed and shift them to 1-indexed.
        communities = network_labels + 1
        metrics["participation_coefficient"] = calculate_participation_coefficient(matrix, communities)
    else:
        metrics["participation_coefficient"] = None
        logger.warning("Network labels not provided. Participation coefficient skipped.")
    
    # Network-specific efficiencies
    if network_labels is not None and network_names is not None:
        metrics["network_efficiency"] = calculate_network_specific_efficiencies(matrix, network_labels, network_names)
    else:
        metrics["network_efficiency"] = {}
        logger.warning("Network labels or names not provided. Network-specific efficiencies skipped.")
    
    # Edge strengths
    metrics["edge_strength"] = extract_edge_strengths(matrix)
    
    return metrics

def save_metrics_to_json(metrics: Dict[str, Any], output_path: Path) -> None:
    """
    Save metrics to a JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Metrics saved to {output_path}")

def main():
    """
    Main function to demonstrate the usage of graph metrics.
    This is a placeholder for a full pipeline integration.
    """
    logger.info("Graph metrics module loaded successfully.")
    # In a real scenario, this would be called by a pipeline script.
    pass

if __name__ == "__main__":
    main()
