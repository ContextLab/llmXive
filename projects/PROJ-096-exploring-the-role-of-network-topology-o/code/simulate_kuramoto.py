"""
Kuramoto Oscillator Simulation Module.

This module implements the Kuramoto model dynamics, including the ODE derivative,
order parameter calculation, and binary search for the critical coupling strength (Kc).
It provides batch simulation capabilities for multiple network topologies.
"""

import os
import json
import logging
from pathlib import Path
from typing import Tuple, Optional, Dict, Any, List
import numpy as np
import networkx as nx
from scipy.integrate import solve_ivp

# Import local utilities
from utils.logging_utils import init_logging, get_logger
from utils.graph_utils import is_connected

# Constants
DEFAULT_TIME_STEPS = 1000
DEFAULT_T_START = 0.0
DEFAULT_T_END = 100.0
ORDER_PARAM_THRESHOLD = 0.5
BINARY_SEARCH_TOL = 0.05
BINARY_SEARCH_MAX_ITER = 10
LINEAR_SWEEP_MIN_K = 0.0
LINEAR_SWEEP_MAX_K = 5.0
LINEAR_SWEEP_STEPS = 50

logger = get_logger(__name__)

def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from JSON file."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Validate required keys
    if 'time_steps' not in config:
        raise ValueError("Config must contain 'time_steps'")
    
    return config

def kuramoto_derivative(t: float, theta: np.ndarray, K: float, adj_matrix: np.ndarray, omega: np.ndarray) -> np.ndarray:
    """
    Compute the derivative of the Kuramoto model.
    
    d(theta_i)/dt = omega_i + (K/N) * sum_j(adj_ij * sin(theta_j - theta_i))
    
    Args:
        t: Current time (unused, but required by solve_ivp)
        theta: Current phase angles
        K: Coupling strength
        adj_matrix: Adjacency matrix of the network
        omega: Natural frequencies of oscillators
    
    Returns:
        Derivative of phase angles
    """
    N = len(theta)
    # Calculate phase differences
    diff = theta[:, np.newaxis] - theta[np.newaxis, :]
    # Calculate coupling term
    coupling = (K / N) * np.dot(adj_matrix, np.sin(diff))
    # Total derivative
    return omega + np.sum(coupling, axis=1)

def calculate_order_parameter(theta: np.ndarray) -> float:
    """
    Calculate the Kuramoto order parameter R.
    
    R = | (1/N) * sum_j(exp(i * theta_j)) |
    
    Args:
        theta: Array of phase angles
    
    Returns:
        Order parameter R (0 <= R <= 1)
    """
    N = len(theta)
    complex_order = np.sum(np.exp(1j * theta)) / N
    return np.abs(complex_order)

def simulate_kuramoto(
    adj_matrix: np.ndarray,
    omega: np.ndarray,
    K: float,
    time_steps: int,
    t_eval: Optional[np.ndarray] = None,
    seed: Optional[int] = None
) -> Tuple[np.ndarray, float]:
    """
    Simulate Kuramoto dynamics for a given coupling strength.
    
    Args:
        adj_matrix: Adjacency matrix of the network
        omega: Natural frequencies
        K: Coupling strength
        time_steps: Number of time steps
        t_eval: Time points for evaluation (optional)
        seed: Random seed for reproducibility (optional)
    
    Returns:
        Tuple of (final_order_parameter, mean_order_parameter_over_time)
    """
    N = len(omega)
    if seed is not None:
        np.random.seed(seed)
    
    # Initialize phases randomly
    theta0 = np.random.uniform(0, 2 * np.pi, N)
    
    # Create time array if not provided
    if t_eval is None:
        t_eval = np.linspace(0, 100, time_steps)
    
    # Solve ODE
    try:
        sol = solve_ivp(
            lambda t, y: kuramoto_derivative(t, y, K, adj_matrix, omega),
            [t_eval[0], t_eval[-1]],
            theta0,
            t_eval=t_eval,
            method='RK45',
            rtol=1e-6,
            atol=1e-9
        )
        
        if not sol.success:
            logger.warning(f"ODE integration failed: {sol.message}")
            # Return fallback values
            return 0.0, 0.0
        
        # Calculate order parameter at each time step
        order_params = []
        for i in range(len(t_eval)):
            order_params.append(calculate_order_parameter(sol.y[:, i]))
        
        final_order = order_params[-1]
        mean_order = np.mean(order_params[-len(order_params)//4:])  # Average last quarter
        
        return final_order, mean_order
        
    except Exception as e:
        logger.error(f"Simulation error: {str(e)}")
        return 0.0, 0.0

def find_critical_coupling_binary_search(
    adj_matrix: np.ndarray,
    omega: np.ndarray,
    time_steps: int,
    threshold: float = ORDER_PARAM_THRESHOLD,
    tol: float = BINARY_SEARCH_TOL,
    max_iter: int = BINARY_SEARCH_MAX_ITER,
    seed: Optional[int] = None
) -> Tuple[Optional[float], str]:
    """
    Find the critical coupling strength Kc using binary search.
    
    Args:
        adj_matrix: Adjacency matrix
        omega: Natural frequencies
        time_steps: Number of time steps
        threshold: Order parameter threshold for synchronization
        tol: Tolerance for binary search
        max_iter: Maximum iterations
        seed: Random seed
    
    Returns:
        Tuple of (Kc, status) where status is 'found', 'not_found', or 'failed'
    """
    K_low = LINEAR_SWEEP_MIN_K
    K_high = LINEAR_SWEEP_MAX_K
    
    for iteration in range(max_iter):
        K_mid = (K_low + K_high) / 2
        
        final_R, mean_R = simulate_kuramoto(
            adj_matrix, omega, K_mid, time_steps, seed=seed
        )
        
        if final_R >= threshold:
            K_high = K_mid
        else:
            K_low = K_mid
        
        if (K_high - K_low) < tol:
            return K_mid, 'found'
    
    # Return best estimate if max iterations reached
    K_est = (K_low + K_high) / 2
    final_R, _ = simulate_kuramoto(adj_matrix, omega, K_est, time_steps, seed=seed)
    
    if final_R >= threshold:
        return K_est, 'found'
    else:
        return None, 'not_found'

def find_critical_coupling_linear_sweep(
    adj_matrix: np.ndarray,
    omega: np.ndarray,
    time_steps: int,
    threshold: float = ORDER_PARAM_THRESHOLD,
    seed: Optional[int] = None
) -> Tuple[Optional[float], str]:
    """
    Fallback: Find Kc using linear sweep.
    
    Args:
        adj_matrix: Adjacency matrix
        omega: Natural frequencies
        time_steps: Number of time steps
        threshold: Order parameter threshold
        seed: Random seed
    
    Returns:
        Tuple of (Kc, status)
    """
    K_values = np.linspace(LINEAR_SWEEP_MIN_K, LINEAR_SWEEP_MAX_K, LINEAR_SWEEP_STEPS)
    
    for K in K_values:
        final_R, _ = simulate_kuramoto(adj_matrix, omega, K, time_steps, seed=seed)
        if final_R >= threshold:
            return K, 'found'
    
    return None, 'not_found'

def run_simulation_batch(config_path: str, output_path: str) -> None:
    """
    Run simulation batch for all valid topologies.
    
    Args:
        config_path: Path to configuration file
        output_path: Path to output CSV file
    """
    # Load configuration
    try:
        config = load_config(config_path)
        time_steps = config['time_steps']
        n_topologies = config.get('n_topologies', 50)
        sc_003_violation = config.get('SC_003_VIOLATION', False)
        
        if sc_003_violation:
            logger.info(f"Running with reduced scope due to SC-003 violation")
            logger.info(f"Time steps: {time_steps}, Topologies: {n_topologies}")
        
    except FileNotFoundError as e:
        logger.error(f"Config file missing: {e}")
        raise RuntimeError("CONFIG_MISSING")
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        raise RuntimeError(f"CONFIG_ERROR: {str(e)}")
    
    # Find topology files
    topology_dir = Path('data/processed')
    topology_files = sorted(topology_dir.glob('topology_*.gpickle'))
    
    if not topology_files:
        logger.error("No topology files found in data/processed/")
        raise RuntimeError("NO_TOPOLOGIES_FOUND")
    
    logger.info(f"Found {len(topology_files)} topology files")
    
    # Prepare output data
    results = []
    
    for topology_file in topology_files:
        # Extract topology ID and p value from filename
        filename = topology_file.name
        parts = filename.replace('.gpickle', '').split('_')
        topology_id = parts[1]  # topology_{id}
        p_value = float(parts[3].replace('p', ''))  # p{p:.2f}
        seed = int(parts[5].replace('seed_', ''))  # seed_{seed}
        
        logger.info(f"Processing topology {topology_id} (p={p_value}, seed={seed})")
        
        try:
            # Load graph
            G = nx.read_gpickle(topology_file)
            
            if not is_connected(G):
                logger.warning(f"Graph {topology_id} is not connected, skipping")
                continue
            
            # Convert to adjacency matrix
            adj_matrix = nx.to_numpy_array(G)
            N = len(adj_matrix)
            
            # Generate natural frequencies (uniform distribution)
            np.random.seed(seed)
            omega = np.random.uniform(-0.5, 0.5, N)
            
            # Run binary search for Kc
            kc_binary, status_binary = find_critical_coupling_binary_search(
                adj_matrix, omega, time_steps, seed=seed
            )
            
            # If binary search fails, use linear sweep
            if status_binary == 'not_found' or kc_binary is None:
                logger.info(f"Binary search failed for {topology_id}, using linear sweep")
                kc_linear, status_linear = find_critical_coupling_linear_sweep(
                    adj_matrix, omega, time_steps, seed=seed
                )
                kc_result = kc_linear
                status_result = f"linear_{status_linear}"
            else:
                kc_result = kc_binary
                status_result = status_binary
            
            results.append({
                'topology_id': topology_id,
                'p': p_value,
                'kc_binary': kc_result if kc_result is not None else '',
                'kc_linear': '',  # Only filled if binary failed
                'status': status_result
            })
            
        except Exception as e:
            logger.error(f"Error processing {topology_file}: {str(e)}")
            results.append({
                'topology_id': topology_id,
                'p': p_value,
                'kc_binary': '',
                'kc_linear': '',
                'status': f'error: {str(e)}'
            })
    
    # Write results to CSV
    import csv
    with open(output_path, 'w', newline='') as csvfile:
        fieldnames = ['topology_id', 'p', 'kc_binary', 'kc_linear', 'status']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    logger.info(f"Simulation results written to {output_path}")
    logger.info(f"Processed {len(results)} topologies")

def main():
    """Main entry point for the simulation batch."""
    init_logging()
    
    config_path = 'data/processed/config.json'
    output_path = 'data/processed/simulation_results.csv'
    
    try:
        run_simulation_batch(config_path, output_path)
        logger.info("Simulation batch completed successfully")
    except Exception as e:
        logger.error(f"Simulation batch failed: {str(e)}")
        raise

if __name__ == '__main__':
    main()