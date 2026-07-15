import networkx as nx
import numpy as np
from typing import Tuple, Dict, Any, Optional
import logging

from config import SimulationConfig, load_config, get_simulation_parameters

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def validate_degree_bounds(target_degree: float) -> None:
    """Validate that the target average degree is within physically meaningful bounds."""
    if target_degree < 0:
        raise ValueError(f"Target degree must be non-negative, got {target_degree}")
    # In a simple graph, max degree is N-1, but average degree can be up to N-1.
    # We perform a soft check here; strict enforcement happens during generation logic.
    if target_degree > 1000:
        logger.warning(f"Target degree {target_degree} is unusually high for nanowire networks.")

def validate_connection_probability(p: float) -> None:
    """Validate connection probability p is within [0, 1]."""
    if not 0.0 <= p <= 1.0:
        raise ValueError(f"Connection probability p must be in [0, 1], got {p}")

def generate_nanowire_network(
    N: int,
    p: float,
    target_degree: Optional[float] = None,
    seed: Optional[int] = None
) -> nx.Graph:
    """
    Generate a synthetic nanowire network graph.

    Args:
        N: Number of nodes (nanowire junctions).
        p: Connection probability for Erdos-Renyi generation.
        target_degree: Optional target average degree. If provided, p is adjusted
                       to approximate this degree (p = target_degree / (N-1)).
        seed: Random seed for reproducibility.

    Returns:
        A NetworkX Graph representing the nanowire network.
    """
    if N < 2:
        raise ValueError("N must be at least 2 for a graph.")

    if target_degree is not None:
        validate_degree_bounds(target_degree)
        # Adjust p to achieve target average degree: <k> = p * (N-1)
        # Avoid division by zero if N=1 (handled above)
        effective_p = target_degree / (N - 1)
        if effective_p > 1.0:
            logger.warning(f"Target degree {target_degree} too high for N={N}. Capping p at 1.0.")
            effective_p = 1.0
        validate_connection_probability(effective_p)
        p = effective_p
    else:
        validate_connection_probability(p)

    if seed is not None:
        np.random.seed(seed)

    G = nx.erdos_renyi_graph(N, p, seed=seed)
    logger.info(f"Generated graph with N={N}, p={p:.4f}, edges={G.number_of_edges()}")
    return G

def calculate_average_degree(G: nx.Graph) -> float:
    """
    Calculate the average degree of the graph.

    Formula: sum(degrees) / number_of_nodes = 2 * |E| / |V|

    Returns:
        float: The average degree.
    """
    if G.number_of_nodes() == 0:
        return 0.0
    # NetworkX degree_histogram or direct sum
    degrees = [d for n, d in G.degree()]
    return float(np.mean(degrees))

def calculate_average_shortest_path_length(G: nx.Graph) -> float:
    """
    Calculate the average shortest path length of the connected components.

    Note: If the graph is disconnected, this calculates the average over all
    reachable pairs in each component, or returns infinity if no paths exist.
    For nanowire networks, we typically care about the giant component.
    This implementation computes the average over all pairs in the largest connected component
    to provide a meaningful metric for percolating networks.

    Returns:
        float: The average shortest path length.
    """
    if G.number_of_nodes() == 0:
        return 0.0

    # Check connectivity
    if not nx.is_connected(G):
        # If disconnected, we calculate for the largest connected component
        # as per typical percolation analysis conventions
        largest_cc = max(nx.connected_components(G), key=len)
        subgraph = G.subgraph(largest_cc)
        if len(largest_cc) < 2:
            return 0.0
        try:
            return float(nx.average_shortest_path_length(subgraph))
        except nx.NetworkXError:
            return float('inf')
    else:
        try:
            return float(nx.average_shortest_path_length(G))
        except nx.NetworkXError:
            return float('inf')

def calculate_clustering_coefficient(G: nx.Graph) -> float:
    """
    Calculate the average clustering coefficient of the graph.

    This metric measures the degree to which nodes in a graph tend to cluster together.
    It is the average of the local clustering coefficients of all nodes.

    Returns:
        float: The average clustering coefficient.
    """
    if G.number_of_nodes() == 0:
        return 0.0
    # NetworkX provides a direct function for this
    return float(nx.average_clustering(G))

def generate_network_grid(
    N: int,
    p_values: list,
    target_degrees: list,
    seed_base: int = 42
) -> list:
    """
    Generate a grid of nanowire networks with varying parameters.

    Args:
        N: Number of nodes.
        p_values: List of connection probabilities to test.
        target_degrees: List of target average degrees to test.
        seed_base: Base seed for reproducibility.

    Returns:
        List of tuples: (G, params_dict)
    """
    results = []
    for i, p in enumerate(p_values):
        for j, target_deg in enumerate(target_degrees):
            seed = seed_base + i * len(target_degrees) + j
            G = generate_nanowire_network(N, p, target_degree=target_deg, seed=seed)
            params = {
                'N': N,
                'p': p,
                'target_degree': target_deg,
                'seed': seed
            }
            results.append((G, params))
    return results

# Ensure the module exports the expected public names explicitly if needed,
# though the API surface list implies these are the top-level names.
__all__ = [
    'validate_degree_bounds',
    'validate_connection_probability',
    'generate_nanowire_network',
    'calculate_average_degree',
    'calculate_average_shortest_path_length',
    'calculate_clustering_coefficient',
    'generate_network_grid'
]