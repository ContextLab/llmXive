import numpy as np
import networkx as nx
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple

from config import is_synthetic, check_data_availability
from entities import ConnectivityMatrix, GraphMetrics

logger = logging.getLogger(__name__)

def calculate_global_efficiency(adj_matrix: np.ndarray) -> float:
    """
    Calculate Global Efficiency of a graph from its adjacency matrix.
    Global Efficiency is the average of the inverse shortest path lengths.
    """
    if adj_matrix.shape[0] != adj_matrix.shape[1]:
        raise ValueError("Adjacency matrix must be square.")
    
    G = nx.from_numpy_array(adj_matrix)
    if not nx.is_connected(G) and nx.number_connected_components(G) > 1:
        # For disconnected graphs, efficiency is defined over reachable pairs only
        # or we can treat infinite distance as 0 contribution (standard approach)
        pass

    try:
        # nx.efficiency uses shortest path length
        # Global efficiency is average efficiency over all pairs
        eff = nx.global_efficiency(G)
        return float(eff)
    except Exception as e:
        logger.warning(f"Could not calculate global efficiency: {e}")
        return 0.0

def calculate_local_efficiency(adj_matrix: np.ndarray) -> float:
    """
    Calculate Local Efficiency of a graph from its adjacency matrix.
    Local efficiency is the average of the efficiencies of the local subgraphs.
    """
    if adj_matrix.shape[0] != adj_matrix.shape[1]:
        raise ValueError("Adjacency matrix must be square.")
    
    G = nx.from_numpy_array(adj_matrix)
    try:
        eff = nx.local_efficiency(G)
        return float(eff)
    except Exception as e:
        logger.warning(f"Could not calculate local efficiency: {e}")
        return 0.0

def calculate_modularity(adj_matrix: np.ndarray, partitions: Optional[Dict[int, int]] = None) -> float:
    """
    Calculate Modularity (Q) of a graph.
    If partitions are not provided, use a default community detection algorithm (Louvain).
    """
    if adj_matrix.shape[0] != adj_matrix.shape[1]:
        raise ValueError("Adjacency matrix must be square.")
    
    G = nx.from_numpy_array(adj_matrix)
    try:
        if partitions is None:
            # Use Louvain algorithm for community detection
            try:
                import community
                partitions = community.best_partition(G)
            except ImportError:
                logger.warning("python-louvain not found, using default partitioning or returning 0.0")
                return 0.0
        
        modularity = nx.community.modularity(G, partitions.values())
        return float(modularity)
    except Exception as e:
        logger.warning(f"Could not calculate modularity: {e}")
        return 0.0

def apply_spatial_threshold(adj_matrix: np.ndarray, threshold_type: str = 'proportional', threshold_value: float = 0.1) -> np.ndarray:
    """
    Apply a threshold to the connectivity matrix.
    
    Args:
        adj_matrix: Input connectivity matrix (symmetric, NxN)
        threshold_type: 'proportional' or 'absolute'
        threshold_value: 
            - If 'proportional', fraction of edges to keep (0.0 to 1.0)
            - If 'absolute', minimum weight to keep
    
    Returns:
        Thresholded adjacency matrix
    """
    if threshold_type == 'proportional':
        if not 0.0 < threshold_value <= 1.0:
            raise ValueError("Proportional threshold must be between 0 and 1 (exclusive of 0).")
        
        # Get upper triangle indices (excluding diagonal)
        n = adj_matrix.shape[0]
        rows, cols = np.triu_indices(n, k=1)
        weights = adj_matrix[rows, cols]
        
        # Calculate the number of edges to keep
        num_edges = int(len(weights) * threshold_value)
        
        if num_edges == 0:
            logger.warning("Proportional threshold resulted in 0 edges. Using a very small threshold.")
            num_edges = 1
        
        # Sort weights and find the cutoff
        sorted_weights = np.sort(weights)
        cutoff = sorted_weights[-num_edges] if num_edges <= len(sorted_weights) else sorted_weights[0]
        
        # Create binary mask
        mask = adj_matrix >= cutoff
        np.fill_diagonal(mask, 0)  # Remove self-loops
        
        # Apply mask
        thresholded_matrix = adj_matrix * mask
        
        # Ensure we have exactly the right number of edges (in case of ties)
        # This is a simplification; exact edge count might vary slightly with ties
        logger.info(f"Applied proportional threshold {threshold_value}. Kept {np.sum(thresholded_matrix > 0)} edges.")
        
    elif threshold_type == 'absolute':
        thresholded_matrix = adj_matrix.copy()
        thresholded_matrix[thresholded_matrix < threshold_value] = 0
        np.fill_diagonal(thresholded_matrix, 0)
    else:
        raise ValueError(f"Unknown threshold type: {threshold_type}")
    
    return thresholded_matrix

def compute_metrics_from_matrix(adj_matrix: np.ndarray, threshold_type: str = 'proportional', threshold_value: float = 0.1) -> Dict[str, float]:
    """
    Compute graph metrics from a connectivity matrix after applying thresholding.
    
    Args:
        adj_matrix: Input connectivity matrix
        threshold_type: Type of thresholding ('proportional' or 'absolute')
        threshold_value: Threshold value
    
    Returns:
        Dictionary of graph metrics
    """
    if adj_matrix.shape[0] != adj_matrix.shape[1]:
        raise ValueError("Adjacency matrix must be square.")
    
    # Apply thresholding
    thresholded_matrix = apply_spatial_threshold(adj_matrix, threshold_type, threshold_value)
    
    # Calculate metrics
    global_eff = calculate_global_efficiency(thresholded_matrix)
    local_eff = calculate_local_efficiency(thresholded_matrix)
    modularity = calculate_modularity(thresholded_matrix)
    
    return {
        "global_efficiency": global_eff,
        "local_efficiency": local_eff,
        "modularity": modularity,
        "threshold_type": threshold_type,
        "threshold_value": threshold_value,
        "num_edges": int(np.sum(thresholded_matrix > 0))
    }

def process_connectivity_matrices(
    matrices: List[Union[np.ndarray, ConnectivityMatrix]],
    threshold_type: str = 'proportional',
    threshold_value: float = 0.1
) -> List[GraphMetrics]:
    """
    Process a list of connectivity matrices and compute graph metrics.
    
    Args:
        matrices: List of connectivity matrices or ConnectivityMatrix objects
        threshold_type: Type of thresholding
        threshold_value: Threshold value
    
    Returns:
        List of GraphMetrics objects
    """
    results = []
    
    for i, mat in enumerate(matrices):
        if isinstance(mat, ConnectivityMatrix):
            adj_matrix = mat.matrix
            subject_id = mat.subject_id
            time_point = mat.time_point
        else:
            adj_matrix = mat
            subject_id = f"subject_{i}"
            time_point = None
        
        try:
            metrics_dict = compute_metrics_from_matrix(adj_matrix, threshold_type, threshold_value)
            metrics = GraphMetrics(
                subject_id=subject_id,
                time_point=time_point,
                global_efficiency=metrics_dict["global_efficiency"],
                local_efficiency=metrics_dict["local_efficiency"],
                modularity=metrics_dict["modularity"],
                threshold_type=metrics_dict["threshold_type"],
                threshold_value=metrics_dict["threshold_value"],
                num_edges=metrics_dict["num_edges"]
            )
            results.append(metrics)
            logger.info(f"Processed matrix {i}: Global Eff={metrics.global_efficiency:.4f}, "
                        f"Local Eff={metrics.local_efficiency:.4f}, Modularity={metrics.modularity:.4f}")
        except Exception as e:
            logger.error(f"Failed to process matrix {i}: {e}")
            # Create a placeholder or skip? Let's create a placeholder with zeros
            metrics = GraphMetrics(
                subject_id=subject_id,
                time_point=time_point,
                global_efficiency=0.0,
                local_efficiency=0.0,
                modularity=0.0,
                threshold_type=threshold_type,
                threshold_value=threshold_value,
                num_edges=0
            )
            results.append(metrics)
    
    return results

def main():
    """
    Main function to demonstrate graph metrics calculation with thresholding.
    This is a placeholder for integration with the full pipeline.
    """
    logging.basicConfig(level=logging.INFO)
    
    # Example: Load a sample matrix (in real usage, this would come from preprocessing)
    # For now, we'll create a synthetic one if in synthetic mode
    if is_synthetic():
        logger.info("Running in synthetic mode. Generating sample data.")
        from synthetic_data import generate_connectivity_matrix
        n_nodes = 90  # AAL atlas size
        sample_matrix = generate_connectivity_matrix(n_nodes, seed=42)
        
        # Process with proportional thresholding
        metrics = compute_metrics_from_matrix(sample_matrix, threshold_type='proportional', threshold_value=0.1)
        logger.info(f"Synthetic metrics: {metrics}")
        
        # Save to file
        output_path = Path("data/results/sample_metrics.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(metrics, f, indent=2)
        logger.info(f"Sample metrics saved to {output_path}")
    else:
        logger.info("Real data mode. Integration with preprocessing pipeline required.")
        # In real mode, this would be called from the pipeline with actual matrices
        # from data/processed/
        pass

if __name__ == "__main__":
    main()
