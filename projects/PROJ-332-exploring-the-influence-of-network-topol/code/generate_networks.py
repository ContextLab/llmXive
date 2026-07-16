import networkx as nx
import numpy as np
from typing import Tuple, Dict, Any, Optional, List
import logging
from config import SimulationConfig, load_config, get_simulation_parameters

logger = logging.getLogger(__name__)

def validate_degree_bounds(target_degree: int, min_degree: int = 1, max_degree: int = 20) -> bool:
    """
    Validate that the target average degree is within valid bounds.
    
    Args:
        target_degree: The desired average node degree.
        min_degree: Minimum allowed degree (default 1).
        max_degree: Maximum allowed degree (default 20).
        
    Returns:
        True if valid, raises ValueError if invalid.
    """
    if target_degree < min_degree or target_degree > max_degree:
        raise ValueError(f"Target degree {target_degree} is out of bounds [{min_degree}, {max_degree}].")
    return True

def validate_connection_probability(p: float) -> bool:
    """
    Validate that connection probability is between 0 and 1.
    
    Args:
        p: Connection probability.
        
    Returns:
        True if valid, raises ValueError if invalid.
    """
    if not (0.0 <= p <= 1.0):
        raise ValueError(f"Connection probability {p} must be in [0.0, 1.0].")
    return True

def generate_nanowire_network(N: int, p: float, seed: Optional[int] = None) -> nx.Graph:
    """
    Generate a random nanowire network graph using Erdos-Renyi model.
    
    Args:
        N: Number of nodes.
        p: Connection probability.
        seed: Random seed for reproducibility.
        
    Returns:
        A NetworkX graph representing the nanowire network.
    """
    if seed is not None:
        np.random.seed(seed)
    
    validate_connection_probability(p)
    
    G = nx.erdos_renyi_graph(N, p, seed=seed)
    logger.debug(f"Generated network with N={N}, p={p}, edges={G.number_of_edges()}")
    return G

def generate_nanowire_network_for_degree(N: int, target_degree: int, seed: Optional[int] = None) -> nx.Graph:
    """
    Generate a nanowire network with a target average degree.
    Adjusts connection probability p to approximate the target degree.
    In Erdos-Renyi G(N, p), expected degree is (N-1)*p.
    
    Args:
        N: Number of nodes.
        target_degree: Desired average node degree.
        seed: Random seed for reproducibility.
        
    Returns:
        A NetworkX graph with average degree close to target_degree.
    """
    if seed is not None:
        np.random.seed(seed)
        
    validate_degree_bounds(target_degree)
    
    # Calculate p needed for target degree: p = target_degree / (N - 1)
    if N <= 1:
        raise ValueError("N must be > 1 to generate a network with edges.")
        
    p = target_degree / (N - 1)
    p = min(p, 1.0)  # Cap at 1.0
    
    logger.info(f"Adjusting p={p:.4f} to achieve target degree {target_degree} for N={N}")
    return generate_nanowire_network(N, p, seed)

def calculate_average_degree(G: nx.Graph) -> float:
    """Calculate the average degree of the graph."""
    if G.number_of_nodes() == 0:
        return 0.0
    return 2.0 * G.number_of_edges() / G.number_of_nodes()

def calculate_average_shortest_path_length(G: nx.Graph) -> Optional[float]:
    """
    Calculate the average shortest path length.
    Returns None if graph is disconnected.
    """
    if not nx.is_connected(G):
        return None
    return nx.average_shortest_path_length(G)

def calculate_clustering_coefficient(G: nx.Graph) -> float:
    """Calculate the global clustering coefficient."""
    return nx.clustering(G)

def generate_network_grid(N_values: List[int], p_values: List[float], degree_values: List[int], seeds: List[int]) -> List[Dict[str, Any]]:
    """
    Generate a grid of networks based on provided parameters.
    
    Args:
        N_values: List of node counts.
        p_values: List of connection probabilities.
        degree_values: List of target degrees (if provided, overrides p).
        seeds: List of random seeds.
        
    Returns:
        List of dictionaries containing network metadata.
    """
    results = []
    
    for N in N_values:
        for p in p_values:
            for target_degree in degree_values:
                for seed in seeds:
                    # If target_degree is specified and valid, use it to derive p
                    # Otherwise use the explicit p
                    if target_degree > 0:
                        try:
                            G = generate_nanowire_network_for_degree(N, target_degree, seed)
                        except ValueError:
                            # Skip invalid combinations
                            continue
                    else:
                        G = generate_nanowire_network(N, p, seed)
                    
                    avg_deg = calculate_average_degree(G)
                    is_connected = nx.is_connected(G)
                    
                    results.append({
                        "N": N,
                        "p": p,
                        "target_degree": target_degree,
                        "actual_avg_degree": avg_deg,
                        "is_connected": is_connected,
                        "seed": seed,
                        "num_nodes": G.number_of_nodes(),
                        "num_edges": G.number_of_edges()
                    })
                    
    return results
