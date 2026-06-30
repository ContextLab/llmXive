import networkx as nx
import numpy as np
from typing import Tuple, Dict, Any, Optional
import logging

from config import SimulationConfig, load_config, get_simulation_parameters

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def validate_degree_bounds(target_degree: float, N: int) -> None:
    """
    Validate that the target average degree is within valid bounds for a graph of size N.
    
    Bounds:
      - Lower bound: target_degree >= 0 (technically >= 2/N for connectivity, but we allow 0)
      - Upper bound: target_degree <= N - 1 (simple graph constraint)
    
    Raises:
        ValueError: If target_degree is outside valid bounds.
    """
    if target_degree < 0:
        raise ValueError(
            f"Target average degree must be non-negative. "
            f"Got {target_degree}, but must be >= 0."
        )
    
    max_degree = N - 1
    if target_degree > max_degree:
        raise ValueError(
            f"Target average degree {target_degree} exceeds maximum possible degree "
            f"for a graph with {N} nodes (max = {max_degree}). "
            "In a simple graph, a node can connect to at most N-1 other nodes."
        )
    
    if N < 2 and target_degree > 0:
        raise ValueError(
            f"Cannot achieve target degree {target_degree} with only {N} node(s). "
            "A graph needs at least 2 nodes to have any edges."
        )

    logger.info(
        f"Target degree {target_degree} validated for N={N}. "
        f"Valid range: [0, {max_degree}]."
    )

def validate_connection_probability(p: float, N: int) -> None:
    """
    Validate that the connection probability p is within valid bounds [0, 1].
    
    Args:
        p: Connection probability.
        N: Number of nodes.
    
    Raises:
        ValueError: If p is outside [0, 1].
    """
    if not (0.0 <= p <= 1.0):
        raise ValueError(
            f"Connection probability p must be in range [0, 1]. "
            f"Got {p}."
        )
    
    logger.info(f"Connection probability p={p} validated for N={N}.")

def generate_nanowire_network(
    N: int,
    p: Optional[float] = None,
    target_degree: Optional[float] = None,
    seed: Optional[int] = None
) -> nx.Graph:
    """
    Generate a synthetic nanowire network graph.
    
    Args:
        N: Number of nodes.
        p: Connection probability (if using Erdős-Rényi).
        target_degree: Target average degree (if specified, p is derived).
        seed: Random seed for reproducibility.
        
    Returns:
        A NetworkX Graph object.
        
    Raises:
        ValueError: If both p and target_degree are None, or if inputs are invalid.
    """
    if seed is not None:
        np.random.seed(seed)
    
    if p is None and target_degree is None:
        raise ValueError("Either 'p' (connection probability) or 'target_degree' must be provided.")
    
    if target_degree is not None:
        # Validate bounds before proceeding
        validate_degree_bounds(target_degree, N)
        
        # For Erdős-Rényi, expected average degree is (N-1)*p
        # So p = target_degree / (N-1)
        if N <= 1:
            p = 0.0
        else:
            p = target_degree / (N - 1)
        
        logger.info(f"Derived connection probability p={p:.6f} from target_degree={target_degree}")
    
    # Validate the derived or provided connection probability
    if p is not None:
        validate_connection_probability(p, N)
    
    # Generate Erdős-Rényi graph
    G = nx.erdos_renyi_graph(n=N, p=p, seed=seed)
    
    actual_avg_degree = 2 * G.number_of_edges() / N if N > 0 else 0.0
    logger.info(
        f"Generated graph with N={N}, p={p:.6f}. "
        f"Actual average degree: {actual_avg_degree:.4f}"
    )
    
    return G

def generate_network_grid(
    N_values: list,
    p_values: list,
    target_degrees: list,
    seed_base: int = 42
) -> list:
    """
    Generate a grid of networks for simulation sweeps.
    
    Args:
        N_values: List of node counts.
        p_values: List of connection probabilities.
        target_degrees: List of target average degrees.
        seed_base: Base seed for reproducibility.
        
    Returns:
        List of (G, params) tuples.
    """
    results = []
    seed_counter = 0
    
    for N in N_values:
        for p in p_values:
            G = generate_nanowire_network(N=N, p=p, seed=seed_base + seed_counter)
            results.append((G, {"N": N, "p": p, "target_degree": None}))
            seed_counter += 1
            
        for target_degree in target_degrees:
            G = generate_nanowire_network(
                N=N, 
                target_degree=target_degree, 
                seed=seed_base + seed_counter
            )
            results.append((G, {"N": N, "p": None, "target_degree": target_degree}))
            seed_counter += 1
            
    return results