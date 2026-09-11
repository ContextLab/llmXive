import logging
import networkx as nx
import numpy as np
from typing import List, Tuple, Optional, Dict, Any
from scipy.sparse.csgraph import laplacian

logger = logging.getLogger(__name__)


def build_coupling_graph(coupling_map: List[List[int]]) -> nx.Graph:
    """
    Build an undirected NetworkX graph from a coupling map.

    Args:
        coupling_map: List of [source, target] pairs representing directed edges.

    Returns:
        An undirected nx.Graph.
    """
    G = nx.Graph()
    for edge in coupling_map:
        if len(edge) != 2:
            logger.warning(f"Invalid edge format in coupling map: {edge}")
            continue
        u, v = edge
        G.add_edge(u, v)
    return G


def compute_shortest_path_metrics(G: nx.Graph) -> Dict[str, float]:
    """
    Compute average shortest-path length and diameter.

    Handles disconnected graphs by computing metrics only on the largest
    connected component. If the graph is empty or has no nodes, returns
    infinity for path metrics.

    Args:
        G: A NetworkX graph.

    Returns:
        Dictionary with keys:
            - 'avg_shortest_path': float (or inf)
            - 'diameter': float (or inf)
    """
    if G.number_of_nodes() == 0:
        return {'avg_shortest_path': float('inf'), 'diameter': float('inf')}

    # Identify connected components
    components = list(nx.connected_components(G))

    if not components:
        return {'avg_shortest_path': float('inf'), 'diameter': float('inf')}

    # Select the largest connected component for path-length metrics
    largest_cc = max(components, key=len)
    subgraph = G.subgraph(largest_cc)

    # Compute metrics on the largest component
    try:
        avg_path = nx.average_shortest_path_length(subgraph)
    except nx.NetworkXError:
        avg_path = float('inf')

    try:
        diameter = nx.diameter(subgraph)
    except nx.NetworkXError:
        diameter = float('inf')

    return {
        'avg_shortest_path': avg_path,
        'diameter': diameter
    }


def compute_clustering_and_assortativity(G: nx.Graph) -> Dict[str, float]:
    """
    Compute global clustering coefficient and degree assortativity.

    Args:
        G: A NetworkX graph.

    Returns:
        Dictionary with keys:
            - 'clustering_coefficient': float
            - 'degree_assortativity': float
    """
    clustering = nx.average_clustering(G)
    assortativity = nx.degree_assortativity_coefficient(G)
    return {
        'clustering_coefficient': clustering,
        'degree_assortativity': assortativity
    }


def compute_edge_betweenness_and_spectral_gap(G: nx.Graph) -> Dict[str, Any]:
    """
    Compute edge betweenness centrality distribution and spectral gap.

    Handles disconnected graphs:
        - Sets spectral gap to 0.
        - Computes edge betweenness on the entire graph (networkx handles this).

    Args:
        G: A NetworkX graph.

    Returns:
        Dictionary with keys:
            - 'edge_betweenness_mean': float
            - 'edge_betweenness_max': float
            - 'spectral_gap': float (0.0 if disconnected)
            - 'is_connected': bool
    """
    # Check connectivity
    is_connected = nx.is_connected(G)
    num_nodes = G.number_of_nodes()

    # Compute edge betweenness
    edge_betweenness = nx.edge_betweenness_centrality(G)
    if not edge_betweenness:
        mean_betweenness = 0.0
        max_betweenness = 0.0
    else:
        values = list(edge_betweenness.values())
        mean_betweenness = float(np.mean(values))
        max_betweenness = float(np.max(values))

    # Compute spectral gap
    # Spectral gap = lambda_2 (second smallest eigenvalue of Laplacian)
    # If disconnected, lambda_2 = 0
    if not is_connected or num_nodes < 2:
        spectral_gap = 0.0
    else:
        try:
            # Compute Laplacian matrix
            L = laplacian(G, normalized=False)
            eigenvalues = np.linalg.eigvalsh(L.toarray() if hasattr(L, 'toarray') else L)
            # Sort eigenvalues
            eigenvalues = np.sort(eigenvalues)
            # The first eigenvalue should be ~0 for Laplacian
            # Spectral gap is the second smallest
            if len(eigenvalues) >= 2:
                spectral_gap = float(eigenvalues[1] - eigenvalues[0])
                # Ensure non-negative due to numerical precision
                spectral_gap = max(0.0, spectral_gap)
            else:
                spectral_gap = 0.0
        except Exception as e:
            logger.warning(f"Failed to compute spectral gap for graph with {num_nodes} nodes: {e}")
            spectral_gap = 0.0

    return {
        'edge_betweenness_mean': mean_betweenness,
        'edge_betweenness_max': max_betweenness,
        'spectral_gap': spectral_gap,
        'is_connected': is_connected
    }


def process_device_coupling_map(coupling_map: List[List[int]]) -> Dict[str, Any]:
    """
    Process a device's coupling map to compute all graph metrics.

    This function orchestrates the metric computation, ensuring that
    disconnected graph handling is applied consistently.

    Args:
        coupling_map: List of [source, target] pairs.

    Returns:
        Dictionary containing all computed metrics.
    """
    G = build_coupling_graph(coupling_map)

    path_metrics = compute_shortest_path_metrics(G)
    cluster_metrics = compute_clustering_and_assortativity(G)
    betweenness_metrics = compute_edge_betweenness_and_spectral_gap(G)

    return {
        **path_metrics,
        **cluster_metrics,
        **betweenness_metrics,
        'num_nodes': G.number_of_nodes(),
        'num_edges': G.number_of_edges()
    }


def main():
    """
    Entry point for standalone execution.
    Demonstrates processing a sample coupling map.
    """
    logging.basicConfig(level=logging.INFO)

    # Sample coupling map (linear chain with a disconnected node)
    sample_map = [
        [0, 1], [1, 2], [2, 3],  # Connected component 1
        [4, 5],                   # Connected component 2
        # Node 6 is isolated
    ]

    # Add an isolated node manually to the graph logic
    # Note: build_coupling_graph only adds nodes present in edges.
    # To simulate an isolated node, we'd need to pass node count or explicit nodes.
    # For this demo, we just use the edges provided.

    results = process_device_coupling_map(sample_map)

    logger.info(f"Computed metrics: {results}")

    # Verify disconnected handling
    if not results['is_connected']:
        assert results['spectral_gap'] == 0.0, "Spectral gap must be 0 for disconnected graphs"
        logger.info("Correctly identified disconnected graph and set spectral gap to 0.")

    # Verify path metrics are computed on largest component
    logger.info(f"Average shortest path (largest CC): {results['avg_shortest_path']}")
    logger.info(f"Diameter (largest CC): {results['diameter']}")


if __name__ == '__main__':
    main()