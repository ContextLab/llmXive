"""
Kuramoto Oscillator Simulation Module.

Implements the Kuramoto model dynamics, order parameter calculation,
and critical coupling strength detection.
"""
from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from scipy.integrate import odeint

# Import shared utilities
# Note: We use the tolerant logging_utils provided in the project
from utils.logging_utils import get_logger

# Import graph utilities if needed (though we mostly work with adjacency matrices here)
# from utils.graph_utils import is_connected # Not strictly needed here as we assume valid input

# Global logger instance
logger = get_logger(__name__)


def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from JSON file."""
    path = Path(config_path)
    if not path.exists():
        logger.log("config_missing", path=str(path))
        # Return fallback config to allow script to run in test environments if needed
        # However, per task T021, we should warn and proceed with fallbacks if config is missing/error
        return {
            "time_steps": 1000,
            "n_topologies": 10,
            "run_count": 10,
            "SC_003_VIOLATION": False,
            "error": "CONFIG_MISSING_FALLBACK"
        }
    with open(path, "r") as f:
        return json.load(f)


def kuramoto_derivative(
    theta: np.ndarray,
    t: float,
    adj_matrix: np.ndarray,
    omega: np.ndarray,
    K: float
) -> np.ndarray:
    """
    Compute the derivative of phases for the Kuramoto model.

    d(theta_i)/dt = omega_i + (K/N) * sum_{j} A_ij * sin(theta_j - theta_i)

    Args:
        theta: Current phase angles (N,)
        t: Current time (unused, required by odeint)
        adj_matrix: Adjacency matrix of the network (N, N)
        omega: Natural frequencies of oscillators (N,)
        K: Global coupling strength

    Returns:
        dtheta: Time derivative of phases (N,)
    """
    N = len(theta)
    # Vectorized calculation of the coupling term
    # sin(theta_j - theta_i) -> sin(theta_j)cos(theta_i) - cos(theta_j)sin(theta_i)
    # But direct matrix multiplication is clearer:
    # coupling_i = sum_j A_ij * sin(theta_j - theta_i)

    # Calculate phase differences matrix
    # theta_diff[i, j] = theta[j] - theta[i]
    theta_diff = theta[np.newaxis, :] - theta[:, np.newaxis]
    sin_diff = np.sin(theta_diff)

    # Multiply by adjacency matrix
    # coupling_term[i] = sum_j A_ij * sin(theta_j - theta_i)
    coupling_term = adj_matrix @ sin_diff

    dtheta = omega + (K / N) * coupling_term
    return dtheta


def calculate_order_parameter(theta: np.ndarray) -> Tuple[float, complex]:
    """
    Calculate the complex order parameter R * e^(i*psi).

    R = | (1/N) * sum_{j} e^(i * theta_j) |
    psi = arg( (1/N) * sum_{j} e^(i * theta_j) )

    Args:
        theta: Array of phase angles (N,)

    Returns:
        R: Magnitude of the order parameter (0.0 to 1.0)
        psi: Phase of the order parameter
    """
    N = len(theta)
    z = np.mean(np.exp(1j * theta))
    R = np.abs(z)
    psi = np.angle(z)
    return R, psi


def simulate_kuramoto(
    adj_matrix: np.ndarray,
    omega: np.ndarray,
    K: float,
    t_eval: np.ndarray,
    seed: int = 42
) -> Tuple[np.ndarray, float]:
    """
    Simulate Kuramoto dynamics for a given coupling strength K.

    Args:
        adj_matrix: Adjacency matrix (N, N)
        omega: Natural frequencies (N,)
        K: Coupling strength
        t_eval: Time points for integration
        seed: Random seed for initial phases

    Returns:
        theta_final: Final phase angles at t_eval[-1]
        R_final: Final order parameter magnitude
    """
    N = len(omega)
    np.random.seed(seed)
    theta_0 = np.random.uniform(0, 2 * np.pi, N)

    # Solve ODE
    sol = odeint(kuramoto_derivative, theta_0, t_eval, args=(adj_matrix, omega, K))

    # Calculate order parameter at the final time step
    theta_final = sol[-1]
    R_final, _ = calculate_order_parameter(theta_final)

    return theta_final, R_final


def find_critical_coupling_binary_search(
    adj_matrix: np.ndarray,
    omega: np.ndarray,
    t_eval: np.ndarray,
    K_min: float = 0.0,
    K_max: float = 10.0,
    tol: float = 0.05,
    max_iter: int = 20,
    threshold: float = 0.5,
    seed: int = 42
) -> Tuple[float, str]:
    """
    Find the critical coupling strength Kc using binary search.

    Kc is defined as the minimum K such that the order parameter R >= threshold.

    Args:
        adj_matrix: Adjacency matrix
        omega: Natural frequencies
        t_eval: Time points
        K_min: Lower bound for search
        K_max: Upper bound for search
        tol: Tolerance for Kc convergence
        max_iter: Maximum iterations
        threshold: Order parameter threshold for synchronization
        seed: Random seed

    Returns:
        Kc: Estimated critical coupling
        status: 'converged' or 'failed'
    """
    K_low = K_min
    K_high = K_max
    Kc = K_max
    status = "failed"

    for i in range(max_iter):
        K_mid = (K_low + K_high) / 2.0
        _, R = simulate_kuramoto(adj_matrix, omega, K_mid, t_eval, seed)

        if R >= threshold:
            Kc = K_mid
            K_high = K_mid
            # Check convergence
            if (K_high - K_low) < tol:
                status = "converged"
                break
        else:
            K_low = K_mid

    if status == "failed" and (K_high - K_low) >= tol:
        # If we didn't converge within max_iter, return the best estimate
        status = "max_iter_reached"

    return Kc, status


def find_critical_coupling_linear_sweep(
    adj_matrix: np.ndarray,
    omega: np.ndarray,
    t_eval: np.ndarray,
    K_range: np.ndarray,
    threshold: float = 0.5,
    seed: int = 42
) -> Tuple[float, str]:
    """
    Fallback method: Linear sweep to find Kc.

    Args:
        adj_matrix: Adjacency matrix
        omega: Natural frequencies
        t_eval: Time points
        K_range: Array of K values to test
        threshold: Order parameter threshold
        seed: Random seed

    Returns:
        Kc: Estimated critical coupling
        status: 'found' or 'failed'
    """
    for K in K_range:
        _, R = simulate_kuramoto(adj_matrix, omega, K, t_eval, seed)
        if R >= threshold:
            return K, "found"
    return float('nan'), "failed"


def run_simulation_batch(
    topology_paths: List[str],
    config: Dict[str, Any],
    output_path: str
) -> None:
    """
    Run simulation batch for all valid topologies.

    Args:
        topology_paths: List of paths to topology files
        config: Configuration dictionary
        output_path: Path for output CSV
    """
    time_steps = config.get("time_steps", 1000)
    # Define time evaluation points
    t_eval = np.linspace(0, 10, time_steps)

    # Threshold for synchronization (can be made configurable)
    threshold = 0.5

    results = []

    for path in topology_paths:
        try:
            import networkx as nx
            G = nx.read_gpickle(path)
            adj_matrix = nx.to_numpy_array(G)
            N = G.number_of_nodes()

            # Generate natural frequencies (random uniform for now, or from data if available)
            # Standard Kuramoto often uses uniform distribution or specific distribution
            # Here we use uniform [0, 1] for simplicity unless specified
            omega = np.random.uniform(0, 1, N)
            # Set seed for reproducibility if needed, but we might want to vary it for stability checks
            # For this task, we use a fixed seed or derive from topology_id
            seed = 42 # Default seed, can be varied

            # Binary search for Kc
            Kc_binary, status_binary = find_critical_coupling_binary_search(
                adj_matrix, omega, t_eval, seed=seed
            )

            # If binary search failed, try linear sweep
            if status_binary == "failed":
                K_range = np.linspace(0, 10, 100)
                Kc_linear, status_linear = find_critical_coupling_linear_sweep(
                    adj_matrix, omega, t_eval, K_range, seed=seed
                )
                status = status_linear
                Kc = Kc_linear
            else:
                status = status_binary
                Kc = Kc_binary
                Kc_linear = float('nan') # Not computed

            # Extract metadata from filename if possible
            # Expected format: topology_{topology_id}_p{p:.2f}_seed_{seed}.gpickle
            filename = os.path.basename(path)
            parts = filename.replace(".gpickle", "").split("_")
            topology_id = parts[1] if len(parts) > 1 else "unknown"
            p_val = float(parts[3]) if len(parts) > 3 and parts[2] == "p" else 0.0

            results.append({
                "topology_id": topology_id,
                "p": p_val,
                "kc_binary": Kc_binary,
                "kc_linear": Kc_linear if 'Kc_linear' in locals() else float('nan'),
                "status": status
            })

        except Exception as e:
            logger.log("simulation_error", file=path, error=str(e))
            # Extract metadata even on error
            filename = os.path.basename(path)
            parts = filename.replace(".gpickle", "").split("_")
            topology_id = parts[1] if len(parts) > 1 else "unknown"
            p_val = float(parts[3]) if len(parts) > 3 and parts[2] == "p" else 0.0
            results.append({
                "topology_id": topology_id,
                "p": p_val,
                "kc_binary": float('nan'),
                "kc_linear": float('nan'),
                "status": f"error: {str(e)}"
            })

    # Write results to CSV
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", newline="") as f:
        if results:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
        else:
            f.write("topology_id,p,kc_binary,kc_linear,status\n")


def main():
    """Main entry point for simulation batch."""
    config_path = "data/processed/config.json"
    output_path = "data/processed/simulation_results.csv"

    # Load config
    config = load_config(config_path)

    # Find all topology files
    topology_files = sorted(glob.glob("data/processed/topology_*.gpickle"))

    if not topology_files:
        logger.log("no_topologies_found")
        # Create empty output file
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w") as f:
            f.write("topology_id,p,kc_binary,kc_linear,status\n")
        return

    logger.log("starting_batch_simulation", num_topologies=len(topology_files))
    run_simulation_batch(topology_files, config, output_path)
    logger.log("batch_simulation_complete", output=output_path)


if __name__ == "__main__":
    import csv
    import glob
    main()