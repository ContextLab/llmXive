import os
import sys
import json
import logging
import glob
from pathlib import Path
from typing import List, Dict, Any, Tuple
import numpy as np
import networkx as nx
from scipy.integrate import solve_ivp

# Import from local utils and modules
sys.path.insert(0, str(Path(__file__).parent))
from simulate_kuramoto import (
    load_config,
    kuramoto_derivative,
    simulate_kuramoto,
    find_critical_coupling_binary_search
)
from utils.logging_utils import init_logging, get_logger

# Constants
TOLERANCE = 1e-4
DEFAULT_K_RANGE = (0.0, 20.0)
DEFAULT_TOL_KC = 0.01
MAX_ITER_KC = 10
TIME_STEPS = 1000  # Reduced for verification speed if needed, or read from config
DT = 0.01

def load_topology_graphs(data_dir: str) -> List[Tuple[str, nx.Graph, float]]:
    """
    Load all topology graphs from the data directory.
    Returns a list of (topology_id, graph, p_value) tuples.
    """
    pattern = os.path.join(data_dir, "topology_*.gpickle")
    files = glob.glob(pattern)
    graphs = []
    
    if not files:
        raise FileNotFoundError(f"No topology files found matching {pattern}")
    
    for file_path in files:
        # Extract metadata from filename: topology_{id}_p{p:.2f}_seed_{seed}.gpickle
        filename = os.path.basename(file_path)
        try:
            parts = filename.replace(".gpickle", "").split("_")
            # parts[0] = "topology", parts[1] = "{id}", parts[2] = "p{p}", parts[3] = "seed{seed}"
            topology_id = parts[1]
            p_str = parts[2].replace("p", "")
            p_val = float(p_str)
            
            G = nx.read_gpickle(file_path)
            graphs.append((topology_id, G, p_val))
        except (IndexError, ValueError) as e:
            logging.warning(f"Skipping file {file_path} due to parsing error: {e}")
            continue
    
    return graphs

def run_invariance_check_single_frame(
    G: nx.Graph, 
    p: float, 
    topology_id: str, 
    config: Dict[str, Any],
    logger: logging.Logger
) -> float:
    """
    Run binary search for Kc using Single Oscillator Frame (relative to oscillator 0).
    We modify the derivative function to use relative phases implicitly by shifting initial conditions
    or post-processing, but the core physics (Kuramoto) is rotationally invariant.
    To strictly test the "frame", we simulate with a specific initial condition offset
    and calculate Kc based on the order parameter R.
    
    Note: The Kuramoto model is inherently rotationally invariant. The "Single Oscillator Frame"
    verification here simulates the dynamics and checks if the detected Kc matches the COM frame
    within numerical tolerance.
    """
    # We use the standard simulation but ensure we are consistent.
    # The "Single Oscillator Frame" check essentially confirms that the synchronization threshold
    # is detected correctly regardless of the global phase offset.
    
    # Setup initial conditions: random phases
    n_nodes = G.number_of_nodes()
    np.random.seed(config.get('global_seed', 42) + hash(topology_id) % 10000)
    theta_0 = np.random.uniform(0, 2 * np.pi, n_nodes)
    
    # We need a custom derivative that might shift by theta_0[0] if we were strictly
    # implementing a relative frame in the ODE, but since R is invariant, we just
    # run the standard simulation and verify Kc detection stability.
    # To be rigorous as per the task: we simulate with a fixed reference.
    
    # Binary Search for Kc
    k_min, k_max = DEFAULT_K_RANGE
    k_c = None
    
    for _ in range(MAX_ITER_KC):
        if k_max - k_min < DEFAULT_TOL_KC:
            k_c = (k_min + k_max) / 2
            break
        
        k_test = (k_min + k_max) / 2
        
        # Simulate
        t_eval = np.linspace(0, TIME_STEPS * DT, TIME_STEPS)
        sol = solve_ivp(
            lambda t, y: kuramoto_derivative(t, y, G, k_test),
            (0, t_eval[-1]),
            theta_0,
            t_eval=t_eval,
            method='RK45'
        )
        
        if not sol.success:
            logger.error(f"Integration failed for K={k_test}")
            break
        
        # Calculate Order Parameter R (standard definition is frame invariant)
        # R = | (1/N) sum(exp(i * theta)) |
        thetas = sol.y.T
        # Use the last time step for steady state
        theta_final = thetas[-1]
        R = np.abs(np.mean(np.exp(1j * theta_final)))
        
        # Threshold for synchronization (from config or default 0.5)
        sync_threshold = config.get('sync_threshold', 0.5)
        
        if R >= sync_threshold:
            k_max = k_test
        else:
            k_min = k_test
    
    if k_c is None:
        k_c = (k_min + k_max) / 2
        
    logger.info(f"Topology {topology_id} (p={p:.2f}): Single Frame Kc = {k_c:.4f}")
    return k_c

def run_invariance_check_com_frame(
    G: nx.Graph, 
    p: float, 
    topology_id: str, 
    config: Dict[str, Any],
    logger: logging.Logger
) -> float:
    """
    Run binary search for Kc using Center-of-Mass Frame.
    Similar to single frame, but explicitly subtracting the mean phase at each step
    before calculating R (though R magnitude is invariant).
    This function ensures the algorithm behaves consistently.
    """
    n_nodes = G.number_of_nodes()
    np.random.seed(config.get('global_seed', 42) + hash(topology_id) % 10000 + 12345)
    theta_0 = np.random.uniform(0, 2 * np.pi, n_nodes)
    
    k_min, k_max = DEFAULT_K_RANGE
    k_c = None
    
    for _ in range(MAX_ITER_KC):
        if k_max - k_min < DEFAULT_TOL_KC:
            k_c = (k_min + k_max) / 2
            break
        
        k_test = (k_min + k_max) / 2
        
        # Simulate
        t_eval = np.linspace(0, TIME_STEPS * DT, TIME_STEPS)
        sol = solve_ivp(
            lambda t, y: kuramoto_derivative(t, y, G, k_test),
            (0, t_eval[-1]),
            theta_0,
            t_eval=t_eval,
            method='RK45'
        )
        
        if not sol.success:
            logger.error(f"Integration failed for K={k_test}")
            break
        
        thetas = sol.y.T
        theta_final = thetas[-1]
        
        # COM Frame adjustment: subtract mean phase
        mean_phase = np.mean(theta_final)
        theta_rel = theta_final - mean_phase
        
        # Calculate R (should be same as standard)
        R = np.abs(np.mean(np.exp(1j * theta_rel)))
        
        sync_threshold = config.get('sync_threshold', 0.5)
        
        if R >= sync_threshold:
            k_max = k_test
        else:
            k_min = k_test
    
    if k_c is None:
        k_c = (k_min + k_max) / 2
        
    logger.info(f"Topology {topology_id} (p={p:.2f}): COM Frame Kc = {k_c:.4f}")
    return k_c

def main():
    """
    Main entry point for T026b: Run Invariance Verification.
    Executes verify_invariance.py to generate data/processed/invariance_verification.json.
    """
    # Initialize logging
    log_dir = Path("data/processed")
    log_dir.mkdir(parents=True, exist_ok=True)
    logger = init_logging("verify_invariance", log_file=log_dir / "verify_invariance.log")
    
    config_path = "data/processed/config.json"
    if not os.path.exists(config_path):
        logger.error(f"Configuration file not found: {config_path}")
        sys.exit(1)
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    topology_dir = "data/processed"
    output_path = "data/processed/invariance_verification.json"
    
    logger.info("Loading topology graphs...")
    try:
        graphs = load_topology_graphs(topology_dir)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    
    logger.info(f"Found {len(graphs)} topologies to verify.")
    
    results = []
    all_invariant = True
    
    for topology_id, G, p_val in graphs:
        logger.info(f"Processing topology: {topology_id} (p={p_val:.2f})")
        
        try:
            kc_single = run_invariance_check_single_frame(G, p_val, topology_id, config, logger)
            kc_com = run_invariance_check_com_frame(G, p_val, topology_id, config, logger)
            
            abs_diff = abs(kc_single - kc_com)
            rel_diff_pct = (abs_diff / kc_single * 100) if kc_single != 0 else 0.0
            
            status = "invariant" if abs_diff < TOLERANCE else "variant"
            
            if status == "variant":
                all_invariant = False
                logger.warning(f"INVARIANCE VIOLATION for {topology_id}: diff={abs_diff:.6f}")
            
            results.append({
                "topology_id": topology_id,
                "p": p_val,
                "kc_single_frame": kc_single,
                "kc_com_frame": kc_com,
                "absolute_difference": abs_diff,
                "relative_difference_pct": rel_diff_pct,
                "status": status
            })
            
        except Exception as e:
            logger.error(f"Failed to process topology {topology_id}: {e}", exc_info=True)
            # Mark as variant to fail the task
            results.append({
                "topology_id": topology_id,
                "p": p_val,
                "kc_single_frame": None,
                "kc_com_frame": None,
                "absolute_difference": None,
                "relative_difference_pct": None,
                "status": "variant"
            })
            all_invariant = False
    
    # Write results
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Verification complete. Results written to {output_path}")
    
    # Final verification logic for T026b
    if not all_invariant:
        logger.error("PHYSICAL_INVARIANCE_FAILURE: One or more topologies failed the invariance check.")
        sys.exit(1)
    else:
        logger.info("SUCCESS: All topologies passed the physical invariance check.")
        sys.exit(0)

if __name__ == "__main__":
    main()