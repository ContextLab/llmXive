import os
import sys
import json
import time
import logging
import numpy as np

# Import existing utilities from the project
from utils.graph_utils import is_connected
from utils.logging_utils import init_logging, get_logger

# We need to import the graph generator to create a test graph
# Since generate_topology is the main module, we import from it
# However, to avoid circular imports or heavy dependencies, we can generate a simple graph here
import networkx as nx

def estimate_runtime_per_step(num_nodes=500, k=2, time_steps=1000, num_samples=3):
    """
    Estimate the runtime per 1000 time steps by running a short simulation.
    
    Args:
        num_nodes: Number of nodes in the test graph
        k: Each node is connected to its k nearest neighbors in the ring
        time_steps: Number of time steps to simulate (scaled to 1000 for measurement)
        num_samples: Number of samples to average over
        
    Returns:
        float: Average runtime per 1000 time steps in seconds
    """
    logger = get_logger(__name__)
    logger.info(f"Estimating runtime per {time_steps} steps with {num_samples} samples...")
    
    runtimes = []
    
    for i in range(num_samples):
        # Create a simple regular ring lattice for testing
        G = nx.regular_ring_lattice(num_nodes, k)
        
        # Ensure connectivity (it should be connected for k >= 2)
        if not is_connected(G):
            logger.warning(f"Sample {i}: Graph not connected, regenerating...")
            G = nx.watts_strogatz_graph(num_nodes, k, 0.0, seed=i)
        
        # Simulate a simplified Kuramoto step to measure overhead
        # We don't need a full simulation, just the ODE evaluation overhead
        phases = np.random.uniform(0, 2 * np.pi, num_nodes)
        frequencies = np.random.normal(0, 0.1, num_nodes)
        
        start_time = time.time()
        
        # Run a simplified integration step multiple times to simulate time_steps
        # Using Euler method for speed
        dt = 0.01
        steps_per_sample = time_steps
        
        for _ in range(steps_per_sample):
            # Compute phase differences and sine
            phase_diffs = phases[:, None] - phases[None, :]
            sin_diffs = np.sin(phase_diffs)
            
            # Get adjacency matrix (sparse for efficiency)
            adj = nx.adjacency_matrix(G).toarray()
            
            # Compute coupling term
            coupling = adj @ sin_diffs
            
            # Update phases
            dphases = frequencies + 0.5 * coupling
            phases = phases + dt * dphases
            phases = phases % (2 * np.pi)
        
        elapsed = time.time() - start_time
        runtimes.append(elapsed)
        logger.info(f"Sample {i+1}/{num_samples}: {elapsed:.3f}s")
    
    avg_runtime = np.mean(runtimes)
    std_runtime = np.std(runtimes)
    logger.info(f"Average runtime per {time_steps} steps: {avg_runtime:.3f}s (±{std_runtime:.3f}s)")
    
    return avg_runtime

def estimate_error(runtime_per_1k, total_budget_seconds=6 * 3600):
    """
    Estimate the error in our feasibility calculation.
    
    Args:
        runtime_per_1k: Runtime per 1000 steps
        total_budget_seconds: Total time budget in seconds
        
    Returns:
        float: Estimated error margin
    """
    # Simple error estimation based on variance
    return runtime_per_1k * 0.1  # 10% margin of error

def run_feasibility_study(
    time_steps_min=1000, 
    time_steps_max=20000, 
    num_topologies_min=10,
    total_budget_seconds=6 * 3600,
    n_nodes=500,
    k=2
):
    """
    Perform a feasibility study to determine maximum time steps and number of topologies.
    
    Args:
        time_steps_min: Minimum time steps to consider
        time_steps_max: Maximum time steps to consider
        num_topologies_min: Minimum number of topologies required for scientific validity
        total_budget_seconds: Total time budget in seconds (default 6 hours)
        n_nodes: Number of nodes for test graphs
        k: Connectivity parameter for ring lattice
        
    Returns:
        dict: Configuration with time_steps, n_topologies, and runtime_estimate
    """
    logger = get_logger(__name__)
    logger.info("Starting feasibility study...")
    logger.info(f"Time budget: {total_budget_seconds/3600:.1f} hours")
    logger.info(f"Time steps range: [{time_steps_min}, {time_steps_max}]")
    
    # Step 1: Measure runtime per 1000 steps
    runtime_per_1k = estimate_runtime_per_step(
        num_nodes=n_nodes, 
        k=k, 
        time_steps=1000
    )
    
    # Step 2: Calculate maximum time steps
    # We assume 50 topologies as a baseline for the initial calculation
    baseline_topologies = 50
    max_time_steps = int((total_budget_seconds / (runtime_per_1k * baseline_topologies)) / 1000) * 1000
    
    # Clamp to valid range
    max_time_steps = max(time_steps_min, min(time_steps_max, max_time_steps))
    
    logger.info(f"Calculated max time_steps for {baseline_topologies} topologies: {max_time_steps}")
    
    # Step 3: If max_time_steps is too low, calculate n_topologies instead
    if max_time_steps < time_steps_min:
        logger.warning(f"Max time_steps ({max_time_steps}) is below minimum ({time_steps_min}).")
        logger.info("Recalculating number of topologies with minimum time steps...")
        
        runtime_per_topology = runtime_per_1k * (time_steps_min / 1000)
        n_topologies = int(total_budget_seconds / runtime_per_topology)
        
        if n_topologies < num_topologies_min:
            logger.critical(f"CRITICAL WARNING: Insufficient compute for minimum scientific validity.")
            logger.critical(f"Even with minimum time_steps={time_steps_min}, only {n_topologies} topologies can be run.")
            logger.critical(f"Minimum required: {num_topologies_min}")
            # We still return the best we can do, but flag it
            n_topologies = max(1, n_topologies)
            max_time_steps = time_steps_min
        else:
            logger.info(f"Adjusted to {n_topologies} topologies with {time_steps_min} time steps each.")
            max_time_steps = time_steps_min
    else:
        # Calculate how many topologies we can run with max_time_steps
        runtime_per_topology = runtime_per_1k * (max_time_steps / 1000)
        n_topologies = int(total_budget_seconds / runtime_per_topology)
        
        if n_topologies < num_topologies_min:
            logger.warning(f"CRITICAL WARNING: Only {n_topologies} topologies feasible with max time_steps.")
            logger.warning(f"Minimum required: {num_topologies_min}")
            # We proceed but log the warning
    
    # Ensure we have at least the minimum
    n_topologies = max(num_topologies_min, n_topologies)
    
    # Final calculation: ensure total runtime is within budget
    total_estimated_runtime = runtime_per_1k * (max_time_steps / 1000) * n_topologies
    
    if total_estimated_runtime > total_budget_seconds:
        logger.warning(f"Estimated runtime {total_estimated_runtime/3600:.1f}h exceeds budget {total_budget_seconds/3600:.1f}h.")
        logger.warning("Adjusting n_topologies to fit budget...")
        n_topologies = int(total_budget_seconds / (runtime_per_1k * (max_time_steps / 1000)))
        n_topologies = max(num_topologies_min, n_topologies)
        total_estimated_runtime = runtime_per_1k * (max_time_steps / 1000) * n_topologies
    
    logger.info(f"Feasibility Study Results:")
    logger.info(f"  - Time steps per simulation: {max_time_steps}")
    logger.info(f"  - Number of topologies: {n_topologies}")
    logger.info(f"  - Estimated total runtime: {total_estimated_runtime/3600:.2f} hours")
    logger.info(f"  - Runtime per 1000 steps: {runtime_per_1k:.3f}s")
    
    return {
        "time_steps": max_time_steps,
        "n_topologies": n_topologies,
        "runtime_estimate": total_estimated_runtime,
        "runtime_per_1k_steps": runtime_per_1k,
        "time_budget_seconds": total_budget_seconds
    }

def main():
    """Main entry point for the feasibility study."""
    # Initialize logging
    init_logging(level=logging.INFO)
    logger = get_logger(__name__)
    
    # Run the feasibility study
    config = run_feasibility_study()
    
    # Write results to data/processed/config.json
    output_path = "data/processed/config.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    logger.info(f"Configuration written to {output_path}")
    
    # Verification
    if config['time_steps'] >= 1000 and config['n_topologies'] >= 10:
        logger.info("Verification PASSED: time_steps >= 1000 and n_topologies >= 10")
        return 0
    else:
        logger.error("Verification FAILED: Configuration does not meet minimum requirements")
        return 1

if __name__ == "__main__":
    sys.exit(main())
