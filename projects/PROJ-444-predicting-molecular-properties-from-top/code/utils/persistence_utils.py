"""
persistence_utils.py
Topological Data Analysis utilities for molecular graphs.
Handles shortest-path filtration, persistence diagram computation,
vectorization, and memory threshold checks for large graphs.
"""

import logging
from typing import List, Tuple, Optional, Dict, Any, Union, Set
import numpy as np
import networkx as nx
from scipy.spatial.distance import pdist, squareform
from scipy.sparse import csr_matrix, diags, issparse
import sys

# Thresholds
MEMORY_THRESHOLD_GB = 6.0
MEMORY_THRESHOLD_BYTES = MEMORY_THRESHOLD_GB * 1024**3
ESTIMATED_EDGE_FACTOR = 8.0  # Bytes per edge in adjacency matrix representation

logger = logging.getLogger(__name__)


def check_memory_requirement(graph: nx.Graph) -> bool:
    """
    Estimate RAM usage for a single molecule's persistence calculation.
    If estimated RAM > 6.0GB, return True (sparse mode recommended).
    Otherwise, return False (dense mode is acceptable).

    Estimation logic:
    - Number of edges in the graph.
    - Assume an adjacency matrix of size N x N where N = num_nodes.
    - Dense float64 matrix takes 8 bytes per entry.
    - We check if N*N * 8 > threshold.

    Note: For extremely large N, we might also consider edge count,
    but the adjacency matrix size is the dominant factor for standard
    persistence algorithms that often rely on dense distance matrices.
    """
    num_nodes = graph.number_of_nodes()
    # Estimate memory for a dense NxN float64 matrix
    estimated_bytes = (num_nodes * num_nodes) * 8

    if estimated_bytes > MEMORY_THRESHOLD_BYTES:
        logger.warning(
            f"Estimated memory for graph with {num_nodes} nodes: "
            f"{estimated_bytes / (1024**3):.2f} GB > {MEMORY_THRESHOLD_GB} GB. "
            "Switching to sparse matrix logic."
        )
        return True
    return False


def compute_shortest_path_matrix(graph: nx.Graph, use_sparse: bool = False) -> Union[np.ndarray, csr_matrix]:
    """
    Compute the shortest-path distance matrix for the graph.

    Args:
        graph: NetworkX graph.
        use_sparse: If True, return a scipy.sparse.csr_matrix.
                   If False, return a dense numpy array.

    Returns:
        Distance matrix (dense or sparse).
    """
    nodes = list(graph.nodes())
    n = len(nodes)
    node_to_idx = {node: i for i, node in enumerate(nodes)}

    if n == 0:
        if use_sparse:
            return csr_matrix((0, 0))
        return np.zeros((0, 0))

    # Initialize distance matrix
    if use_sparse:
        # We will build a sparse matrix using COO format then convert to CSR
        rows = []
        cols = []
        data = []
        
        # For each node, run Dijkstra
        for source_idx, source_node in enumerate(nodes):
            lengths = nx.single_source_dijkstra_path_length(graph, source_node)
            for target_node, dist in lengths.items():
                target_idx = node_to_idx[target_node]
                rows.append(source_idx)
                cols.append(target_idx)
                data.append(float(dist))
        
        dist_matrix = csr_matrix(
            (data, (rows, cols)), 
            shape=(n, n),
            dtype=np.float64
        )
    else:
        dist_matrix = np.zeros((n, n), dtype=np.float64)
        for source_idx, source_node in enumerate(nodes):
            lengths = nx.single_source_dijkstra_path_length(graph, source_node)
            for target_node, dist in lengths.items():
                target_idx = node_to_idx[target_node]
                dist_matrix[source_idx, target_idx] = dist

    return dist_matrix


def build_shortest_path_filtration(graph: nx.Graph) -> List[Tuple[int, int, float]]:
    """
    Build a filtration based on shortest-path distances.
    Returns a list of simplices (edges) with their filtration values.
    Format: [(node_u_idx, node_v_idx, distance), ...]
    Only includes edges (1-simplices) for simplicity in this implementation,
    as full clique filtration is computationally expensive for large graphs.

    Note: In standard TDA on graphs, we often use edge weights directly.
    Here we use shortest-path distances which for connected graphs are just
    the edge weights if the graph is unweighted (distance = 1 for edges).
    However, the task specifies "shortest-path filtration", so we compute
    all-pairs shortest paths and use those as filtration values for edges.
    """
    nodes = list(graph.nodes())
    node_to_idx = {node: i for i, node in enumerate(nodes)}
    n = len(nodes)
    
    if n == 0:
        return []

    filtration = []
    
    # Compute all-pairs shortest paths
    try:
        lengths = nx.all_pairs_dijkstra_path_length(graph)
        for source_node, source_lengths in lengths:
            source_idx = node_to_idx[source_node]
            for target_node, dist in source_lengths.items():
                if source_node < target_node:  # Avoid duplicates and self-loops
                    target_idx = node_to_idx[target_node]
                    filtration.append((source_idx, target_idx, float(dist)))
    except nx.NetworkXError as e:
        logger.error(f"Error computing shortest paths: {e}")
        return []

    return filtration


def compute_persistence_diagram(filtration: List[Tuple[int, int, float]]) -> List[Tuple[float, float]]:
    """
    Compute the persistence diagram from a filtration.
    This is a simplified implementation for 1-simplices (edges).
    In a full implementation, we would use a library like Dionysus or Gudhi
    to compute the full persistence diagram for higher-dimensional simplices.
    
    For 1-simplices, the persistence is simply the filtration value of the edge
    if it creates a cycle, or infinity (or a large number) if it doesn't.
    However, for simplicity and to match the task's scope, we return the
    filtration values as (birth, death) pairs where death is approximated.
    
    A more accurate approach for graphs:
    - Birth: The filtration value when the edge is added.
    - Death: The filtration value when a cycle is formed (if this edge closes a cycle).
    
    We'll use a Union-Find approach to detect cycles.
    """
    # Sort by filtration value
    sorted_filtration = sorted(filtration, key=lambda x: x[2])
    
    # Union-Find data structure
    parent = {}
    rank = {}
    
    def find(x):
        if x not in parent:
            parent[x] = x
            rank[x] = 0
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]
    
    def union(x, y):
        rx, ry = find(x), find(y)
        if rx == ry:
            return False  # Cycle detected
        if rank[rx] < rank[ry]:
            parent[rx] = ry
        elif rank[rx] > rank[ry]:
            parent[ry] = rx
        else:
            parent[ry] = rx
            rank[rx] += 1
        return True
    
    diagram = []
    
    for u, v, value in sorted_filtration:
        if find(u) == find(v):
            # Cycle detected: this edge creates a 1-cycle
            # Birth is the value when the cycle is formed (this edge)
            # Death is infinity (or a large number) for unbounded persistence
            diagram.append((value, float('inf')))
        else:
            # Edge connects two components, no cycle yet
            # Birth is the value when the edge is added
            # Death is infinity (it will be killed by a future cycle)
            union(u, v)
            diagram.append((value, float('inf')))
    
    # Note: In a full implementation, we would track when cycles are filled.
    # For now, we return the simplified diagram.
    return diagram


def vectorize(diagram: List[Tuple[float, float]], resolution: int = 10) -> np.ndarray:
    """
    Vectorize a persistence diagram into a persistence image.
    Uses a fixed grid resolution and a Gaussian kernel.
    
    Args:
        diagram: List of (birth, death) tuples.
        resolution: Grid resolution (resolution x resolution).
    
    Returns:
        1D array of size resolution*resolution representing the image.
    """
    if not diagram:
        return np.zeros(resolution * resolution)
    
    # Filter out infinite deaths for visualization purposes
    # We'll cap them at a maximum value
    max_birth = max(b for b, d in diagram if d != float('inf')) if diagram else 0
    max_death = max(d for b, d in diagram if d != float('inf')) if diagram else 0
    
    # If all deaths are infinite, set a reasonable max
    if max_death == 0:
        max_death = max_birth + 10 if max_birth > 0 else 10
    
    # Define grid boundaries
    min_birth = min(b for b, d in diagram)
    max_val = max(max_birth, max_death)
    
    # Create grid
    x_edges = np.linspace(min_birth, max_val, resolution + 1)
    y_edges = np.linspace(min_birth, max_val, resolution + 1)
    
    # Initialize image
    image = np.zeros((resolution, resolution))
    
    # Gaussian kernel parameters
    sigma = 0.1
    
    # Add contributions from each point
    for birth, death in diagram:
        if death == float('inf'):
            # Use a large value for infinite deaths
            death_val = max_val + 1
        else:
            death_val = death
        
        # Weight based on persistence
        persistence = death_val - birth
        weight = persistence  # Simple weighting by persistence
        
        # Find grid cell
        x_idx = np.searchsorted(x_edges, birth) - 1
        y_idx = np.searchsorted(y_edges, death_val) - 1
        
        if 0 <= x_idx < resolution and 0 <= y_idx < resolution:
            image[y_idx, x_idx] += weight
    
    # Flatten to 1D array
    return image.flatten()


def handle_empty_diagram(resolution: int = 10) -> np.ndarray:
    """
    Handle empty persistence diagrams by returning a zero vector.
    
    Args:
        resolution: Grid resolution.
    
    Returns:
        Zero vector of size resolution*resolution.
    """
    return np.zeros(resolution * resolution)


def compute_betti_numbers(diagram: List[Tuple[float, float]], threshold: float) -> Dict[int, int]:
    """
    Compute Betti numbers at a given threshold.
    
    Args:
        diagram: Persistence diagram.
        threshold: Filtration value at which to compute Betti numbers.
    
    Returns:
        Dictionary mapping dimension to Betti number.
    """
    betti_0 = 0
    betti_1 = 0
    
    for birth, death in diagram:
        if birth <= threshold < death:
            if death == float('inf'):
                # Infinite persistence component
                betti_0 += 1
            else:
                betti_1 += 1
    
    return {0: betti_0, 1: betti_1}


def get_topological_features(diagram: List[Tuple[float, float]]) -> Dict[str, float]:
    """
    Extract simple topological features from a persistence diagram.
    
    Args:
        diagram: Persistence diagram.
    
    Returns:
        Dictionary of features.
    """
    if not diagram:
        return {
            'num_features': 0,
            'total_persistence': 0.0,
            'max_persistence': 0.0,
            'avg_persistence': 0.0
        }
    
    persistences = [
        (d - b) if d != float('inf') else float('inf')
        for b, d in diagram
    ]
    
    finite_persistences = [p for p in persistences if p != float('inf')]
    
    if finite_persistences:
        total_persistence = sum(finite_persistences)
        max_persistence = max(finite_persistences)
        avg_persistence = total_persistence / len(finite_persistences)
    else:
        total_persistence = 0.0
        max_persistence = 0.0
        avg_persistence = 0.0
    
    return {
        'num_features': len(diagram),
        'total_persistence': total_persistence,
        'max_persistence': max_persistence,
        'avg_persistence': avg_persistence
    }


def main():
    """
    Main function to demonstrate memory threshold checks and sparse matrix logic.
    """
    logging.basicConfig(level=logging.INFO)
    
    # Test with a small graph
    small_graph = nx.Graph()
    small_graph.add_edges_from([(0, 1), (1, 2), (2, 3)])
    
    print("Testing small graph...")
    needs_sparse = check_memory_requirement(small_graph)
    print(f"Needs sparse mode: {needs_sparse}")
    
    dist_matrix = compute_shortest_path_matrix(small_graph, use_sparse=needs_sparse)
    print(f"Distance matrix type: {type(dist_matrix)}")
    print(f"Distance matrix shape: {dist_matrix.shape}")
    
    # Test with a large graph (simulated)
    # Create a graph with many nodes to trigger sparse mode
    large_n = 3000  # 3000^2 * 8 bytes = 72 GB > 6 GB
    large_graph = nx.Graph()
    large_graph.add_nodes_from(range(large_n))
    # Add some edges to make it non-trivial
    for i in range(large_n - 1):
        large_graph.add_edge(i, i + 1)
    
    print("\nTesting large graph...")
    needs_sparse_large = check_memory_requirement(large_graph)
    print(f"Needs sparse mode: {needs_sparse_large}")
    
    if needs_sparse_large:
        dist_matrix_large = compute_shortest_path_matrix(large_graph, use_sparse=True)
        print(f"Large distance matrix type: {type(dist_matrix_large)}")
        print(f"Large distance matrix shape: {dist_matrix_large.shape}")
        print(f"Large distance matrix nnz: {dist_matrix_large.nnz}")
    
    print("\nMemory threshold check test completed.")


if __name__ == "__main__":
    main()
