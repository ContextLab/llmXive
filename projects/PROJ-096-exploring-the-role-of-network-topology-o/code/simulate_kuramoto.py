import os
import json
import logging
from pathlib import Path
from typing import Tuple, Optional, Dict, Any, List
import numpy as np
from scipy import integrate
from scipy import stats

# Import from project utils to ensure consistency
from utils.logging_utils import init_logging, get_logger, log_simulation_params
from utils.graph_utils import is_connected
from utils.config import get_seed, get_t_eval

# --- Configuration Loading ---

def load_config(config_path: str = "data/processed/config.json") -> Dict[str, Any]:
    """
    Load the experiment configuration from the generated config file.
    Raises FileNotFoundError or ValueError if the file is missing or invalid.
    """
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found at {config_path}")
    
    with open(path, 'r') as f:
        config = json.load(f)
    
    # Validate critical keys
    if 'time_steps' not in config:
        raise ValueError("Config missing 'time_steps'")
    if 'n_topologies' not in config:
        raise ValueError("Config missing 'n_topologies'")
    
    # Check for fatal convergence failure from feasibility study
    if config.get('error') == 'CONVERGENCE_FAILURE':
        raise RuntimeError("CONVERGENCE_FAILURE: Feasibility study failed to determine valid parameters.")
    
    return config

# --- Kuramoto Dynamics ---

def kuramoto_derivative(t: float, theta: np.ndarray, adj_matrix: np.ndarray, K: float) -> np.ndarray:
    """
    Computes the derivative of the phase angles for the Kuramoto model.
    
    d(theta_i)/dt = omega_i + (K/N) * sum_j(A_ij * sin(theta_j - theta_i))
    
    Assumes natural frequencies omega_i = 0 for simplicity (or can be extended).
    Here we assume identical oscillators (omega_i = 0) to focus on topology effects.
    
    Args:
        t: Time (unused for autonomous system but required by ODE solver)
        theta: Current phase angles (array of shape N)
        adj_matrix: Adjacency matrix of the network (NxN)
        K: Global coupling strength
        
    Returns:
        d_theta: Time derivative of phases (array of shape N)
    """
    N = len(theta)
    # Calculate phase differences
    # sin(theta_j - theta_i)
    # Vectorized: sin(theta) - cos(theta) * cot? No, use broadcasting
    # sin(theta_j - theta_i) = sin(theta_j)cos(theta_i) - cos(theta_j)sin(theta_i)
    # But simpler: just compute the sum directly
      
    sin_theta = np.sin(theta)
    cos_theta = np.cos(theta)
    
    # sum_j A_ij sin(theta_j - theta_i)
    # = sum_j A_ij (sin_j cos_i - cos_j sin_i)
    # = cos_i * sum_j (A_ij sin_j) - sin_i * sum_j (A_ij cos_j)
    
    weighted_sin = adj_matrix @ sin_theta  # sum_j A_ij sin_j
    weighted_cos = adj_matrix @ cos_theta  # sum_j A_ij cos_j
    
    coupling_term = (K / N) * (cos_theta * weighted_sin - sin_theta * weighted_cos)
    
    # Natural frequencies (assuming 0 for identical oscillators)
    omega = np.zeros_like(theta)
    
    return omega + coupling_term

def calculate_order_parameter(theta: np.ndarray) -> float:
    """
    Calculates the Kuramoto order parameter R.
    R = | (1/N) * sum_j exp(i * theta_j) |
    
    Args:
        theta: Array of phase angles
        
    Returns:
        R: Magnitude of the complex order parameter (float)
    """
    complex_sum = np.sum(np.exp(1j * theta))
    R = np.abs(complex_sum) / len(theta)
    return R

def simulate_kuramoto(
    adj_matrix: np.ndarray,
    K: float,
    time_steps: int,
    dt: float = 0.01,
    seed: Optional[int] = None,
    logger: Optional[logging.Logger] = None
) -> Tuple[float, np.ndarray]:
    """
    Simulates the Kuramoto model on a given network for a specified number of steps.
    
    Args:
        adj_matrix: Adjacency matrix of the network
        K: Coupling strength
        time_steps: Number of time steps to simulate
        dt: Time step size
        seed: Random seed for initial phases
        logger: Logger instance
        
    Returns:
        R_avg: Average order parameter over the time series (after transient)
        R_series: Full time series of R values
    """
    N = adj_matrix.shape[0]
    
    # Initialize phases
    rng = np.random.default_rng(seed)
    theta = rng.uniform(0, 2 * np.pi, N)
    
    # Integration parameters
    t_span = (0, time_steps * dt)
    t_eval = np.linspace(t_span[0], t_span[1], time_steps)
    
    # Solve ODE
    sol = integrate.solve_ivp(
        fun=lambda t, y: kuramoto_derivative(t, y, adj_matrix, K),
        t_span=t_span,
        y0=theta,
        t_eval=t_eval,
        method='RK45',
        rtol=1e-5,
        atol=1e-7
    )
    
    if not sol.success:
        if logger:
            logger.error(f"ODE integration failed: {sol.message}")
        raise RuntimeError(f"Simulation failed: {sol.message}")
    
    # Calculate order parameter time series
    R_series = np.array([calculate_order_parameter(sol.y[:, i]) for i in range(time_steps)])
    
    # Discard transient (first 20% of steps)
    transient_steps = int(time_steps * 0.2)
    R_avg = np.mean(R_series[transient_steps:])
    
    return R_avg, R_series

# --- Critical Coupling Detection ---

def find_critical_coupling_binary_search(
    adj_matrix: np.ndarray,
    time_steps: int,
    threshold: float = 0.5,
    tol: float = 0.01,
    max_iter: int = 20,
    seed: Optional[int] = None,
    logger: Optional[logging.Logger] = None
) -> Optional[float]:
    """
    Finds the critical coupling strength K_c using binary search.
    
    K_c is defined as the smallest K where the average order parameter R >= threshold.
    
    Args:
        adj_matrix: Adjacency matrix
        time_steps: Simulation duration
        threshold: Target order parameter threshold (default 0.5)
        tol: Convergence tolerance for K
        max_iter: Maximum iterations for binary search
        seed: Random seed
        logger: Logger instance
        
    Returns:
        K_c: Critical coupling strength, or None if binary search fails to converge
    """
    K_low = 0.0
    K_high = 10.0 # Upper bound guess
    K_c = None
    
    if logger:
        logger.info(f"Starting binary search for K_c with threshold={threshold}, tol={tol}")
    
    for i in range(max_iter):
        K_mid = (K_low + K_high) / 2
        
        try:
            R_avg, _ = simulate_kuramoto(adj_matrix, K_mid, time_steps, seed=seed, logger=logger)
        except Exception as e:
            if logger:
                logger.warning(f"Simulation failed at K={K_mid}: {e}. Skipping.")
            K_low = K_mid
            continue
        
        if logger:
            logger.debug(f"Iter {i}: K={K_mid:.4f}, R_avg={R_avg:.4f}")
        
        if R_avg >= threshold:
            K_c = K_mid
            K_high = K_mid
        else:
            K_low = K_mid
        
        if (K_high - K_low) < tol:
            if logger:
                logger.info(f"Binary search converged at K_c={K_c:.4f} after {i+1} iterations.")
            return K_c
    
    if logger:
        logger.warning(f"Binary search did not converge within {max_iter} iterations. Last estimate: {K_c}")
    
    return K_c

def find_critical_coupling_linear_sweep(
    adj_matrix: np.ndarray,
    time_steps: int,
    threshold: float = 0.5,
    K_start: float = 0.0,
    K_end: float = 10.0,
    step_size: float = 0.1,
    seed: Optional[int] = None,
    logger: Optional[logging.Logger] = None
) -> Optional[float]:
    """
    Fallback method: Finds K_c using a linear sweep if binary search fails.
    
    Scans K from K_start to K_end with step_size. Returns the first K where R >= threshold.
    
    Args:
        adj_matrix: Adjacency matrix
        time_steps: Simulation duration
        threshold: Target order parameter threshold
        K_start: Start of sweep range
        K_end: End of sweep range
        step_size: Step size for sweep
        seed: Random seed
        logger: Logger instance
        
    Returns:
        K_c: Critical coupling strength, or None if no K satisfies the condition
    """
    if logger:
        logger.info(f"Starting linear sweep for K_c from {K_start} to {K_end} with step {step_size}")
    
    K_values = np.arange(K_start, K_end + step_size, step_size)
    
    for K in K_values:
        try:
            R_avg, _ = simulate_kuramoto(adj_matrix, K, time_steps, seed=seed, logger=logger)
        except Exception as e:
            if logger:
                logger.warning(f"Simulation failed at K={K}: {e}. Skipping.")
            continue
        
        if logger:
            logger.debug(f"Linear Sweep: K={K:.4f}, R_avg={R_avg:.4f}")
        
        if R_avg >= threshold:
            if logger:
                logger.info(f"Linear sweep found K_c={K:.4f} (R={R_avg:.4f} >= {threshold})")
            return K
    
    if logger:
        logger.warning("Linear sweep did not find any K satisfying the threshold condition.")
    
    return None

# --- Batch Execution ---

def run_simulation_batch(
    graph_files: List[str],
    config: Dict[str, Any],
    output_path: str,
    logger: Optional[logging.Logger] = None
) -> List[Dict[str, Any]]:
    """
    Runs simulation on a batch of graph files and saves results.
    
    Args:
        graph_files: List of paths to .gpickle files
        config: Experiment configuration
        output_path: Path to save results CSV
        logger: Logger instance
        
    Returns:
        results: List of result dictionaries
    """
    time_steps = config['time_steps']
    threshold = config.get('threshold', 0.5)
    run_count = config.get('run_count', 1) # Default 1 if not specified
    
    if logger:
        logger.info(f"Running batch simulation for {len(graph_files)} graphs with {time_steps} steps.")
    
    results = []
    
    for i, file_path in enumerate(graph_files):
        graph_name = Path(file_path).stem
        
        if logger:
            logger.info(f"Processing {i+1}/{len(graph_files)}: {graph_name}")
        
        # Load graph
        try:
            import networkx as nx
            G = nx.read_gpickle(file_path)
            adj_matrix = nx.to_numpy_array(G)
        except Exception as e:
            if logger:
                logger.error(f"Failed to load graph {file_path}: {e}")
            continue
        
        # Check connectivity
        if not is_connected(G):
            if logger:
                logger.warning(f"Graph {graph_name} is not connected. Skipping.")
            continue
        
        # Run binary search
        K_c_binary = find_critical_coupling_binary_search(
            adj_matrix, 
            time_steps, 
            threshold=threshold,
            seed=get_seed(),
            logger=logger
        )
        
        # Fallback to linear sweep if binary search fails
        if K_c_binary is None:
            if logger:
                logger.warning(f"Binary search failed for {graph_name}. Attempting linear sweep.")
            K_c_binary = find_critical_coupling_linear_sweep(
                adj_matrix,
                time_steps,
                threshold=threshold,
                seed=get_seed(),
                logger=logger
            )
        
        if K_c_binary is None:
            if logger:
                logger.error(f"Failed to determine K_c for {graph_name} after fallback.")
            continue
        
        results.append({
            "topology_id": graph_name,
            "K_c": K_c_binary,
            "method": "binary_search_fallback" if K_c_binary is not None else "linear_sweep"
        })
    
    # Save results to CSV
    if results:
        import csv
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["topology_id", "K_c", "method"])
            writer.writeheader()
            writer.writerows(results)
        
        if logger:
            logger.info(f"Saved {len(results)} results to {output_path}")
    else:
        if logger:
            logger.warning("No results were generated.")
    
    return results

def main():
    """
    Main entry point for the simulation script.
    """
    # Initialize logging
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    logger = init_logging(module_name="simulate_kuramoto", log_dir=log_dir)
    
    logger.info("Starting Kuramoto Simulation Batch")
    
    try:
        # Load configuration
        config = load_config()
        logger.info(f"Configuration loaded: time_steps={config['time_steps']}, n_topologies={config['n_topologies']}")
        
        # Find graph files
        data_dir = Path("data/processed")
        graph_files = sorted(data_dir.glob("graph_p*.gpickle"))
        
        if not graph_files:
            logger.error("No graph files found in data/processed/.")
            return
        
        logger.info(f"Found {len(graph_files)} graph files.")
        
        # Run batch
        output_file = data_dir / "simulation_results.csv"
        results = run_simulation_batch(
            graph_files=[str(f) for f in graph_files],
            config=config,
            output_path=str(output_file),
            logger=logger
        )
        
        logger.info(f"Simulation batch completed. {len(results)} successful runs.")
        
    except FileNotFoundError as e:
        logger.error(f"Configuration error: {e}")
    except RuntimeError as e:
        logger.error(f"Runtime error: {e}")
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()