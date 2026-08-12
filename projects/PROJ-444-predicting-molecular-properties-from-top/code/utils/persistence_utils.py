import logging
from typing import List, Tuple, Optional, Dict, Any, Union
import numpy as np
import networkx as nx
from scipy.spatial.distance import pdist, squareform
from scipy.sparse import csr_matrix, diags
import os
import sys

# Memory threshold for sparse matrix operations (in bytes)
# Default to ~100MB for safety in standard environments
MEMORY_THRESHOLD_BYTES = 100 * 1024 * 1024

def compute_shortest_path_matrix(graph: nx.Graph) -> csr_matrix:
    """
    Computes the shortest path matrix for a given graph using NetworkX.
    Returns a sparse CSR matrix.
    Implements memory threshold checks to handle extremely large molecular weights.
    
    Raises:
        MemoryError: If the computed matrix exceeds the memory threshold.
    """
    num_nodes = graph.number_of_nodes()
    
    if num_nodes == 0:
        return csr_matrix((0, 0))
    
    # Check for disconnected components
    # If the graph is disconnected, shortest path between nodes in different components is infinity.
    # We need to handle this carefully.
    try:
        # Use all_pairs_shortest_path_length for dense calculation first to check feasibility
        # However, for large graphs, this might be too memory intensive.
        # We will attempt to compute the matrix and check size.
        
        # For molecular graphs, the number of nodes is usually small (< 100 atoms).
        # But if a user passes a massive polymer, we need to check.
        
        # Estimate size: num_nodes * num_nodes * 8 bytes (float64)
        estimated_size = num_nodes * num_nodes * 8
        if estimated_size > MEMORY_THRESHOLD_BYTES:
            raise MemoryError(
                f"Shortest path matrix for {num_nodes} nodes would require "
                f"{estimated_size / (1024*1024):.2f} MB, exceeding threshold of "
                f"{MEMORY_THRESHOLD_BYTES / (1024*1024):.2f} MB."
            )
        
        # Compute shortest paths
        lengths = nx.shortest_path_length(graph)
        
        # Convert to dense array first to handle infinity (disconnected)
        # Then convert to sparse
        dist_matrix = np.zeros((num_nodes, num_nodes))
        
        # Map nodes to indices 0..N-1
        node_map = {node: i for i, node in enumerate(graph.nodes())}
        
        for u, v_dict in lengths.items():
            i = node_map[u]
            for v, length in v_dict.items():
                j = node_map[v]
                dist_matrix[i, j] = length
        
        # Handle disconnected components (inf values)
        # For TDA, we typically treat infinity as a very large number or filter them out.
        # Here we replace inf with a large sentinel value (e.g., max finite + 1)
        # or simply ignore pairs that are disconnected if the filtration logic handles it.
        # Standard approach: replace inf with a large value (e.g., 1e9)
        if np.isinf(dist_matrix).any():
            max_val = np.max(dist_matrix[np.isfinite(dist_matrix)]) if np.isfinite(dist_matrix).any() else 0
            dist_matrix[np.isinf(dist_matrix)] = max_val + 1.0
        
        sparse_matrix = csr_matrix(dist_matrix)
        return sparse_matrix
        
    except nx.NetworkXError as e:
        logging.error(f"NetworkX error in shortest path computation: {e}")
        raise
    except MemoryError as e:
        logging.error(f"Memory threshold exceeded: {e}")
        raise

def build_shortest_path_filtration(graph: nx.Graph) -> List[Tuple[int, int, float]]:
    """
    Builds a shortest-path filtration for the given graph.
    Returns a list of simplices (edges) with their filtration values (shortest path distances).
    
    The filtration is based on the shortest path distances between all pairs of nodes.
    We consider the complete graph where edge weights are shortest path distances.
    """
    if graph.number_of_nodes() == 0:
        return []
    
    sparse_matrix = compute_shortest_path_matrix(graph)
    dense_matrix = sparse_matrix.toarray()
    
    filtration = []
    nodes = list(graph.nodes())
    n = len(nodes)
    
    # We only need upper triangle to avoid duplicates and self-loops
    for i in range(n):
        for j in range(i + 1, n):
            dist = dense_matrix[i, j]
            # Add edge (i, j) with weight dist
            # In TDA, we usually add edges in increasing order of weight
            filtration.append((i, j, dist))
    
    # Sort by filtration value (distance)
    filtration.sort(key=lambda x: x[2])
    return filtration

def compute_persistence_diagram(filtration: List[Tuple[int, int, float]]) -> List[Tuple[float, float]]:
    """
    Computes the persistence diagram from the filtration.
    This is a simplified implementation assuming 0-dimensional persistence (connected components).
    For a full TDA implementation, one would use Gudhi or Dionysus.
    Here we simulate the persistence of connected components merging.
    
    Returns a list of (birth, death) tuples.
    """
    if not filtration:
        return []
    
    # Use Union-Find to track connected components
    parent = list(range(len(set([u for u, v, w in filtration] + [v for u, v, w in filtration]))))
    # Note: This is a simplified approach. A robust implementation would map node indices properly.
    # Since we are dealing with a complete graph derived from shortest paths,
    # the "birth" of a component is when a node is first encountered, and "death" is when it merges.
    
    # Actually, for a complete graph with edge weights as distances:
    # We process edges in order.
    # If an edge connects two previously unconnected components, it merges them.
    # The "death" of the component with the later birth time is the current edge weight.
    # The "birth" times of components are the weights of the edges that created them?
    # No, in 0-dim persistence:
    # - Each node is born at time 0 (or the weight of the first edge connected to it? No, standard is 0).
    # - When two components merge, the one with the later "birth" (which is 0 for all) dies?
    # This is tricky with shortest path metric.
    
    # Let's use a standard approach for 0-dim persistence on a weighted graph:
    # Birth of a component = 0 (start of filtration).
    # Death of a component = weight of the edge that merges it into a larger component.
    # The last remaining component dies at infinity.
    
    # However, the task asks for "shortest-path filtration".
    # This usually implies we are looking at the metric space of the graph.
    # Let's assume we are computing 0-dim persistence of the Rips complex built on the graph nodes
    # with distances from the shortest path matrix.
    
    # Since the graph is already connected (or we handled disconnected),
    # we just need to find when components merge.
    
    # Re-implementing Union-Find properly
    unique_nodes = set()
    for u, v, w in filtration:
        unique_nodes.add(u)
        unique_nodes.add(v)
    
    node_list = sorted(list(unique_nodes))
    node_to_idx = {node: i for i, node in enumerate(node_list)}
    n_nodes = len(node_list)
    
    parent = list(range(n_nodes))
    rank = [0] * n_nodes
    
    def find(x):
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]
    
    def union(x, y):
        rx, ry = find(x), find(y)
        if rx == ry:
            return False
        if rank[rx] < rank[ry]:
            parent[rx] = ry
        elif rank[rx] > rank[ry]:
            parent[ry] = rx
        else:
            parent[ry] = rx
            rank[rx] += 1
        return True
    
    diagram = []
    # Birth times for all components are 0
    # We track which components exist.
    # Actually, in standard persistence:
    # - Each point starts as a component at birth=0.
    # - When two components merge, one dies at the current filtration value.
    # - The survivor continues.
    # - The last component dies at infinity.
    
    # But we have a filtration of edges.
    # We iterate through edges.
    # If an edge connects two different components, we merge them.
    # The component that "dies" is the one that was created later?
    # In 0-dim, all are created at 0. So we just merge.
    # The "death" of a component is the weight of the edge that merges it into another.
    # We need to track the "death" of each component.
    # Since all are born at 0, we just need to record the death time for each merge.
    
    # Let's track the "representative" of each component.
    # When merging A and B, we record (0, weight) for one of them?
    # Standard algorithm:
    # Sort edges by weight.
    # Initialize DSU.
    # For each edge (u, v) with weight w:
    #   root_u = find(u), root_v = find(v)
    #   if root_u != root_v:
    #       union(root_u, root_v)
    #       record a death for one of the components?
    #       Actually, we record (birth, death).
    #       Since all born at 0, we record (0, w) for the component that disappears.
    #       But which one? It doesn't matter for the set of pairs, as long as we count correctly.
    #       However, we need to ensure we have N-1 pairs for N nodes (if connected).
    
    # Correct logic:
    # We have N nodes. We expect N-1 merges to form one component.
    # Each merge produces one death event.
    # The last component has death = infinity.
    
    # We need to track the "birth" of each component.
    # Since all start at 0, birth=0 for all.
    # But wait, if the graph is disconnected initially?
    # The problem says "shortest-path filtration".
    # If the graph is disconnected, we have multiple components at the end.
    # We should handle that.
    
    # Let's assume the graph is connected for now (handled in T011).
    # If not, we have multiple components at the end, each dying at infinity.
    
    # Implementation:
    # We track the "birth" of each component. Initially, each node is a component born at 0.
    # When merging component A and B, the one with the later birth dies at w.
    # Since all are 0, we can arbitrarily say A dies at w, B survives.
    # But to be precise, we need to know the birth time.
    # Let's store (birth_time, representative) for each root.
    
    component_birth = {i: 0 for i in range(n_nodes)}
    
    for u, v, w in filtration:
        idx_u = node_to_idx[u]
        idx_v = node_to_idx[v]
        
        root_u = find(idx_u)
        root_v = find(idx_v)
        
        if root_u != root_v:
            # Merge
            birth_u = component_birth[root_u]
            birth_v = component_birth[root_v]
            
            # The component with the later birth dies at w
            if birth_u > birth_v:
                diagram.append((birth_u, w))
                # root_v survives, its birth remains birth_v
                union(root_u, root_v)
                # The new root is root_v (or whatever union returns, but we need to update birth)
                # Let's force root_v to be the parent
                parent[root_u] = root_v
                # component_birth[root_v] remains birth_v
            else:
                diagram.append((birth_v, w))
                union(root_u, root_v)
                parent[root_v] = root_u
                # component_birth[root_u] remains birth_u
    
    # Any remaining components die at infinity
    roots = set(find(i) for i in range(n_nodes))
    for root in roots:
        diagram.append((component_birth[root], float('inf')))
    
    return diagram

def handle_empty_diagram(diagram: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
    """
    Handles empty persistence diagrams.
    Returns an empty list or a zero-vector representation if needed.
    """
    if not diagram:
        return []
    
    # Filter out infinite deaths if necessary, or keep them
    # For vectorization, we might need to cap infinity
    # This function just returns the diagram as is, or cleans it
    cleaned = []
    for birth, death in diagram:
        if birth < death:
            cleaned.append((birth, death))
    return cleaned

def compute_betti_numbers(diagram: List[Tuple[float, float]], threshold: float) -> int:
    """
    Computes the Betti number (number of connected components) at a given threshold.
    """
    count = 0
    for birth, death in diagram:
        if birth <= threshold < death:
            count += 1
    return count

def get_topological_features(diagram: List[Tuple[float, float]]) -> Dict[str, Any]:
    """
    Extracts topological features from a persistence diagram.
    Returns a dictionary of features.
    """
    if not diagram:
        return {
            "persistence_entropy": 0.0,
            "max_persistence": 0.0,
            "total_persistence": 0.0,
            "num_features": 0
        }
    
    persistences = [death - birth for birth, death in diagram if death != float('inf')]
    if not persistences:
        return {
            "persistence_entropy": 0.0,
            "max_persistence": 0.0,
            "total_persistence": 0.0,
            "num_features": len(diagram) # Count infinite ones? Or just finite?
        }
    
    total_persistence = sum(persistences)
    max_persistence = max(persistences) if persistences else 0.0
    
    # Persistence entropy
    if total_persistence > 0:
        probs = [p / total_persistence for p in persistences]
        entropy = -sum(p * np.log(p) if p > 0 else 0 for p in probs)
    else:
        entropy = 0.0
    
    return {
        "persistence_entropy": entropy,
        "max_persistence": max_persistence,
        "total_persistence": total_persistence,
        "num_features": len(diagram)
    }

def main():
    """
    Main function for testing persistence utilities.
    """
    # Create a simple graph
    G = nx.Graph()
    G.add_edges_from([(0, 1, {'weight': 1}), (1, 2, {'weight': 2}), (0, 2, {'weight': 3})])
    
    print("Computing shortest path matrix...")
    mat = compute_shortest_path_matrix(G)
    print(f"Matrix shape: {mat.shape}")
    print(f"Matrix:\n{mat.toarray()}")
    
    print("\nBuilding filtration...")
    filt = build_shortest_path_filtration(G)
    print(f"Filtration: {filt}")
    
    print("\nComputing persistence diagram...")
    diag = compute_persistence_diagram(filt)
    print(f"Diagram: {diag}")
    
    print("\nHandling empty diagram...")
    empty_diag = handle_empty_diagram(diag)
    print(f"Cleaned: {empty_diag}")
    
    print("\nComputing features...")
    features = get_topological_features(diag)
    print(f"Features: {features}")

if __name__ == "__main__":
    main()
