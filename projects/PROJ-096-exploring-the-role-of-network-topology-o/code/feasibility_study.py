import os
import sys
import json
import time
import logging
import numpy as np
from pathlib import Path

# Import from existing API surface
from utils.graph_utils import is_connected
from utils.logging_utils import init_logging, get_logger
from generate_topology import generate_regular_ring_lattice, generate_watts_strogatz_graph

# Constants
BUDGET_SECONDS = 6 * 3600  # 6 hours
MIN_TIME_STEPS = 1000
MAX_TIME_STEPS = 20000
FIXED_N_TOPOLOGIES = 50
MIN_TOPOLOGIES = 10
NODE_COUNT = 500
K = 2
DEFAULT_SEED = 42

def estimate_runtime_per_step(n_nodes: int, n_steps: int, seed: int = DEFAULT_SEED) -> float:
    """
    Run a single short simulation to measure runtime per step.
    Uses a synthetic ring lattice and a dummy Kuramoto-like integration loop.
    """
    logger = get_logger()
    logger.info(f"Estimating runtime per step for N={n_nodes}, steps={n_steps}")

    # Generate base graph
    G = generate_regular_ring_lattice(n_nodes, K)
    if not is_connected(G):
        logger.error("Base graph is not connected. Cannot proceed.")
        raise RuntimeError("Base graph connectivity check failed.")

    # Initialize phases (dummy Kuramoto state)
    phases = np.random.uniform(0, 2 * np.pi, n_nodes)
    dt = 0.01
    
    start_time = time.perf_counter()
    
    # Simulate n_steps (dummy integration: just phase rotation + noise)
    # This mimics the computational cost of the ODE solver without full physics
    for _ in range(n_steps):
        # Dummy derivative: dtheta/dt = omega + coupling_term
        # We use a simplified vectorized operation to approximate cost
        dtheta = np.random.normal(0, 0.01, n_nodes) 
        phases += dtheta * dt
        # Normalize phases
        phases = phases % (2 * np.pi)
    
    end_time = time.perf_counter()
    total_runtime = end_time - start_time
    runtime_per_step = total_runtime / n_steps
    
    logger.info(f"Runtime for {n_steps} steps: {total_runtime:.4f}s. Per step: {runtime_per_step:.6f}s")
    return runtime_per_step

def estimate_error(runs: list) -> float:
    """Estimate error margin from multiple runs."""
    if len(runs) < 2:
        return 0.0
    return float(np.std(runs))

def run_feasibility_study(output_path: str) -> dict:
    """
    Perform binary search for max time_steps within 6-hour budget.
    Writes config.json and returns the result dict.
    """
    logger = get_logger()
    logger.info("Starting Feasibility Study (T009)")

    # 1. Measure baseline: 1000 steps
    try:
        baseline_steps = 1000
        runtime_baseline = estimate_runtime_per_step(NODE_COUNT, baseline_steps)
    except Exception as e:
        logger.error(f"Failed to estimate baseline runtime: {e}")
        return write_failure_output(output_path, "BASELINE_ESTIMATION_FAILURE", str(e))

    # 2. Binary search for max time_steps
    # Constraint: 50 * (time_steps/1000) * runtime_baseline <= BUDGET_SECONDS
    # => time_steps <= (BUDGET_SECONDS * 1000) / (50 * runtime_baseline)
    
    max_possible_steps = int((BUDGET_SECONDS * 1000) / (50 * runtime_baseline))
    
    # Clamp search range
    low = MIN_TIME_STEPS
    high = min(max_possible_steps, MAX_TIME_STEPS)
    
    if high < low:
        logger.warning(f"Max feasible steps ({high}) is below minimum ({low}).")
        # Calculate max topologies for fixed 1000 steps
        max_topologies = int(BUDGET_SECONDS / (runtime_baseline * 1.0)) # 1 step unit logic
        # Actually: runtime for 1000 steps is runtime_baseline.
        # Total budget / runtime_per_1000_steps = max topologies
        runtime_1k = runtime_baseline * 1000
        max_topologies = int(BUDGET_SECONDS / runtime_1k)
        
        result = {
            "time_steps": MIN_TIME_STEPS,
            "n_topologies": max_topologies,
            "runtime_estimate": float(runtime_1k * max_topologies),
            "contingency_flag": max_topologies < MIN_TOPOLOGIES,
            "SC_003_VIOLATION": True,
            "scope_reduction_factor": 0.0, # Calculated later if needed
            "error": None
        }
        
        if max_topologies < MIN_TOPOLOGIES:
            logger.critical(f"CRITICAL WARNING: Insufficient compute for minimum scientific validity. Max topologies: {max_topologies}")
            result["n_topologies"] = MIN_TOPOLOGIES
            result["contingency_flag"] = True
            result["scope_reduction_factor"] = float(MIN_TOPOLOGIES) / MAX_TOPOLOGIES if MAX_TOPOLOGIES else 0.0
            # Adjust time steps down to fit if we force n_topologies
            # Budget = n_top * (steps/1000) * runtime_1k
            # steps = Budget / (n_top * runtime_1k) * 1000
            feasible_steps = int((BUDGET_SECONDS / (MIN_TOPOLOGIES * runtime_1k)) * 1000)
            result["time_steps"] = max(MIN_TIME_STEPS, feasible_steps) # Ensure at least min
            # If still not feasible, we set error or clamp
            if feasible_steps < MIN_TIME_STEPS:
                 result["time_steps"] = MIN_TIME_STEPS # Will exceed budget, but we try
                 result["error"] = "BUDGET_EXCEEDED_AFTER_CONTINGENCY"
        
        write_output(output_path, result)
        return result

    # Binary search to find exact max steps
    best_steps = low
    while low <= high:
        mid = (low + high) // 2
        # Estimate total time for 50 topologies
        estimated_total_time = 50 * (mid / 1000.0) * runtime_baseline
        
        if estimated_total_time <= BUDGET_SECONDS:
            best_steps = mid
            low = mid + 1
        else:
            high = mid - 1

    # 3. Calculate final metrics
    final_runtime_estimate = 50 * (best_steps / 1000.0) * runtime_baseline
    scope_reduction_factor = 1.0 if best_steps == MAX_TIME_STEPS else float(best_steps) / MAX_TIME_STEPS
    sc_003_violation = best_steps < MAX_TIME_STEPS or best_steps < MIN_TIME_STEPS # Assuming "full suite" is max steps

    result = {
        "time_steps": best_steps,
        "n_topologies": FIXED_N_TOPOLOGIES,
        "runtime_estimate": float(final_runtime_estimate),
        "contingency_flag": False,
        "SC_003_VIOLATION": sc_003_violation,
        "scope_reduction_factor": float(scope_reduction_factor),
        "error": None
    }

    if best_steps < MIN_TIME_STEPS:
        result["error"] = "CONVERGENCE_FAILURE"
        result["time_steps"] = 0
        write_output(output_path, result)
        return result

    write_output(output_path, result)
    logger.info(f"Feasibility Study Complete: {best_steps} steps, 50 topologies, est. time: {final_runtime_estimate:.2f}s")
    return result

def write_output(path: str, data: dict):
    """Write the config.json file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def write_failure_output(path: str, error_code: str, message: str):
    """Write a failure config.json."""
    data = {
        "time_steps": 0,
        "n_topologies": 0,
        "runtime_estimate": 0.0,
        "contingency_flag": False,
        "SC_003_VIOLATION": True,
        "scope_reduction_factor": 0.0,
        "error": error_code,
        "message": message
    }
    write_output(path, data)

def main():
    init_logging()
    logger = get_logger()
    output_path = "data/processed/config.json"
    
    try:
        result = run_feasibility_study(output_path)
        if result.get("error"):
            logger.error(f"Feasibility study failed: {result['error']} - {result.get('message', '')}")
            sys.exit(1)
        logger.info("Feasibility study completed successfully.")
    except Exception as e:
        logger.critical(f"Unexpected error in feasibility study: {e}")
        write_failure_output(output_path, "UNEXPECTED_ERROR", str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()
