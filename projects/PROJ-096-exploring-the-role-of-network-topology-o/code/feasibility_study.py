"""
Feasibility Study for Kuramoto Synchronization Experiment (T009).

Determines the maximum time steps, number of topologies, and run count feasible
within a 6-hour window on a 2-core CPU runner.

Logic:
1. Run a single simulation with time_steps = 1000 to measure runtime_per_1k_steps.
2. Binary search for max time_steps in [1000, 20000] for a fixed N=50 topologies.
3. If max time_steps < 1000, calculate max n_topologies for fixed 1000 steps.
4. HALT CONDITION: If feasible n_topologies < 10, set n_topologies=0 and error='INSUFFICIENT_SCOPE'.
5. Write results to data/processed/config.json.
"""

import os
import sys
import json
import time
import logging
import numpy as np
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
code_dir = project_root / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from simulate_kuramoto import simulate_kuramoto, load_config
from utils.graph_utils import is_connected
from utils.logging_utils import init_logging, get_logger

# Constants
MAX_WALL_CLOCK_SECONDS = 6 * 3600  # 6 hours
MIN_TIME_STEPS = 1000
MAX_TIME_STEPS_UPPER_BOUND = 20000
TARGET_TOPLOGIES = 50
MIN_VALID_TOPOLOGIES = 10
NODE_COUNT = 500
NEIGHBORS = 2
SEED = 42

logger = None

def estimate_runtime_per_step(time_steps: int, p: float = 0.5) -> float:
    """
    Runs a single Kuramoto simulation to measure time per step.
    Returns seconds per step.
    """
    global logger
    # Create a simple Watts-Strogatz graph for timing
    try:
        import networkx as nx
        G = nx.watts_strogatz_graph(NODE_COUNT, NEIGHBORS, p, seed=SEED)
        if not is_connected(G):
            # Retry with a different seed if disconnected
            G = nx.watts_strogatz_graph(NODE_COUNT, NEIGHBORS, p, seed=SEED + 1)
    except Exception as e:
        logger.error(f"Failed to generate timing graph: {e}")
        raise

    # Initialize phases
    phases = np.random.uniform(0, 2 * np.pi, NODE_COUNT)

    start_time = time.perf_counter()
    # Run simulation for specified steps
    # We pass a dummy K value that ensures fast convergence or just a few steps
    # to avoid long runs during timing. However, the task requires measuring
    # the actual cost of the ODE integration for the target steps.
    try:
        # Run simulation for a small batch to measure speed, then extrapolate?
        # The task says: "Run a single simulation with time_steps = 1000 to measure runtime_per_1k_steps"
        # So we run exactly 1000 steps for the base measurement, or the input time_steps.
        # To be safe and accurate, we run the input time_steps.
        _, _ = simulate_kuramoto(G, phases, K=1.0, t_eval=np.linspace(0, time_steps, time_steps))
    except Exception as e:
        logger.error(f"Simulation failed during timing: {e}")
        raise

    end_time = time.perf_counter()
    duration = end_time - start_time
    return duration / time_steps

def estimate_error():
    """
    Placeholder for error estimation if needed.
    Currently returns 0.0 as we rely on deterministic timing for feasibility.
    """
    return 0.0

def write_output(config: dict, output_path: Path):
    """Writes the configuration to JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(config, f, indent=2)
    logger.info(f"Configuration written to {output_path}")

def write_failure_output(error: str, output_path: Path):
    """Writes a failure configuration."""
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
    write_output(config, output_path)

def run_feasibility_study():
    """
    Main logic for the feasibility study.
    """
    global logger
    logger = init_logging(log_file=project_root / "data" / "feasibility_study.log")
    logger.info("Starting Feasibility Study (T009)")

    output_path = project_root / "data" / "processed" / "config.json"

    # 1. Measure runtime per 1000 steps
    logger.info("Measuring runtime per 1000 steps...")
    try:
        runtime_per_1k = estimate_runtime_per_step(1000)
        logger.info(f"Runtime per 1000 steps: {runtime_per_1k:.4f} seconds")
    except Exception as e:
        logger.error(f"Failed to measure runtime: {e}")
        write_failure_output("RUNTIME_MEASUREMENT_FAILURE", output_path)
        return

    # 2. Binary search for max time_steps
    # Constraint: 50 * (time_steps/1000) * runtime_per_1k <= MAX_WALL_CLOCK_SECONDS
    # Let T = time_steps.
    # 50 * (T/1000) * runtime_per_1k <= 21600
    # T <= (21600 * 1000) / (50 * runtime_per_1k)
    # T <= 432000 / runtime_per_1k

    max_possible_steps = int((MAX_WALL_CLOCK_SECONDS * 1000) / (TARGET_TOPLOGIES * runtime_per_1k))
    
    # Clamp to bounds
    if max_possible_steps < MIN_TIME_STEPS:
        max_feasible_steps = MIN_TIME_STEPS - 1 # Will trigger n_topologies calc
    else:
        # We need to find the max steps <= max_possible_steps but also <= MAX_TIME_STEPS_UPPER_BOUND
        max_feasible_steps = min(max_possible_steps, MAX_TIME_STEPS_UPPER_BOUND)

    logger.info(f"Calculated max feasible steps (for 50 topologies): {max_feasible_steps}")

    # 3. Determine n_topologies and time_steps
    final_time_steps = 0
    final_n_topologies = 0
    final_run_count = 1000 # Default run count for stability checks, can be adjusted
    scope_reduction_factor = 1.0
    sc_003_violation = False
    error_msg = None
    contingency_flag = False

    if max_feasible_steps < MIN_TIME_STEPS:
        # Case: Even 1000 steps is too much for 50 topologies.
        # Calculate max n_topologies for fixed 1000 steps.
        # Constraint: n * (1000/1000) * runtime_per_1k <= 21600
        # n <= 21600 / runtime_per_1k
        max_n = int(MAX_WALL_CLOCK_SECONDS / runtime_per_1k)
        
        final_time_steps = MIN_TIME_STEPS
        final_n_topologies = max_n
        
        logger.warning(f"Max steps < 1000. Calculated max n_topologies: {final_n_topologies}")

        if final_n_topologies < MIN_VALID_TOPOLOGIES:
            error_msg = "INSUFFICIENT_SCOPE"
            final_n_topologies = 0
            contingency_flag = True
            logger.critical("CRITICAL WARNING: Insufficient compute for minimum scientific validity.")
        else:
            # Scope reduced
            scope_reduction_factor = final_n_topologies / TARGET_TOPLOGIES
            sc_003_violation = True
            contingency_flag = True
    else:
        # Case: We can run at least 1000 steps.
        # We use the calculated max_feasible_steps.
        # If max_feasible_steps > 20000, we cap it at 20000 (upper bound) and recalculate n?
        # The task says binary search in [1000, 20000].
        # If the theoretical max is > 20000, we cap at 20000 and keep n=50.
        
        if max_feasible_steps > MAX_TIME_STEPS_UPPER_BOUND:
            final_time_steps = MAX_TIME_STEPS_UPPER_BOUND
            final_n_topologies = TARGET_TOPLOGIES
            logger.info(f"Max feasible steps capped at {MAX_TIME_STEPS_UPPER_BOUND}. Keeping n_topologies={TARGET_TOPLOGIES}.")
        else:
            final_time_steps = max_feasible_steps
            final_n_topologies = TARGET_TOPLOGIES
            # If we reduced steps from a theoretical higher number, is it a violation?
            # The target is usually defined by the science, not just compute.
            # If the target was 20000 and we got 15000, that's a reduction.
            # Assuming target was 20000 for this study context.
            if final_time_steps < MAX_TIME_STEPS_UPPER_BOUND:
                sc_003_violation = True
                contingency_flag = True
                scope_reduction_factor = final_time_steps / MAX_TIME_STEPS_UPPER_BOUND

    # 4. Calculate total runtime estimate
    total_runtime_estimate = final_n_topologies * (final_time_steps / 1000) * runtime_per_1k

    # 5. Construct output
    result = {
        "time_steps": final_time_steps,
        "n_topologies": final_n_topologies,
        "run_count": final_run_count,
        "runtime_estimate": total_runtime_estimate,
        "contingency_flag": contingency_flag,
        "SC_003_VIOLATION": sc_003_violation,
        "scope_reduction_factor": scope_reduction_factor,
        "error": error_msg
    }

    write_output(result, output_path)
    logger.info(f"Feasibility study complete. Output: {result}")

def main():
    run_feasibility_study()

if __name__ == "__main__":
    main()
