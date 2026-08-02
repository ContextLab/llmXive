import numpy as np
import networkx as nx
from typing import Tuple, Dict, Any, List, Optional
import warnings
import os
import sys

def generate_correlation_matrix(time_series: np.ndarray) -> np.ndarray:
    """
    Compute the Pearson correlation matrix from a time series array.
    
    Args:
        time_series: Array of shape (n_timepoints, n_rois)
        
    Returns:
        Correlation matrix of shape (n_rois, n_rois)
    """
    if time_series.shape[0] < 2:
        raise ValueError("Need at least 2 timepoints to compute correlation.")
    
    # Use numpy corrcoef which returns (n_rois, n_rois)
    corr_matrix = np.corrcoef(time_series.T)
    
    # Handle NaNs that might arise from constant signals
    corr_matrix = np.nan_to_num(corr_matrix, nan=0.0)
    
    return corr_matrix

def compute_global_efficiency(adjacency_matrix: np.ndarray) -> float:
    """
    Compute global efficiency of a graph from its adjacency matrix.
    
    Args:
        adjacency_matrix: Square matrix representing edge weights
        
    Returns:
        Global efficiency value (0.0 to 1.0)
    """
    # Create graph from adjacency matrix
    G = nx.from_numpy_array(adjacency_matrix)
    
    # Calculate global efficiency
    try:
        efficiency = nx.global_efficiency(G)
    except nx.NetworkXError:
        # Handle disconnected graphs or empty graphs
        efficiency = 0.0
        
    return float(efficiency)

def compute_clustering_coefficient(adjacency_matrix: np.ndarray) -> float:
    """
    Compute the average clustering coefficient of a graph.
    
    Args:
        adjacency_matrix: Square matrix representing edge weights
        
    Returns:
        Average clustering coefficient (0.0 to 1.0)
    """
    G = nx.from_numpy_array(adjacency_matrix)
    
    try:
        clustering = nx.average_clustering(G)
    except nx.NetworkXError:
        clustering = 0.0
        
    return float(clustering)

def compute_modularity_louvain(adjacency_matrix: np.ndarray, resolution: float = 1.0) -> float:
    """
    Compute modularity using the Louvain algorithm with a specific resolution.
    
    Args:
        adjacency_matrix: Square matrix representing edge weights
        resolution: Resolution parameter for Louvain algorithm
        
    Returns:
        Modularity value
        
    Raises:
        RuntimeError: If Louvain algorithm fails to converge
    """
    G = nx.from_numpy_array(adjacency_matrix)
    
    try:
        # Use louvain_communities from networkx (available in recent versions)
        # If not available, fallback to community_louvain
        try:
            from networkx.algorithms import community
            partitions = community.louvain_communities(G, resolution=resolution, seed=42)
        except (ImportError, AttributeError):
            # Fallback for older networkx versions
            import community as community_louvain
            partition = community_louvain.best_partition(G, weight='weight', resolution=resolution)
            partitions = [node for node, comm in partition.items()]
            
        # Calculate modularity
        modularity = nx.community.modularity(G, partitions)
        return float(modularity)
        
    except Exception as e:
        raise RuntimeError(f"Louvain algorithm failed to converge: {e}")

def compute_modularity_with_resolution_sweep(
    adjacency_matrix: np.ndarray,
    resolution_range: Optional[List[float]] = None,
    max_attempts: int = 10
) -> Dict[str, Any]:
    """
    Compute modularity with a resolution parameter sweep to find optimal value.
    
    Args:
        adjacency_matrix: Square matrix representing edge weights
        resolution_range: List of resolution parameters to try. Defaults to [0.1, 0.5, 1.0, 1.5, 2.0]
        max_attempts: Maximum number of resolution values to try
        
    Returns:
        Dictionary with:
            - 'best_modularity': Highest modularity found
            - 'best_resolution': Resolution parameter that achieved best modularity
            - 'all_results': List of (resolution, modularity) tuples
    """
    if resolution_range is None:
        resolution_range = [0.1, 0.5, 1.0, 1.5, 2.0]
        
    results = []
    best_modularity = -float('inf')
    best_resolution = 1.0
    
    # Try each resolution parameter
    for resolution in resolution_range[:max_attempts]:
        try:
            modularity = compute_modularity_louvain(adjacency_matrix, resolution=resolution)
            results.append((resolution, modularity))
            
            if modularity > best_modularity:
                best_modularity = modularity
                best_resolution = resolution
                
        except RuntimeError as e:
            warnings.warn(f"Resolution {resolution} failed: {e}")
            continue
            
    if not results:
        # If all attempts failed, return default
        return {
            'best_modularity': 0.0,
            'best_resolution': 1.0,
            'all_results': [],
            'error': 'All resolution attempts failed'
        }
        
    return {
        'best_modularity': best_modularity,
        'best_resolution': best_resolution,
        'all_results': results
    }

def compute_graph_metrics(time_series: np.ndarray, resolution_range: Optional[List[float]] = None) -> Dict[str, float]:
    """
    Compute all graph metrics for a subject's time series.
    
    Args:
        time_series: Array of shape (n_timepoints, n_rois)
        resolution_range: Resolution parameters for modularity sweep
        
    Returns:
        Dictionary with metric names and values:
            - global_efficiency
            - clustering_coefficient
            - modularity
            - modularity_best_resolution
    """
    # Generate correlation matrix
    corr_matrix = generate_correlation_matrix(time_series)
    
    # Convert correlation matrix to adjacency (thresholding)
    # Simple threshold: keep edges with correlation > 0.2
    threshold = 0.2
    adjacency_matrix = np.where(np.abs(corr_matrix) > threshold, corr_matrix, 0.0)
    
    # Compute metrics
    global_eff = compute_global_efficiency(adjacency_matrix)
    clustering_coef = compute_clustering_coefficient(adjacency_matrix)
    
    # Modularity with resolution sweep
    modularity_result = compute_modularity_with_resolution_sweep(adjacency_matrix, resolution_range)
    
    return {
        'global_efficiency': global_eff,
        'clustering_coefficient': clustering_coef,
        'modularity': modularity_result['best_modularity'],
        'modularity_best_resolution': modularity_result['best_resolution']
    }

def main():
    """
    Main function to demonstrate graph metrics computation.
    This is a placeholder for actual execution; real usage requires 
    preprocessed time series data from data/processed/.
    """
    print("Graph metrics module loaded successfully.")
    print("Available functions:")
    print("  - generate_correlation_matrix")
    print("  - compute_global_efficiency")
    print("  - compute_clustering_coefficient")
    print("  - compute_modularity_louvain")
    print("  - compute_modularity_with_resolution_sweep")
    print("  - compute_graph_metrics")
    
    # Example usage with dummy data
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        print("\nRunning test with dummy data...")
        # Create dummy time series: 100 timepoints, 100 ROIs
        dummy_ts = np.random.randn(100, 100)
        
        metrics = compute_graph_metrics(dummy_ts)
        print(f"Dummy metrics: {metrics}")

if __name__ == '__main__':
    main()