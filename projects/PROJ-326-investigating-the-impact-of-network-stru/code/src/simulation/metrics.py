"""
Metrics module for simulation analysis.
Implements energy density profile tracking, spatial variance calculation,
and transient phase metric extraction.
"""
import numpy as np
import networkx as nx
import json
import logging
import json
from pathlib import Path

from code.src.utils.config import get_global_config
from code.src.utils.io import ensure_data_directory

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


def extract_transient_metrics(history: List[Dict[str, Any]], transient_steps: int) -> Dict[str, Any]:
    """
    Extract and aggregate metrics specifically for the transient phase of the simulation.

    This function isolates the first N steps (defined by transient_steps) from the
    full simulation history and computes aggregate statistics (mean, std, min, max)
    for the spatial variance during this period.

    Args:
        history: List of metric snapshots from the simulation run.
               Each snapshot should be a dict with 'step', 'spatial_variance', etc.
        transient_steps: Number of initial steps to consider as the transient phase.

    Returns:
        Dictionary containing transient phase statistics:
        {
            "transient_steps": int,
            "steps_analyzed": int,
            "spatial_variance": {
                "mean": float,
                "std": float,
                "min": float,
                "max": float
            },
            "raw_transient_data": [list of step snapshots]
        }
    """
    if not history:
        logger.warning("Empty history provided to transient metric extraction.")
        return {
            "transient_steps": transient_steps,
            "steps_analyzed": 0,
            "spatial_variance": {"mean": 0.0, "std": 0.0, "min": 0.0, "max": 0.0},
            "raw_transient_data": []
        }

    # Filter for transient steps (0 to transient_steps - 1)
    # Note: history is usually 0-indexed by step count
    transient_data = [
        entry for entry in history 
        if entry.get("step", -1) < transient_steps
    ]

    if not transient_data:
        logger.warning(f"No steps found in range [0, {transient_steps}) in history.")
        return {
            "transient_steps": transient_steps,
            "steps_analyzed": 0,
            "spatial_variance": {"mean": 0.0, "std": 0.0, "min": 0.0, "max": 0.0},
            "raw_transient_data": []
        }

    variances = [entry["spatial_variance"] for entry in transient_data]
    
    stats = {
        "transient_steps": transient_steps,
        "steps_analyzed": len(transient_data),
        "spatial_variance": {
            "mean": float(np.mean(variances)),
            "std": float(np.std(variances)),
            "min": float(np.min(variances)),
            "max": float(np.max(variances))
        },
        "raw_transient_data": transient_data
    }

    return stats


def save_transient_metrics(metrics: Dict[str, Any], output_path: str) -> None:
    """
    Save transient phase metrics to a JSON file.

    Args:
        metrics: Dictionary containing transient metrics (output of extract_transient_metrics).
        output_path: File path where the JSON will be saved.
    """
    path = Path(output_path)
    ensure_data_directory(path)
    
    with open(path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Transient metrics saved to {output_path}")


def main() -> None:
    """
    CLI entry point for transient metrics extraction (for testing/debugging).
    Normally called by the simulation runner.
    """
    config = get_global_config()
    transient_steps = config.get("simulation_params", {}).get("transient_steps", 10)
    
    # Example usage:
    # This would typically be called by run_simulation.py with the actual history
    logger.info(f"Transient metrics extraction configured for {transient_steps} steps.")
    logger.info("To use: Call extract_transient_metrics(history, transient_steps) and save_transient_metrics.")

if __name__ == "__main__":
    main()
