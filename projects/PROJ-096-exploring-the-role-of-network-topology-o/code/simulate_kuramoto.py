import os
import json
import logging
from pathlib import Path
from typing import Tuple, Optional, Dict, Any, List
import numpy as np
from scipy.integrate import solve_ivp

from utils.logging_utils import init_logging, get_logger
from utils.stats_utils import spearman_correlation

# Initialize logging for this module
logger = init_logging(__name__)

def load_config(config_path: str = "data/processed/config.json") -> Dict[str, Any]:
    """
    Load the feasibility study configuration.
    Raises RuntimeError if the configuration indicates a convergence failure.
    """
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(path, 'r') as f:
        config = json.load(f)

    # Check for critical errors that prevent simulation
    if config.get('error') is not None:
        raise RuntimeError(f"CONVERGENCE_FAILURE: {config['error']}")

    if config.get('time_steps', 0) == 0:
        raise RuntimeError("CONVERGENCE_FAILURE: time_steps is zero.")

    return config

def kuramoto_derivative(t: float, theta: np.ndarray, K: float, omega: np.ndarray) -> np.ndarray:
    """
    Computes the derivative of the phase angles for the Kuramoto model.

    dθ_i/dt = ω_i + (K/N) * Σ_j sin(θ_j - θ_i)

    Parameters
    ----------
    t : float
        Current time (unused, but required by ODE solver).
    theta : np.ndarray
        Current phase angles (N,).
    K : float
        Global coupling strength.
    omega : np.ndarray
        Natural frequencies of the oscillators (N,).

    Returns
    -------
    np.ndarray
        Time derivatives of the phase angles (N,).
    """
    N = len(theta)
    # Vectorized calculation of the sum of sines
    # sin(θ_j - θ_i) = sin(θ_j)cos(θ_i) - cos(θ_j)sin(θ_i)
    # We need sum over j for each i.
    # sum_j sin(θ_j - θ_i) = sum_j sin(θ_j)cos(θ_i) - sum_j cos(θ_j)sin(θ_i)
    #                       = cos(θ_i) * sum(sin(θ_j)) - sin(θ_i) * sum(cos(θ_j))
    
    sin_theta = np.sin(theta)
    cos_theta = np.cos(theta)
    
    sum_sin = np.sum(sin_theta)
    sum_cos = np.sum(cos_theta)
    
    coupling_term = (K / N) * (cos_theta * sum_sin - sin_theta * sum_cos)
    
    return omega + coupling_term

def calculate_order_parameter(theta: np.ndarray) -> Tuple[float, float]:
    """
    Calculates the complex order parameter R and phase Psi.
    
    R * e^(i*Psi) = (1/N) * Σ_j e^(i*θ_j)
    
    Parameters
    ----------
    theta : np.ndarray
        Phase angles (N,).
        
    Returns
    -------
    R : float
        Magnitude of the order parameter (0 <= R <= 1).
    Psi : float
        Average phase.
    """
    z = np.mean(np.exp(1j * theta))
    R = np.abs(z)
    Psi = np.angle(z)
    return R, Psi

def simulate_kuramoto(
    N: int,
    omega: np.ndarray,
    K: float,
    time_steps: int,
    dt: float = 0.1,
    seed: Optional[int] = None
) -> Tuple[float, float]:
    """
    Simulates the Kuramoto model for a given coupling strength K.
    
    Returns the time-averaged order parameter <R> and the final R.
    """
    if seed is not None:
        np.random.seed(seed)
        
    # Initialize phases randomly
    theta0 = np.random.uniform(0, 2 * np.pi, N)
    
    t_eval = np.linspace(0, time_steps * dt, time_steps)
    
    sol = solve_ivp(
        fun=lambda t, y: kuramoto_derivative(t, y, K, omega),
        t_span=(0, t_eval[-1]),
        y0=theta0,
        t_eval=t_eval,
        method='RK45',
        rtol=1e-4,
        atol=1e-6
    )
    
    if not sol.success:
        raise RuntimeError(f"ODE integration failed: {sol.message}")
        
    thetas = sol.y.T  # Shape: (time_steps, N)
    
    # Calculate R for each time step
    R_values = np.array([calculate_order_parameter(theta)[0] for theta in thetas])
    
    # Discard transient (first 20%)
    transient_cutoff = int(0.2 * len(R_values))
    R_steady = R_values[transient_cutoff:]
    
    if len(R_steady) == 0:
        R_steady = R_values
        
    return np.mean(R_steady), R_values[-1]

def find_critical_coupling_binary_search(
    N: int,
    omega: np.ndarray,
    time_steps: int,
    k_min: float = 0.0,
    k_max: float = 2.0,
    tol: float = 0.05,
    max_iter: int = 20,
    seed: Optional[int] = None
) -> float:
    """
    Finds the critical coupling strength Kc using binary search.
    
    The threshold for synchronization is defined as <R> >= 0.5.
    """
    k_low = k_min
    k_high = k_max
    k_mid = (k_low + k_high) / 2.0
    
    logger.info(f"Starting binary search for Kc in [{k_low}, {k_high}]")
    
    for i in range(max_iter):
        k_mid = (k_low + k_high) / 2.0
        r_mean, _ = simulate_kuramoto(N, omega, k_mid, time_steps, seed=seed)
        
        logger.debug(f"Iter {i}: K={k_mid:.4f}, R_mean={r_mean:.4f}")
        
        if abs(k_high - k_low) < tol:
            logger.info(f"Binary search converged at K={k_mid:.4f} after {i+1} iterations.")
            return k_mid
            
        if r_mean < 0.5:
            k_low = k_mid
        else:
            k_high = k_mid
            
    logger.warning(f"Binary search did not converge within {max_iter} iterations. Returning {k_mid}.")
    return k_mid

def find_critical_coupling_linear_sweep(
    N: int,
    omega: np.ndarray,
    time_steps: int,
    k_start: float = 0.0,
    k_end: float = 2.0,
    k_step: float = 0.1,
    seed: Optional[int] = None
) -> float:
    """
    Fallback: Finds Kc using a linear sweep if binary search fails.
    """
    logger.info("Performing linear sweep for Kc.")
    k_val = k_start
    while k_val <= k_end:
        r_mean, _ = simulate_kuramoto(N, omega, k_val, time_steps, seed=seed)
        if r_mean >= 0.5:
            logger.info(f"Linear sweep found Kc at K={k_val:.4f}")
            return k_val
        k_val += k_step
        
    logger.warning("Linear sweep did not find a synchronized state.")
    return k_end

def run_simulation_batch(
    graph_paths: List[str],
    config: Dict[str, Any],
    output_path: str = "data/processed/simulation_results.csv"
) -> None:
    """
    Runs the simulation for a batch of graphs and saves results to CSV.
    """
    time_steps = config['time_steps']
    run_count = config.get('run_count', 10)
    sc_violation = config.get('SC_003_VIOLATION', False)
    
    results = []
    
    logger.info(f"Starting batch simulation for {len(graph_paths)} graphs.")
    logger.info(f"Time steps: {time_steps}, Run count (for stability later): {run_count}")
    
    if sc_violation:
        logger.warning("SC_003_VIOLATION flag is set. Proceeding with reduced scope as defined in config.")
        
    for i, path in enumerate(graph_paths):
        logger.info(f"Processing graph {i+1}/{len(graph_paths)}: {path}")
        
        # Load graph
        import networkx as nx
        G = nx.read_gpickle(path)
        N = G.number_of_nodes()
        
        # Assign natural frequencies (uniform distribution for simplicity, or from degree)
        # Standard Kuramoto often uses identical oscillators (omega=0) or random.
        # We use random uniform [-0.5, 0.5]
        omega = np.random.uniform(-0.5, 0.5, N)
        
        # Run binary search to find Kc
        try:
            kc = find_critical_coupling_binary_search(
                N, omega, time_steps, seed=42 + i
            )
        except Exception as e:
            logger.error(f"Simulation failed for {path}: {e}")
            # Fallback
            kc = find_critical_coupling_linear_sweep(N, omega, time_steps, seed=42 + i)
            
        results.append({
            'graph_path': path,
            'N': N,
            'Kc': kc
        })
        
    # Write results
    import csv
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['graph_path', 'N', 'Kc'])
        writer.writeheader()
        writer.writerows(results)
        
    logger.info(f"Simulation batch complete. Results saved to {output_path}")

def main():
    """
    Main entry point for the simulation script.
    """
    # Load configuration
    try:
        config = load_config()
    except (FileNotFoundError, RuntimeError) as e:
        logger.error(f"Failed to load config: {e}")
        # If error is CONVERGENCE_FAILURE, we must stop.
        if "CONVERGENCE_FAILURE" in str(e):
            raise
        # Otherwise, log and try to proceed with defaults if possible, 
        # but task spec says raise if error key present.
        raise

    # Determine graph paths
    graph_dir = Path("data/processed")
    graph_files = sorted(graph_dir.glob("graph_p*.gpickle"))
    
    if not graph_files:
        logger.warning("No graph files found in data/processed. Exiting.")
        return

    # Run simulation
    run_simulation_batch(
        graph_paths=[str(f) for f in graph_files],
        config=config,
        output_path="data/processed/simulation_results.csv"
    )

if __name__ == "__main__":
    main()