import networkx as nx
import numpy as np
from typing import Tuple, Dict, Any, Optional
import logging
from config import SimulationConfig, load_config, get_simulation_parameters

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def validate_degree_bounds(target_degree: float, N: int) -> None:
    """
    Validate that the target average degree is within valid bounds.
    For a graph with N nodes, the maximum possible average degree is N-1.
    The minimum is 0.
    
    Args:
        target_degree: The desired average degree.
        N: Number of nodes in the graph.
        
    Raises:
        ValueError: If target_degree is out of bounds.
    """
    if target_degree < 0:
        raise ValueError(f"Target degree {target_degree} must be non-negative.")
    if target_degree > N - 1:
        raise ValueError(f"Target degree {target_degree} cannot exceed N-1 ({N-1}) for {N} nodes.")
    logger.debug(f"Degree bounds validated: target={target_degree}, N={N}")

def validate_connection_probability(p: float) -> None:
    """
    Validate that the connection probability is within [0, 1].
    
    Args:
        p: Connection probability.
        
    Raises:
        ValueError: If p is not in [0, 1].
    """
    if not (0.0 <= p <= 1.0):
        raise ValueError(f"Connection probability {p} must be in [0, 1].")
    logger.debug(f"Connection probability validated: p={p}")

def generate_nanowire_network(N: int, p: float, target_degree: Optional[float] = None, seed: Optional[int] = None) -> nx.Graph:
    """
    Generate a synthetic nanowire network graph.
    
    If target_degree is provided, the function attempts to find a connection
    probability p' that yields an average degree close to target_degree.
    If p is provided, it generates an Erdos-Renyi graph with that p.
    
    Args:
        N: Number of nodes.
        p: Connection probability (if target_degree is not specified).
        target_degree: Desired average degree (optional).
        seed: Random seed for reproducibility.
        
    Returns:
        A networkx Graph representing the nanowire network.
    """
    if seed is not None:
        np.random.seed(seed)
        
    if target_degree is not None:
        validate_degree_bounds(target_degree, N)
        # For Erdos-Renyi, expected average degree k = (N-1)*p
        # So p = k / (N-1)
        # We clamp p to [0, 1]
        calculated_p = target_degree / (N - 1) if N > 1 else 0.0
        calculated_p = max(0.0, min(1.0, calculated_p))
        logger.info(f"Adjusted connection probability to {calculated_p:.4f} to target degree {target_degree}")
        G = nx.erdos_renyi_graph(N, calculated_p, seed=seed)
    else:
        validate_connection_probability(p)
        G = nx.erdos_renyi_graph(N, p, seed=seed)
        
    logger.info(f"Generated network: N={N}, edges={G.number_of_edges()}, avg_degree={nx.average_degree_centrality(G):.4f}")
    return G

def calculate_average_degree(G: nx.Graph) -> float:
    """
    Calculate the average degree of the graph.
    
    Args:
        G: Networkx graph.
        
    Returns:
        The average degree as a float.
    """
    if G.number_of_nodes() == 0:
        return 0.0
    return sum(d for _, d in G.degree()) / G.number_of_nodes()

def calculate_average_shortest_path_length(G: nx.Graph) -> float:
    """
    Calculate the average shortest path length of the graph.
    Handles disconnected graphs by considering only the largest connected component.
    
    Args:
        G: Networkx graph.
        
    Returns:
        The average shortest path length, or infinity if the graph is disconnected
        or has no paths.
    """
    if G.number_of_nodes() == 0:
        return float('inf')
        
    # Check connectivity
    if not nx.is_connected(G):
        # Use the largest connected component
        largest_cc = max(nx.connected_components(G), key=len)
        subgraph = G.subgraph(largest_cc)
        if subgraph.number_of_nodes() < 2:
            return float('inf')
        try:
            return nx.average_shortest_path_length(subgraph)
        except nx.NetworkXError:
            return float('inf')
    else:
        try:
            return nx.average_shortest_path_length(G)
        except nx.NetworkXError:
            return float('inf')

def calculate_clustering_coefficient(G: nx.Graph) -> float:
    """
    Calculate the global clustering coefficient (transitivity) of the graph.
    This measures the density of triangles in the graph.
    
    Args:
        G: Networkx graph.
        
    Returns:
        The clustering coefficient as a float between 0 and 1.
    """
    if G.number_of_nodes() == 0:
        return 0.0
        
    # Use networkx built-in transitivity which is the global clustering coefficient
    # This is 3 * triangles / number of triplets
    try:
        coeff = nx.transitivity(G)
        logger.debug(f"Calculated clustering coefficient: {coeff}")
        return coeff
    except ZeroDivisionError:
        # No triplets (e.g., no edges or star graph)
        return 0.0

def generate_network_grid(N_values: list, p_values: list, seeds: list) -> list:
    """
    Generate a grid of networks for different parameters.
    
    Args:
        N_values: List of node counts.
        p_values: List of connection probabilities.
        seeds: List of random seeds.
        
    Returns:
        A list of dictionaries containing graph and metadata.
    """
    results = []
    for N in N_values:
        for p in p_values:
            for seed in seeds:
                G = generate_nanowire_network(N, p, seed=seed)
                avg_deg = calculate_average_degree(G)
                avg_spl = calculate_average_shortest_path_length(G)
                clustering = calculate_clustering_coefficient(G)
                
                results.append({
                    'N': N,
                    'p': p,
                    'seed': seed,
                    'avg_degree': avg_deg,
                    'avg_shortest_path_length': avg_spl,
                    'clustering_coefficient': clustering,
                    'graph': G
                })
    return results