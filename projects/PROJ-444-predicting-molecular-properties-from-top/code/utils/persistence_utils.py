"""
Persistence utility functions for Topological Data Analysis on molecular graphs.
Implements shortest-path filtration, persistence diagram computation, and vectorization.
Includes memory threshold checks for large molecular weights.
"""
import logging
from typing import List, Tuple, Optional, Dict, Any, Union
import numpy as np
import networkx as nx
from scipy.spatial.distance import pdist, squareform
from scipy.sparse import csr_matrix, diags, issparse
import sys

# Memory threshold in bytes (6.0 GB)
MEMORY_THRESHOLD_BYTES = 6.0 * 1024**3

logger = logging.getLogger(__name__)

def check_memory_requirement(num_nodes: int, num_edges: int) -> bool:
    """
    Estimate RAM usage for dense matrix operations and check against threshold.
    
    Args:
        num_nodes: Number of nodes in the graph
        num_edges: Number of edges in the graph
        
    Returns:
        True if estimated RAM usage exceeds threshold (sparse recommended),
        False if dense processing is acceptable.
    """
    # Estimate size for dense adjacency matrix (float64)
    # Size = num_nodes * num_nodes * 8 bytes
    dense_size = num_nodes * num_nodes * 8
    
    # Estimate size for distance matrix (symmetric, stored as full)
    # Size = num_nodes * num_nodes * 8 bytes
    distance_size = num_nodes * num_nodes * 8
    
    # Estimate size for filtration matrix (simple: num_nodes * num_nodes * 8)
    filtration_size = num_nodes * num_nodes * 8
    
    total_estimated = dense_size + distance_size + filtration_size
    
    if total_estimated > MEMORY_THRESHOLD_BYTES:
        logger.warning(
            f"Estimated memory usage ({total_estimated / 1024**3:.2f} GB) exceeds "
            f"threshold ({MEMORY_THRESHOLD_BYTES / 1024**3:.2f} GB). "
            "Switching to sparse matrix operations."
        )
        return True
    
    logger.info(f"Estimated memory usage ({total_estimated / 1024**6:.3f} GB) within threshold.")
    return False

def compute_shortest_path_matrix(graph: nx.Graph, use_sparse: bool = False) -> Union[np.ndarray, csr_matrix]:
    """
    Compute shortest path distances between all pairs of nodes using Dijkstra's algorithm.
    
    Args:
        graph: NetworkX graph representing the molecule
        use_sparse: If True, return scipy.sparse.csr_matrix; otherwise return numpy array
        
    Returns:
        Distance matrix (either dense numpy or sparse csr_matrix)
    """
    num_nodes = graph.number_of_nodes()
    
    if num_nodes == 0:
        if use_sparse:
            return csr_matrix((0, 0))
        return np.zeros((0, 0))
    
    # Get node indices to ensure consistent ordering
    nodes = list(graph.nodes())
    node_to_idx = {node: i for i, node in enumerate(nodes)}
    
    # Compute all shortest paths
    # Using scipy.sparse if requested for memory efficiency
    if use_sparse:
        # Build sparse adjacency matrix with edge weights (default 1.0)
        rows, cols, data = [], [], []
        for u, v, data_dict in graph.edges(data=True):
            i, j = node_to_idx[u], node_to_idx[v]
            weight = data_dict.get('weight', 1.0)
            rows.extend([i, j])
            cols.extend([j, i])
            data.extend([weight, weight])
        
        adj_matrix = csr_matrix(
            (data, (rows, cols)),
            shape=(num_nodes, num_nodes)
        )
        
        # Compute shortest paths using scipy.sparse algorithms
        # For small graphs, we can use Floyd-Warshall via dense conversion
        # For large graphs, we use multiple Dijkstra runs
        try:
            # Use networkx's all_pairs_dijkstra_path_length which is efficient
            # and returns a generator, allowing us to build sparse matrix
            dist_dict = dict(nx.all_pairs_dijkstra_path_length(graph, weight='weight'))
            
            # Build sparse matrix from distances
            rows, cols, data = [], [], []
            for i, (u, dists) in enumerate(dist_dict.items()):
                for v, dist in dists.items():
                    j = node_to_idx[v]
                    rows.append(i)
                    cols.append(j)
                    data.append(float(dist))
            
            return csr_matrix((data, (rows, cols)), shape=(num_nodes, num_nodes))
        except Exception as e:
            logger.warning(f"Sparse shortest path computation failed: {e}, falling back to dense")
            use_sparse = False
    
    # Dense computation fallback
    dist_matrix = np.zeros((num_nodes, num_nodes))
    for i, u in enumerate(nodes):
        try:
            lengths = nx.single_source_dijkstra_path_length(graph, u, weight='weight')
            for j, v in enumerate(nodes):
                dist_matrix[i, j] = lengths.get(v, np.inf)
        except Exception as e:
            logger.error(f"Error computing shortest paths from node {u}: {e}")
            raise
    
    return dist_matrix

def build_shortest_path_filtration(dist_matrix: Union[np.ndarray, csr_matrix]) -> List[Tuple[float, float]]:
    """
    Build filtration from distance matrix.
    Creates simplices with filtration values based on shortest path distances.
    
    Args:
        dist_matrix: Distance matrix (dense or sparse)
        
    Returns:
        List of (birth, death) tuples for persistence diagram
    """
    if issparse(dist_matrix):
        dist_matrix = dist_matrix.toarray()
    
    n = dist_matrix.shape[0]
    if n == 0:
        return []
    
    # Build edge list for 1-simplices (edges)
    # Filtration value = distance between nodes
    edges = []
    for i in range(n):
        for j in range(i + 1, n):
            if not np.isinf(dist_matrix[i, j]):
                edges.append((i, j, dist_matrix[i, j]))
    
    # Sort edges by filtration value (distance)
    edges.sort(key=lambda x: x[2])
    
    # Compute persistence using union-find for 0-dimensional homology
    # and simple edge tracking for 1-dimensional homology
    parent = list(range(n))
    
    def find(i):
        if parent[i] != i:
            parent[i] = find(parent[i])
        return parent[i]
    
    def union(i, j):
        root_i, root_j = find(i), find(j)
        if root_i != root_j:
            parent[root_i] = root_j
            return True
        return False
    
    diagram = []
    active_cycles = {}  # Track potential 1-cycles: (u, v, birth) -> death_candidate
    
    # Process edges in filtration order
    for u, v, birth in edges:
        root_u, root_v = find(u), find(v)
        
        if root_u != root_v:
            # Edge connects two components -> birth of 0-cycle or death of 0-cycle
            union(u, v)
            # Record birth of a 0-cycle (component merging)
            # The birth value is the edge weight
            # The death value will be determined when this component merges with another
            # For simplicity, we track component births
        else:
            # Edge connects nodes in same component -> potential 1-cycle birth
            # Birth of 1-cycle is the edge weight
            # We'll determine death when the cycle is "filled"
            # For now, we mark this as a potential cycle
            pass
    
    # Simplified approach: Use standard persistence computation
    # For molecular graphs, we focus on 0-dim (components) and 1-dim (cycles)
    
    # Re-compute using a more direct method
    # Birth of 0-cycle: when a component is created (initially all nodes)
    # Death of 0-cycle: when two components merge
    # Birth of 1-cycle: when an edge creates a cycle
    # Death of 1-cycle: when the cycle is "filled" (hard to define, often infinity)
    
    # For this implementation, we'll use a simplified approach:
    # 1. Compute connected components at each filtration level
    # 2. Track when components merge (0-dim persistence)
    # 3. Track when cycles form (1-dim persistence)
    
    # Reset union-find
    parent = list(range(n))
    component_births = {i: 0.0 for i in range(n)}  # Each node starts as a component at birth=0
    
    for u, v, birth in edges:
        root_u, root_v = find(u), find(v)
        
        if root_u != root_v:
            # Components merge: death of the later-born component
            # The component that was born later dies at 'birth'
            birth_u = component_births[root_u]
            birth_v = component_births[root_v]
            
            if birth_u > birth_v:
                diagram.append((birth_v, birth_u, 0))  # (birth, death, dim)
            else:
                diagram.append((birth_u, birth_v, 0))
            
            # Merge components
            union(u, v)
            new_root = find(u)
            # The merged component inherits the earlier birth time
            component_births[new_root] = min(birth_u, birth_v)
        else:
            # Cycle formed: birth of 1-cycle
            # Death is typically infinity for molecular graphs (no filling)
            diagram.append((birth, np.inf, 1))
    
    return diagram

def compute_persistence_diagram(graph: nx.Graph) -> List[Tuple[float, float, int]]:
    """
    Compute persistence diagram for a molecular graph using shortest-path filtration.
    
    Args:
        graph: NetworkX graph representing the molecule
        
    Returns:
        List of (birth, death, dimension) tuples
    """
    if graph.number_of_nodes() == 0:
        return []
    
    # Check memory requirements
    num_nodes = graph.number_of_nodes()
    num_edges = graph.number_of_edges()
    use_sparse = check_memory_requirement(num_nodes, num_edges)
    
    # Compute distance matrix
    dist_matrix = compute_shortest_path_matrix(graph, use_sparse=use_sparse)
    
    # Build filtration and compute persistence
    diagram = build_shortest_path_filtration(dist_matrix)
    
    return diagram

def vectorize(diagram: List[Tuple[float, float, int]], resolution: int) -> np.ndarray:
    """
    Vectorize a persistence diagram into a persistence image (grid representation).
    
    Args:
        diagram: List of (birth, death, dimension) tuples
        resolution: Grid resolution (e.g., 10 for 10x10)
        
    Returns:
        Flattened numpy array of size resolution*resolution
    """
    if not diagram:
        return np.zeros(resolution * resolution)
    
    # Filter for 1-dimensional cycles (rings in molecules)
    # Focus on 1-dim for molecular topology
    cycles = [(b, d) for b, d, dim in diagram if dim == 1 and np.isfinite(d)]
    
    if not cycles:
        return np.zeros(resolution * resolution)
    
    # Determine bounding box
    births = [b for b, d in cycles]
    deaths = [d for b, d in cycles]
    
    min_birth = min(births)
    max_birth = max(births)
    min_death = min(deaths)
    max_death = max(deaths)
    
    # Ensure non-zero range
    if max_birth == min_birth:
        max_birth = min_birth + 1.0
    if max_death == min_death:
        max_death = min_death + 1.0
    
    # Create grid
    image = np.zeros((resolution, resolution))
    
    # Map points to grid
    for birth, death in cycles:
        # Normalize to [0, 1]
        norm_birth = (birth - min_birth) / (max_birth - min_birth)
        norm_death = (death - min_death) / (max_death - min_death)
        
        # Map to grid indices
        i = min(int(norm_birth * resolution), resolution - 1)
        j = min(int(norm_death * resolution), resolution - 1)
        
        # Ensure indices are within bounds
        i = max(0, min(i, resolution - 1))
        j = max(0, min(j, resolution - 1))
        
        # Weight by persistence (death - birth)
        persistence = death - birth
        image[i, j] += persistence
    
    # Flatten and return
    return image.flatten()

def handle_empty_diagram(resolution: int) -> np.ndarray:
    """
    Handle empty persistence diagram by returning zero vector.
    
    Args:
        resolution: Grid resolution
        
    Returns:
        Zero vector of size resolution*resolution
    """
    return np.zeros(resolution * resolution)

def compute_betti_numbers(diagram: List[Tuple[float, float, int]], threshold: float) -> Dict[int, int]:
    """
    Compute Betti numbers at a given threshold.
    
    Args:
        diagram: Persistence diagram
        threshold: Filtration threshold
        
    Returns:
        Dictionary mapping dimension to Betti number
    """
    betti = {0: 0, 1: 0}
    
    for birth, death, dim in diagram:
        if birth <= threshold < death:
            betti[dim] += 1
    
    return betti

def get_topological_features(diagram: List[Tuple[float, float, int]]) -> Dict[str, float]:
    """
    Extract summary features from persistence diagram.
    
    Args:
        diagram: Persistence diagram
        
    Returns:
        Dictionary of topological features
    """
    features = {}
    
    # Count 1-dimensional cycles (rings)
    cycles_1d = [d for b, d, dim in diagram if dim == 1 and np.isfinite(d)]
    features['num_rings'] = len(cycles_1d)
    
    if cycles_1d:
        persistences = [d - b for b, d in cycles_1d]
        features['max_persistence'] = max(persistences)
        features['mean_persistence'] = np.mean(persistences)
        features['total_persistence'] = sum(persistences)
    else:
        features['max_persistence'] = 0.0
        features['mean_persistence'] = 0.0
        features['total_persistence'] = 0.0
    
    return features

def main():
    """Test function for persistence utilities."""
    logging.basicConfig(level=logging.INFO)
    
    # Create a test graph (simple cycle)
    graph = nx.cycle_graph(5)
    graph.add_edge(0, 1, weight=1.0)
    graph.add_edge(1, 2, weight=1.0)
    graph.add_edge(2, 3, weight=1.0)
    graph.add_edge(3, 4, weight=1.0)
    graph.add_edge(4, 0, weight=1.0)
    
    # Test memory check
    use_sparse = check_memory_requirement(1000, 2000)
    logger.info(f"Use sparse: {use_sparse}")
    
    # Test persistence diagram
    diagram = compute_persistence_diagram(graph)
    logger.info(f"Diagram: {diagram}")
    
    # Test vectorization
    vec = vectorize(diagram, 10)
    logger.info(f"Vector shape: {vec.shape}")
    
    # Test empty diagram
    empty_vec = handle_empty_diagram(10)
    logger.info(f"Empty vector: {empty_vec}")
    
    print("Persistence utils test completed.")

if __name__ == "__main__":
    main()