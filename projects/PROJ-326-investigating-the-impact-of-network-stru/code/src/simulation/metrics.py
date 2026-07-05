"""
Metrics module for simulation analysis.
Implements energy density profile tracking and spatial variance calculation.
"""
import numpy as np
import networkx as nx
from typing import List, Dict, Any, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


def compute_energy_density_profile(spins: np.ndarray, graph: nx.Graph) -> np.ndarray:
    """
    Compute the local energy density for each node in the network.

    For an Ising model with Hamiltonian H = -J * sum_{<i,j>} s_i * s_j,
    the local energy contribution for node i is:
    E_i = -J * sum_{j in neighbors(i)} s_i * s_j

    Args:
        spins: 1D numpy array of spin values (+1 or -1) for each node.
               Index corresponds to node ID (assuming contiguous 0..N-1).
        graph: NetworkX graph representing the network topology.

    Returns:
        1D numpy array of energy density values for each node.
    """
    if spins.shape[0] != len(graph):
        raise ValueError(f"Spins array length ({spins.shape[0]}) must match graph node count ({len(graph)})")

    n_nodes = len(graph)
    energy_density = np.zeros(n_nodes, dtype=np.float64)

    # Assume J=1 for simplified dynamics as per T024 context
    J = 1.0

    # Convert graph to adjacency list for faster iteration
    for node, neighbors in graph.adj.items():
        if node >= n_nodes or node < 0:
            continue
        
        spin_i = spins[node]
        neighbor_sum = 0.0
        
        for neighbor in neighbors:
            if neighbor >= n_nodes or neighbor < 0:
                continue
            neighbor_sum += spins[neighbor]
        
        # Local energy: -J * s_i * sum(s_j)
        energy_density[node] = -J * spin_i * neighbor_sum

    return energy_density


def compute_spatial_variance(energy_density: np.ndarray) -> float:
    """
    Calculate the spatial variance of the energy density profile across the network.

    This metric quantifies the heterogeneity of energy distribution.
    Increasing spatial variance indicates growing spatial correlations
    or phase separation in the spin system.

    Args:
        energy_density: 1D numpy array of energy density values per node.

    Returns:
        Float representing the variance of the energy density distribution.
    """
    if energy_density.size == 0:
        logger.warning("Empty energy density array provided to spatial variance calculation.")
        return 0.0

    variance = np.var(energy_density, ddof=0) # Population variance
    return float(variance)


def track_metrics_history(history: List[Dict[str, Any]], step: int, spins: np.ndarray, graph: nx.Graph) -> Dict[str, Any]:
    """
    Compute and append metrics for a single simulation step.

    Args:
        history: List of previous metric snapshots.
        step: Current simulation time step.
        spins: Current spin configuration.
        graph: Network topology.

    Returns:
        Dictionary containing step metrics (energy density profile, spatial variance).
    """
    energy_density = compute_energy_density_profile(spins, graph)
    spatial_variance = compute_spatial_variance(energy_density)

    snapshot = {
        "step": step,
        "spatial_variance": spatial_variance,
        "energy_density_profile": energy_density.tolist()
    }

    history.append(snapshot)
    return snapshot


def validate_metrics(metrics: Dict[str, Any]) -> bool:
    """
    Validate that computed metrics are numerically stable and within expected bounds.

    Args:
        metrics: Dictionary containing 'spatial_variance' and 'energy_density_profile'.

    Returns:
        True if valid, False otherwise.
    """
    if "spatial_variance" not in metrics:
        logger.error("Missing 'spatial_variance' in metrics.")
        return False
    
    if "energy_density_profile" not in metrics:
        logger.error("Missing 'energy_density_profile' in metrics.")
        return False

    var = metrics["spatial_variance"]
    if not np.isfinite(var):
        logger.error(f"Spatial variance is not finite: {var}")
        return False

    if var < 0:
        logger.error(f"Spatial variance is negative: {var}")
        return False

    profile = np.array(metrics["energy_density_profile"])
    if not np.all(np.isfinite(profile)):
        logger.error("Energy density profile contains non-finite values.")
        return False

    return True