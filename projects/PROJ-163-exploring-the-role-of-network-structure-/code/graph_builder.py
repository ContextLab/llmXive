import logging
import networkx as nx
import numpy as np
from typing import List, Tuple, Optional, Dict, Any
from scipy.sparse.csgraph import laplacian

logger = logging.getLogger(__name__)

def build_coupling_graph(coupling_map: List[List[int]]) -> nx.Graph:
    """
    Build an undirected NetworkX graph from a coupling map list.
    
    Args:
        coupling_map: List of [control, target] pairs representing directed edges.
                      Converted to undirected for topology analysis.
    
    Returns:
        nx.Graph: Undirected graph representing qubit connectivity.
    """
    G = nx.Graph()
    for edge in coupling_map:
        if len(edge) >= 2:
            u, v = edge[0], edge[1]
            G.add_edge(u, v)
    return G

def compute_shortest_path_metrics(G: nx.Graph) -> Dict[str, float]:
    """
    Compute shortest-path metrics (average length, diameter).
    Handles disconnected graphs by computing metrics only on the largest connected component.
    
    Args:
        G: NetworkX graph.
    
    Returns:
        Dict with 'avg_shortest_path', 'diameter', 'largest_component_size'.
        If graph is disconnected or empty, path metrics are set to np.inf or 0.
    """
    if G.number_of_nodes() == 0:
        return {
            'avg_shortest_path': float('inf'),
            'diameter': 0,
            'largest_component_size': 0,
            'is_connected': False
        }

    if not nx.is_connected(G):
        # Identify largest connected component
        components = sorted(nx.connected_components(G), key=len, reverse=True)
        largest_cc = G.subgraph(components[0]).copy()
        logger.warning(f"Graph is disconnected. Computing path metrics on largest component (size={len(largest_cc)}).")
        
        size_lcc = len(largest_cc)
        if size_lcc <= 1:
            return {
                'avg_shortest_path': float('inf'),
                'diameter': 0,
                'largest_component_size': size_lcc,
                'is_connected': False
            }
        
        try:
            avg_path = nx.average_shortest_path_length(largest_cc)
            diam = nx.diameter(largest_cc)
        except nx.NetworkXError:
            avg_path = float('inf')
            diam = 0
        
        return {
            'avg_shortest_path': avg_path,
            'diameter': diam,
            'largest_component_size': size_lcc,
            'is_connected': False
        }
    else:
        try:
            avg_path = nx.average_shortest_path_length(G)
            diam = nx.diameter(G)
        except nx.NetworkXError:
            avg_path = float('inf')
            diam = 0
        
        return {
            'avg_shortest_path': avg_path,
            'diameter': diam,
            'largest_component_size': G.number_of_nodes(),
            'is_connected': True
        }

def compute_clustering_and_assortativity(G: nx.Graph) -> Dict[str, float]:
    """
    Compute global clustering coefficient and degree assortativity.
    
    Args:
        G: NetworkX graph.
    
    Returns:
        Dict with 'clustering_coeff' and 'assortativity'.
    """
    if G.number_of_nodes() == 0:
        return {'clustering_coeff': 0.0, 'assortativity': 0.0}
    
    try:
        clustering = nx.average_clustering(G)
    except ZeroDivisionError:
        clustering = 0.0
    
    try:
        assortativity = nx.degree_assortativity_coefficient(G)
    except ZeroDivisionError:
        assortativity = 0.0
    
    return {
        'clustering_coeff': clustering,
        'assortativity': assortativity
    }

def compute_edge_betweenness_and_spectral_gap(G: nx.Graph) -> Dict[str, Any]:
    """
    Compute edge betweenness centrality distribution and spectral gap of the Laplacian.
    Handles disconnected graphs by setting spectral gap to 0.
    
    Args:
        G: NetworkX graph.
    
    Returns:
        Dict with 'edge_betweenness_mean', 'edge_betweenness_std', 'spectral_gap'.
        If disconnected, spectral_gap is 0.
    """
    if G.number_of_nodes() == 0:
        return {
            'edge_betweenness_mean': 0.0,
            'edge_betweenness_std': 0.0,
            'spectral_gap': 0.0
        }

    # Edge Betweenness
    try:
        betweenness = nx.edge_betweenness_centrality(G)
        if betweenness:
            vals = list(betweenness.values())
            eb_mean = float(np.mean(vals))
            eb_std = float(np.std(vals))
        else:
            eb_mean = 0.0
            eb_std = 0.0
    except ZeroDivisionError:
        eb_mean = 0.0
        eb_std = 0.0

    # Spectral Gap (Second smallest eigenvalue of Laplacian)
    spectral_gap = 0.0
    if not nx.is_connected(G):
        logger.warning("Graph is disconnected. Setting spectral gap to 0.")
        spectral_gap = 0.0
    else:
        try:
            # Compute Laplacian matrix
            L = nx.laplacian_matrix(G).astype(float)
            # Get eigenvalues
            eigenvalues = np.linalg.eigvalsh(L.toarray())
            # Sort ascending
            eigenvalues = np.sort(eigenvalues)
            # Spectral gap is the second smallest eigenvalue (index 1)
            # The smallest (index 0) should be ~0 for connected graphs
            if len(eigenvalues) > 1:
                spectral_gap = float(eigenvalues[1])
            else:
                spectral_gap = 0.0
        except Exception as e:
            logger.error(f"Error computing spectral gap: {e}")
            spectral_gap = 0.0

    return {
        'edge_betweenness_mean': eb_mean,
        'edge_betweenness_std': eb_std,
        'spectral_gap': spectral_gap
    }

def process_device_coupling_map(coupling_map: List[List[int]]) -> Dict[str, Any]:
    """
    Orchestrate all graph metric computations for a single device's coupling map.
    Ensures disconnected graph handling is applied correctly.
    
    Args:
        coupling_map: List of [u, v] edges.
    
    Returns:
        Dictionary containing all computed metrics.
    """
    G = build_coupling_graph(coupling_map)
    
    path_metrics = compute_shortest_path_metrics(G)
    cluster_metrics = compute_clustering_and_assortativity(G)
    spectral_metrics = compute_edge_betweenness_and_spectral_gap(G)
    
    result = {
        'num_nodes': G.number_of_nodes(),
        'num_edges': G.number_of_edges(),
        'is_connected': path_metrics['is_connected'],
        **path_metrics,
        **cluster_metrics,
        **spectral_metrics
    }
    
    return result

def main():
    """
    Entry point for standalone execution (e.g., testing with a sample map).
    """
    # Example usage
    sample_map = [[0, 1], [1, 2], [2, 3]]
    logging.basicConfig(level=logging.INFO)
    result = process_device_coupling_map(sample_map)
    logger.info(f"Processed sample map: {result}")

if __name__ == "__main__":
    main()