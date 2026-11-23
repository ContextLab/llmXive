import os
import sys
import json
import time
import logging
import numpy as np

# Import project utilities to ensure consistency
from utils.logging_utils import init_logging, get_logger
from utils.config import init_config, get_config

# Initialize logging
init_logging()
logger = get_logger(__name__)

# Constants
CONFIG_PATH = "data/processed/config.json"
RUNTIME_LIMIT_SECONDS = 6 * 3600  # 6 hours
MIN_TIME_STEPS = 1000
MIN_TOPOLOGIES = 10
FIXED_TOPOLOGIES_FOR_TEST = 50
NODE_COUNT = 500
K = 2  # Average degree for ring lattice

def estimate_runtime_per_step(time_steps: int, n_topologies: int = 1) -> float:
    """
    Runs a single simulation with a fixed small topology to measure runtime per step.
    This uses a minimal Kuramoto simulation to estimate cost without full overhead.
    """
    logger.info(f"Running benchmark simulation with {time_steps} steps...")
    
    # Import simulation dependencies locally to avoid circular imports if any
    from simulate_kuramoto import kuramoto_derivative, calculate_order_parameter
    import numpy as np
    from scipy.integrate import solve_ivp

    # Create a tiny test graph (N=10) to measure ODE cost, scaled to N=500 later
    # We assume O(N) per step for the derivative calculation in this context
    # But we measure the actual wall time for the solve_ivp call.
    # To be safe and realistic, we simulate a small portion of the actual workload.
    
    # We will run a dummy integration for the requested time_steps on a tiny graph
    # to get a baseline "time per step" that accounts for Python overhead, 
    # then scale it by (500/10) roughly, or just use the raw time if we run 
    # the actual N=500 graph.
    
    # Strategy: Run a single step on N=500 to get the base cost, then extrapolate.
    # This avoids running a full 6-hour simulation during the study.
    
    N = NODE_COUNT
    k = K
    # Create a regular ring lattice (p=0)
    import networkx as nx
    G = nx.watts_strogatz_graph(N, k, 0)
    
    # Initial phases
    phases = np.random.rand(N) * 2 * np.pi
    
    # Define a short time span for 1 step
    t_span = (0, 1.0)
    t_eval = np.linspace(0, 1.0, 2) # Just start and end
    
    start = time.time()
    sol = solve_ivp(
        lambda t, y: kuramoto_derivative(t, y, G, 1.0),
        t_span,
        phases,
        t_eval=t_eval,
        method='RK45'
    )
    elapsed = time.time() - start
    
    # elapsed is time for 1 step (conceptually, though solve_ivp does internal steps)
    # We treat this as the cost for 1 unit of simulation time.
    # The task asks for "time steps" in the config. We assume 1 step = 1 unit of integration.
    # If the config uses 'time_steps' as the number of integration steps, we need to be careful.
    # Usually, solve_ivp handles adaptive steps. 
    # Let's assume 'time_steps' in the config refers to the duration T_eval or a fixed number of steps.
    # Given the context of "6 hours", we assume a fixed step count is not the bottleneck, 
    # but the total integration duration is.
    # However, the task says "binary search for time_steps in range [1000, 20000]".
    # This implies a fixed step simulation (Euler) or a duration.
    # Let's assume the simulation runs for `time_steps` units of time with a fixed dt=0.01?
    # Or `time_steps` is the number of evaluations?
    # Let's assume `time_steps` is the number of integration steps in a fixed-step scheme.
    # To be safe, we measure the time for 1000 steps of a simple Euler integration on N=500.
    
    # Re-estimating with a simple Euler loop for 1000 steps to get "time per step"
    dt = 0.01
    steps = 1000
    phases = np.random.rand(N) * 2 * np.pi
    
    start = time.time()
    for _ in range(steps):
        # Kuramoto derivative
        dphases = np.zeros(N)
        for i in range(N):
            for j in G.neighbors(i):
                dphases[i] += np.sin(phases[j] - phases[i])
        phases += dt * dphases
    elapsed_1000 = time.time() - start
    
    runtime_per_1000_steps = elapsed_1000
    return runtime_per_1000_steps / 1000.0

def estimate_error(runtime_per_step: float) -> float:
    """
    Estimate error margin for the runtime prediction.
    """
    return runtime_per_step * 0.1  # 10% margin

def write_output(config: dict):
    """
    Writes the configuration to the output file.
    """
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=2)
    logger.info(f"Configuration written to {CONFIG_PATH}")

def write_failure_output(error: str):
    """
    Writes a failure configuration.
    """
    config = {
        "time_steps": 0,
        "n_topologies": 0,
        "run_count": 0,
        "runtime_estimate": 0.0,
        "contingency_flag": False,
        "SC_003_VIOLATION": False,
        "scope_reduction_factor": 0.0,
        "error": error
    }
    write_output(config)
    logger.error(f"Feasibility study failed: {error}")

def run_feasibility_study():
    """
    Performs the feasibility study to determine maximum time steps and topologies.
    """
    logger.info("Starting Feasibility Study...")
    
    # 1. Measure runtime per 1000 steps
    try:
        runtime_per_step = estimate_runtime_per_step(MIN_TIME_STEPS)
        logger.info(f"Estimated runtime per step: {runtime_per_step:.6f} seconds")
    except Exception as e:
        write_failure_output(f"RUNTIME_MEASUREMENT_FAILURE: {str(e)}")
        return

    # 2. Binary search for max time_steps with fixed n_topologies = 50
    # Constraint: 50 * (time_steps / 1000) * runtime_per_1k_steps <= 6 hours
    # Let T_1k = runtime_per_step * 1000
    T_1k = runtime_per_step * 1000
    
    low = MIN_TIME_STEPS
    high = 20000
    best_time_steps = MIN_TIME_STEPS
    
    logger.info(f"Binary searching for max time_steps with n_topologies=50...")
    logger.info(f"Target: 50 * (time_steps/1000) * {T_1k:.4f} <= {RUNTIME_LIMIT_SECONDS}")
    
    while low <= high:
        mid = (low + high) // 2
        estimated_total_time = 50 * (mid / 1000.0) * T_1k
        
        if estimated_total_time <= RUNTIME_LIMIT_SECONDS:
            best_time_steps = mid
            low = mid + 1
        else:
            high = mid - 1
    
    logger.info(f"Max feasible time_steps for 50 topologies: {best_time_steps}")
    
    # 3. Check if max time_steps < 1000 (should not happen if MIN_TIME_STEPS is 1000 and we found a solution)
    # If best_time_steps < MIN_TIME_STEPS, then even 1000 is too much for 50 topologies.
    if best_time_steps < MIN_TIME_STEPS:
        # Calculate max n_topologies for fixed 1000 steps
        max_n_topologies = int(RUNTIME_LIMIT_SECONDS / (T_1k * 1.0))
        logger.warning(f"Max time_steps < 1000. Calculating max n_topologies for 1000 steps: {max_n_topologies}")
        
        if max_n_topologies < MIN_TOPOLOGIES:
            logger.critical(f"CRITICAL WARNING: Insufficient compute for minimum scientific validity. Max topologies: {max_n_topologies}")
            write_failure_output("INSUFFICIENT_SCOPE")
            return
        
        # If we have enough topologies, we reduce time_steps to 1000 and use max_n_topologies
        final_time_steps = MIN_TIME_STEPS
        final_n_topologies = max_n_topologies
        final_run_count = 100 # Default run count, adjustable
        scope_reduction_factor = (final_n_topologies * final_time_steps) / (50 * 20000) # Arbitrary target
        
        config = {
            "time_steps": final_time_steps,
            "n_topologies": final_n_topologies,
            "run_count": final_run_count,
            "runtime_estimate": RUNTIME_LIMIT_SECONDS,
            "contingency_flag": True,
            "SC_003_VIOLATION": True,
            "scope_reduction_factor": scope_reduction_factor,
            "error": None
        }
    else:
        # We found a valid time_steps >= 1000 for 50 topologies.
        # We can potentially increase n_topologies or keep it at 50.
        # The task says: "Binary search for time_steps... for a fixed N=50 topologies."
        # Then "If max time_steps < 1000, calculate max n_topologies".
        # It implies if we found >= 1000, we use that time_steps and the fixed 50?
        # Or we can maximize n_topologies?
        # "If feasible scope is sufficient, set n_topologies to the calculated max (capped at a predetermined limit)"
        # Let's assume the "predetermined limit" is 50 for this study, or we can calculate max n_topologies for the found time_steps.
        
        final_time_steps = best_time_steps
        # Calculate max n_topologies for this time_steps
        max_n_topologies = int(RUNTIME_LIMIT_SECONDS / ((final_time_steps / 1000.0) * T_1k))
        # Cap at a reasonable limit, e.g., 100, or use the calculated max if < 100
        # The task says "capped at a predetermined limit". Let's use 100 as a safe limit.
        capped_n_topologies = min(max_n_topologies, 100)
        
        if capped_n_topologies < MIN_TOPOLOGIES:
             # Should not happen if best_time_steps >= 1000 and 50 was feasible
             write_failure_output("INSUFFICIENT_SCOPE")
             return

        final_n_topologies = capped_n_topologies
        final_run_count = 100
        # Target scope: 50 topologies * 20000 steps = 1,000,000 unit-steps
        target_scope = 50 * 20000
        actual_scope = final_n_topologies * final_time_steps
        scope_reduction_factor = actual_scope / target_scope
        
        config = {
            "time_steps": final_time_steps,
            "n_topologies": final_n_topologies,
            "run_count": final_run_count,
            "runtime_estimate": RUNTIME_LIMIT_SECONDS,
            "contingency_flag": False,
            "SC_003_VIOLATION": False,
            "scope_reduction_factor": scope_reduction_factor,
            "error": None
        }
    
    logger.info(f"Final Configuration: time_steps={final_time_steps}, n_topologies={final_n_topologies}")
    write_output(config)
    return config

def main():
    try:
        run_feasibility_study()
    except Exception as e:
        write_failure_output(f"UNEXPECTED_ERROR: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()