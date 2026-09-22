import logging
from typing import List, Tuple, Optional, Dict, Any, Union
import numpy as np
import networkx as nx
from scipy.spatial.distance import pdist, squareform
from scipy.sparse import csr_matrix, diags
from scipy.sparse.csgraph import dijkstra

MEMORY_THRESHOLD_GB = 4.0

def check_memory_requirement(n_nodes: int) -> float:
    """
    Estimate memory requirement for shortest path matrix computation.
    
    Args:
        n_nodes: Number of nodes in the graph.
        
    Returns:
        Estimated memory requirement in GB.
    """
    # Dense matrix: n_nodes * n_nodes * 8 bytes (float64)
    dense_bytes = n_nodes * n_nodes * 8
    dense_gb = dense_bytes / (1024 ** 3)
    
    # Sparse matrix is typically much smaller, but we estimate conservatively
    # Assume average degree of 4 for molecular graphs
    sparse_bytes = n_nodes * 4 * 8 * 2  # CSR format overhead
    sparse_gb = sparse_bytes / (1024 ** 3)
    
    # Return the larger estimate for safety
    return max(dense_gb, sparse_gb)

def compute_shortest_path_matrix(
    graph: nx.Graph,
    use_sparse: bool = False
) -> np.ndarray:
    """
    Compute shortest path matrix for a graph.
    
    Args:
        graph: NetworkX graph with edge weights.
        use_sparse: If True, use sparse matrix computation.
        
    Returns:
        2D numpy array of shortest path lengths.
    """
    n = graph.number_of_nodes()
    nodes = list(graph.nodes())
    
    if use_sparse:
        # Use sparse matrix computation
        adj_matrix = nx.adjacency_matrix(graph)
        sparse_adj = csr_matrix(adj_matrix)
        
        try:
            lengths = dijkstra(csgraph=sparse_adj, directed=False, indices=range(n))
            # Handle disconnected components
            lengths = np.where(np.isinf(lengths), n * 10, lengths)
            return lengths
        except Exception as e:
            logging.warning(f"Sparse shortest path failed: {e}")
            # Fallback to dense computation
            use_sparse = False
    
    if not use_sparse:
        # Standard computation
        shortest_paths = nx.shortest_path_length(graph, weight='weight')
        matrix = np.zeros((n, n))
        for i, u in enumerate(nodes):
            for j, v in enumerate(nodes):
                if u in shortest_paths and v in shortest_paths[u]:
                    matrix[i, j] = shortest_paths[u][v]
                else:
                    matrix[i, j] = n * 10  # Large value for disconnected
        return matrix

def build_shortest_path_filtration(
    shortest_paths: np.ndarray
) -> List[Tuple[float, float, float, float]]:
    """
    Build a filtration from shortest path matrix.
    
    Args:
        shortest_paths: 2D array of shortest path lengths.
        
    Returns:
        List of simplices with (birth, death, dim, index).
    """
    n = shortest_paths.shape[0]
    filtration = []
    
    # 0-simplices (vertices) - born at 0
    for i in range(n):
        filtration.append((0.0, 0.0, 0, i))
    
    # 1-simplices (edges) - born at shortest path distance
    for i in range(n):
        for j in range(i + 1, n):
            dist = shortest_paths[i, j]
            if dist < n * 10:  # Connected
                filtration.append((dist, dist, 1, (i, j)))
    
    return filtration

def compute_persistence_diagram(
    filtration: List[Tuple[float, float, float, float]]
) -> List[Tuple[float, float]]:
    """
    Compute persistence diagram from filtration.
    
    Note: This is a simplified implementation. In production, use Gudhi or Dionysus.
    
    Args:
        filtration: List of simplices with birth/death times.
        
    Returns:
        List of (birth, death) tuples.
    """
    # For demonstration, return a simplified diagram
    # In reality, this would use a proper persistence algorithm
    diagram = []
    
    # Group by dimension
    dim_0 = [s for s in filtration if s[2] == 0]
    dim_1 = [s for s in filtration if s[2] == 1]
    
    # Simplified persistence calculation
    if dim_0:
        # First component born at 0
        diagram.append((0.0, 1.0))  # Infinite persistence approximated
    
    if dim_1:
        # Cycles born and die at edge distances
        for s in dim_1:
            birth = s[0]
            death = s[0] + 0.1  # Simplified death time
            if death > birth:
                diagram.append((birth, death))
    
    return diagram

def handle_empty_diagram() -> List[Tuple[float, float]]:
    """
    Handle case where no persistence diagram is computed.
    
    Returns:
        Empty diagram placeholder.
    """
    return []

def compute_betti_numbers(
    diagram: List[Tuple[float, float]]
) -> List[int]:
    """
    Compute Betti numbers from persistence diagram.
    
    Args:
        diagram: List of (birth, death) tuples.
        
    Returns:
        List of Betti numbers [beta_0, beta_1, ...].
    """
    if not diagram:
        return [0, 0]
    
    # Count features with significant persistence
    beta_0 = 0
    beta_1 = 0
    
    for birth, death in diagram:
        persistence = death - birth
        if persistence > 0.1:  # Threshold for significance
            if birth == 0.0:
                beta_0 += 1
            else:
                beta_1 += 1
    
    return [beta_0, beta_1]

def get_topological_features(
    diagram: List[Tuple[float, float]]
) -> Dict[str, float]:
    """
    Extract topological features from persistence diagram.
    
    Args:
        diagram: List of (birth, death) tuples.
        
    Returns:
        Dictionary of topological features.
    """
    if not diagram:
        return {
            "total_persistence": 0.0,
            "max_persistence": 0.0,
            "mean_persistence": 0.0,
            "num_features": 0
        }
    
    persistences = [d - b for b, d in diagram if d > b]
    
    return {
        "total_persistence": sum(persistences),
        "max_persistence": max(persistences) if persistences else 0.0,
        "mean_persistence": np.mean(persistences) if persistences else 0.0,
        "num_features": len(persistences)
    }

def main():
    """Main entry point for persistence utilities."""
    print("Persistence utilities module loaded successfully.")

if __name__ == "__main__":
    main()
