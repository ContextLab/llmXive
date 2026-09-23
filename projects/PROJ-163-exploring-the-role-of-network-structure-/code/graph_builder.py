import logging
import networkx as nx
import numpy as np
from typing import List, Tuple, Optional, Dict, Any
from scipy.sparse.csgraph import laplacian
from models import QubitDevice, GraphMetric

logger = logging.getLogger(__name__)

def build_coupling_graph(coupling_map: List[Tuple[int, int]], num_qubits: int) -> nx.Graph:
    """
    Build an undirected NetworkX graph from a coupling map.
    
    Args:
        coupling_map: List of (control, target) tuples representing directed edges.
        num_qubits: Total number of qubits (ensures isolated qubits are included if needed).
        
    Returns:
        nx.Graph: Undirected graph representing the connectivity.
    """
    G = nx.Graph()
    G.add_nodes_from(range(num_qubits))
    
    for edge in coupling_map:
        # Treat as undirected for topology analysis
        G.add_edge(edge[0], edge[1])
        
    return G

def compute_shortest_path_metrics(G: nx.Graph) -> Dict[str, float]:
    """
    Compute average shortest-path length and diameter.
    
    Handles disconnected graphs by computing metrics only for the largest connected component.
    
    Args:
        G: NetworkX graph.
        
    Returns:
        Dict with 'avg_shortest_path' and 'diameter'. 
        If graph is disconnected, metrics are computed on the largest component.
        If no edges exist, returns 0.0.
    """
    if G.number_of_edges() == 0:
        return {"avg_shortest_path": 0.0, "diameter": 0.0}
    
    # Handle disconnected graphs: use largest connected component
    if not nx.is_connected(G):
        largest_cc = max(nx.connected_components(G), key=len)
        subgraph = G.subgraph(largest_cc)
        logger.warning(f"Graph is disconnected. Computing path metrics on largest component (size: {len(largest_cc)}).")
    else:
        subgraph = G
    
    try:
        avg_path = nx.average_shortest_path_length(subgraph)
        diameter = nx.diameter(subgraph)
    except nx.NetworkXError as e:
        logger.error(f"Error computing path metrics: {e}")
        return {"avg_shortest_path": float('inf'), "diameter": float('inf')}
        
    return {"avg_shortest_path": avg_path, "diameter": diameter}

def compute_clustering_and_assortativity(G: nx.Graph) -> Dict[str, float]:
    """
    Compute global clustering coefficient and degree assortativity.
    
    Args:
        G: NetworkX graph.
        
    Returns:
        Dict with 'clustering_coeff' and 'assortativity'.
    """
    clustering = nx.average_clustering(G)
    assortativity = nx.degree_assortativity_coefficient(G)
    return {"clustering_coeff": clustering, "assortativity": assortativity}

def compute_edge_betweenness_and_spectral_gap(G: nx.Graph) -> Dict[str, float]:
    """
    Compute edge betweenness centrality distribution and spectral gap of Laplacian.
    
    For disconnected graphs, spectral gap is set to 0.
    
    Args:
        G: NetworkX graph.
        
    Returns:
        Dict with 'edge_betweenness_mean', 'edge_betweenness_std', and 'spectral_gap'.
    """
    # Edge betweenness
    if G.number_of_edges() == 0:
        edge_betweenness_mean = 0.0
        edge_betweenness_std = 0.0
    else:
        edge_bet = nx.edge_betweenness_centrality(G)
        values = list(edge_bet.values())
        edge_betweenness_mean = float(np.mean(values))
        edge_betweenness_std = float(np.std(values))
    
    # Spectral gap of Laplacian
    # Laplacian L = D - A
    # Spectral gap is the second smallest eigenvalue (lambda_1)
    # If disconnected, lambda_1 = 0
    if not nx.is_connected(G):
        spectral_gap = 0.0
        logger.info("Graph is disconnected. Setting spectral gap to 0.")
    else:
        try:
            L = nx.laplacian_matrix(G).astype(float).todense()
            eigenvalues = np.linalg.eigvalsh(L)
            # Sort eigenvalues: lambda_0 = 0, lambda_1 is the spectral gap
            eigenvalues = np.sort(eigenvalues)
            spectral_gap = float(eigenvalues[1]) if len(eigenvalues) > 1 else 0.0
        except Exception as e:
            logger.error(f"Error computing spectral gap: {e}")
            spectral_gap = float('nan')
    
    return {
        "edge_betweenness_mean": edge_betweenness_mean,
        "edge_betweenness_std": edge_betweenness_std,
        "spectral_gap": spectral_gap
    }

def process_device_coupling_map(device_id: str, coupling_map: List[Tuple[int, int]], num_qubits: int) -> Dict[str, Any]:
    """
    Process a device's coupling map to compute all graph metrics.
    
    Args:
        device_id: Identifier for the device.
        coupling_map: List of (control, target) edges.
        num_qubits: Number of qubits on the device.
        
    Returns:
        Dict containing device_id and all computed metrics.
    """
    G = build_coupling_graph(coupling_map, num_qubits)
    
    path_metrics = compute_shortest_path_metrics(G)
    cluster_metrics = compute_clustering_and_assortativity(G)
    spectral_metrics = compute_edge_betweenness_and_spectral_gap(G)
    
    result = {
        "device_id": device_id,
        "avg_shortest_path": path_metrics["avg_shortest_path"],
        "diameter": path_metrics["diameter"],
        "clustering_coeff": cluster_metrics["clustering_coeff"],
        "assortativity": cluster_metrics["assortativity"],
        "edge_betweenness_mean": spectral_metrics["edge_betweenness_mean"],
        "edge_betweenness_std": spectral_metrics["edge_betweenness_std"],
        "spectral_gap": spectral_metrics["spectral_gap"],
        "is_connected": nx.is_connected(G) if G.number_of_nodes() > 0 else False
    }
    
    return result

def main():
    """
    Main entry point for testing graph builder logic.
    """
    logging.basicConfig(level=logging.INFO)
    
    # Example usage with a mock coupling map (line graph: 0-1-2-3)
    mock_coupling_map = [(0, 1), (1, 2), (2, 3)]
    num_qubits = 4
    
    result = process_device_coupling_map("test_device", mock_coupling_map, num_qubits)
    logger.info(f"Graph metrics: {result}")

if __name__ == "__main__":
    main()
