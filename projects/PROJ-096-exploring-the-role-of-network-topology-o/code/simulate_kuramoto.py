"""
Kuramoto Oscillator Simulation Module

Implements the Kuramoto model dynamics for coupled oscillators on arbitrary
network topologies. Provides the ODE derivative function, order parameter
calculation, and critical coupling detection.

Dependencies:
- networkx: for graph operations
- scipy: for ODE integration
- numpy: for numerical operations
- utils.logging_utils: for logging simulation parameters
"""

import os
import json
import logging
from pathlib import Path
from typing import Tuple, Optional, Dict, Any, List

import numpy as np
import networkx as nx
from scipy import integrate
from scipy import stats

from utils.logging_utils import init_logging, get_logger, log_simulation_params
from utils.config import get_seed, apply_global_seed

# Initialize logging
logger = get_logger(__name__)


def load_config() -> Dict[str, Any]:
    """
    Load configuration from data/processed/config.json.

    Returns:
        Dict containing configuration parameters including time_steps.

    Raises:
        RuntimeError: If config.json has time_steps=0 (CONVERGENCE_FAILURE).
        FileNotFoundError: If config.json does not exist.
    """
    config_path = Path("data/processed/config.json")
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, 'r') as f:
        config = json.load(f)

    time_steps = config.get('time_steps', 0)
    if time_steps == 0:
        raise RuntimeError("CONVERGENCE_FAILURE: time_steps is 0 in config.json")

    return config


def kuramoto_derivative(t: float, theta: np.ndarray, K: float, adj_matrix: np.ndarray) -> np.ndarray:
    """
    Compute the derivative of the Kuramoto oscillator phases.

    The Kuramoto model is defined as:
        dθ_i/dt = ω_i + (K/N) * Σ_j A_ij * sin(θ_j - θ_i)

    Where:
        - θ_i: phase of oscillator i
        - ω_i: natural frequency of oscillator i (assumed 0 for simplicity here,
               or can be drawn from a distribution)
        - K: coupling strength
        - A_ij: adjacency matrix element (1 if connected, 0 otherwise)
        - N: number of oscillators

    For this implementation, we assume all natural frequencies ω_i = 0
    (identical oscillators), which simplifies the dynamics to:
        dθ_i/dt = (K/N) * Σ_j A_ij * sin(θ_j - θ_i)

    Args:
        t: Current time (unused for autonomous system, but required by scipy.integrate)
        theta: Array of current phases (shape: N,)
        K: Coupling strength
        adj_matrix: Adjacency matrix of the network (shape: N x N)

    Returns:
        Array of phase derivatives (shape: N,)
    """
    N = len(theta)
    adj_matrix = np.array(adj_matrix)

    # Compute phase differences: sin(θ_j - θ_i) for all pairs
    # theta[:, None] - theta[None, :] gives N x N matrix of (θ_i - θ_j)
    phase_diff = theta[:, np.newaxis] - theta[np.newaxis, :]
    sin_diff = np.sin(phase_diff)

    # Compute coupling term: (K/N) * Σ_j A_ij * sin(θ_j - θ_i)
    # Note: sin(θ_j - θ_i) = -sin(θ_i - θ_j), so we use -sin_diff
    coupling_term = (K / N) * np.dot(adj_matrix, -sin_diff)

    return coupling_term


def calculate_order_parameter(theta: np.ndarray) -> Tuple[float, complex]:
    """
    Calculate the Kuramoto order parameter R and the complex order parameter Z.

    The order parameter R measures the degree of phase synchronization:
        Z = (1/N) * Σ_j exp(i * θ_j)
        R = |Z|
        ψ = arg(Z)

    R ranges from 0 (incoherent) to 1 (fully synchronized).

    Args:
        theta: Array of phases (shape: N,)

    Returns:
        Tuple of (R, Z) where:
            - R: Magnitude of the order parameter (float, 0 <= R <= 1)
            - Z: Complex order parameter (complex)
    """
    N = len(theta)
    Z = np.mean(np.exp(1j * theta))
    R = np.abs(Z)
    return R, Z


def simulate_kuramoto(
    adj_matrix: np.ndarray,
    K: float,
    time_steps: int,
    t_eval: Optional[np.ndarray] = None,
    theta0: Optional[np.ndarray] = None,
    seed: Optional[int] = None
) -> Tuple[np.ndarray, np.ndarray, List[float]]:
    """
    Simulate Kuramoto dynamics on a given network.

    Args:
        adj_matrix: Adjacency matrix of the network (N x N)
        K: Coupling strength
        time_steps: Number of time steps to simulate
        t_eval: Time points at which to store the solution (optional)
        theta0: Initial phases (optional, random if not provided)
        seed: Random seed for initial conditions (optional)

    Returns:
        Tuple of (t, theta_history, R_history) where:
            - t: Time array
            - theta_history: Array of phases over time (len(t) x N)
            - R_history: Array of order parameter values over time
    """
    N = adj_matrix.shape[0]

    # Set seed if provided
    if seed is not None:
        np.random.seed(seed)

    # Initialize phases if not provided
    if theta0 is None:
        theta0 = np.random.uniform(0, 2 * np.pi, N)

    # Create time array
    if t_eval is None:
        t_eval = np.linspace(0, time_steps, time_steps)

    # Integrate ODE
    solution = integrate.solve_ivp(
        fun=lambda t, theta: kuramoto_derivative(t, theta, K, adj_matrix),
        t_span=(t_eval[0], t_eval[-1]),
        y0=theta0,
        t_eval=t_eval,
        method='RK45',
        rtol=1e-6,
        atol=1e-9
    )

    if not solution.success:
        raise RuntimeError(f"ODE integration failed: {solution.message}")

    theta_history = solution.y.T  # Shape: (len(t_eval), N)

    # Calculate order parameter at each time step
    R_history = []
    for theta_t in theta_history:
        R, _ = calculate_order_parameter(theta_t)
        R_history.append(R)

    return t_eval, theta_history, np.array(R_history)


def find_critical_coupling_binary_search(
    adj_matrix: np.ndarray,
    time_steps: int,
    threshold: float = 0.5,
    K_min: float = 0.0,
    K_max: float = 10.0,
    tol: float = 0.01,
    max_iterations: int = 20,
    seed: Optional[int] = None,
    logger: Optional[logging.Logger] = None
) -> Optional[float]:
    """
    Find the critical coupling strength K_c using binary search.

    The critical coupling is the minimum K such that the time-averaged
    order parameter R exceeds the given threshold.

    Args:
        adj_matrix: Adjacency matrix of the network
        time_steps: Number of time steps for simulation
        threshold: Order parameter threshold for synchronization (default 0.5)
        K_min: Lower bound for binary search
        K_max: Upper bound for binary search
        tol: Tolerance for binary search convergence
        max_iterations: Maximum number of binary search iterations
        seed: Random seed for initial conditions
        logger: Logger instance

    Returns:
        The critical coupling K_c, or None if binary search fails to converge
    """
    if logger is None:
        logger = get_logger(__name__)

    # Create time array
    t_eval = np.linspace(0, time_steps, time_steps)

    K_low, K_high = K_min, K_max
    K_c = None

    for iteration in range(max_iterations):
        K_mid = (K_low + K_high) / 2.0

        # Simulate with K_mid
        try:
            t, theta_hist, R_hist = simulate_kuramoto(
                adj_matrix, K_mid, time_steps, t_eval, seed=seed
            )

            # Calculate time-averaged order parameter (after transient)
            # Skip first 20% as transient
            transient_cutoff = int(0.2 * len(R_hist))
            R_avg = np.mean(R_hist[transient_cutoff:])

            logger.debug(f"Iteration {iteration}: K={K_mid:.4f}, R_avg={R_avg:.4f}")

            if R_avg >= threshold:
                K_high = K_mid
                K_c = K_mid
            else:
                K_low = K_mid

            # Check convergence
            if (K_high - K_low) < tol:
                logger.info(f"Binary search converged at iteration {iteration}")
                break

        except Exception as e:
            logger.error(f"Simulation failed for K={K_mid}: {e}")
            K_low = K_mid  # Treat failure as insufficient coupling

    if K_c is None:
        logger.warning("Binary search did not converge within max iterations")

    return K_c


def find_critical_coupling_linear_sweep(
    adj_matrix: np.ndarray,
    time_steps: int,
    threshold: float = 0.5,
    K_values: Optional[np.ndarray] = None,
    seed: Optional[int] = None,
    logger: Optional[logging.Logger] = None
) -> Optional[float]:
    """
    Fallback method: Find K_c using linear sweep over K values.

    Args:
        adj_matrix: Adjacency matrix of the network
        time_steps: Number of time steps for simulation
        threshold: Order parameter threshold
        K_values: Array of K values to test (default: linspace 0 to 10, 50 points)
        seed: Random seed
        logger: Logger instance

    Returns:
        The first K value where R_avg >= threshold, or None if not found
    """
    if logger is None:
        logger = get_logger(__name__)

    if K_values is None:
        K_values = np.linspace(0, 10, 50)

    t_eval = np.linspace(0, time_steps, time_steps)

    for K in K_values:
        try:
            t, theta_hist, R_hist = simulate_kuramoto(
                adj_matrix, K, time_steps, t_eval, seed=seed
            )

            transient_cutoff = int(0.2 * len(R_hist))
            R_avg = np.mean(R_hist[transient_cutoff:])

            logger.debug(f"K={K:.4f}, R_avg={R_avg:.4f}")

            if R_avg >= threshold:
                logger.info(f"Linear sweep found K_c = {K:.4f}")
                return K

        except Exception as e:
            logger.error(f"Simulation failed for K={K}: {e}")
            continue

    logger.warning("Linear sweep did not find K_c within tested range")
    return None


def run_simulation_batch(
    graph_paths: List[str],
    time_steps: int,
    output_csv: str = "data/processed/simulation_results.csv",
    threshold: float = 0.5,
    seed: Optional[int] = None
) -> None:
    """
    Run simulation batch for multiple graphs and save results to CSV.

    Args:
        graph_paths: List of paths to .gpickle graph files
        time_steps: Number of time steps for simulation
        output_csv: Path to output CSV file
        threshold: Order parameter threshold for K_c detection
        seed: Random seed
    """
    import csv
    from utils.logging_utils import init_logging

    init_logging()
    logger = get_logger(__name__)

    # Load config to get additional parameters
    try:
        config = load_config()
        K_min = config.get('K_min', 0.0)
        K_max = config.get('K_max', 10.0)
        K_tol = config.get('K_tol', 0.01)
        K_max_iter = config.get('K_max_iter', 20)
    except (FileNotFoundError, RuntimeError) as e:
        logger.error(f"Failed to load config: {e}")
        raise

    results = []

    for i, graph_path in enumerate(graph_paths):
        logger.info(f"Processing graph {i+1}/{len(graph_paths)}: {graph_path}")

        try:
            # Load graph
            G = nx.read_gpickle(graph_path)
            adj_matrix = nx.to_numpy_array(G)
            N = G.number_of_nodes()

            # Determine seed for this run
            run_seed = seed if seed is not None else (i * 42)

            # Find K_c using binary search
            K_c = find_critical_coupling_binary_search(
                adj_matrix, time_steps, threshold,
                K_min, K_max, K_tol, K_max_iter,
                seed=run_seed, logger=logger
            )

            # Fallback to linear sweep if binary search fails
            if K_c is None:
                logger.warning(f"Binary search failed for {graph_path}, trying linear sweep")
                K_c = find_critical_coupling_linear_sweep(
                    adj_matrix, time_steps, threshold,
                    seed=run_seed, logger=logger
                )

            results.append({
                'graph_path': graph_path,
                'node_count': N,
                'K_c': K_c,
                'threshold': threshold,
                'seed': run_seed,
                'status': 'success' if K_c is not None else 'failed'
            })

            logger.info(f"Graph {i+1}: K_c = {K_c}")

        except Exception as e:
            logger.error(f"Failed to process {graph_path}: {e}")
            results.append({
                'graph_path': graph_path,
                'node_count': 0,
                'K_c': None,
                'threshold': threshold,
                'seed': seed,
                'status': 'error',
                'error': str(e)
            })

    # Write results to CSV
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    with open(output_csv, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

    logger.info(f"Results written to {output_csv}")


def main():
    """Main entry point for Kuramoto simulation."""
    init_logging()
    logger = get_logger(__name__)

    try:
        config = load_config()
        time_steps = config['time_steps']
        logger.info(f"Loaded configuration: time_steps={time_steps}")

        # Example: Run a single simulation on a test graph
        # In practice, this would be called by run_simulation_batch
        logger.info("Kuramoto simulation module loaded successfully")

    except FileNotFoundError as e:
        logger.error(f"Configuration error: {e}")
        raise
    except RuntimeError as e:
        logger.error(f"Runtime error: {e}")
        raise


if __name__ == "__main__":
    main()