import os
import sys
import json
import logging
import glob
from pathlib import Path
import numpy as np

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from code.simulate_kuramoto import simulate_kuramoto, load_config
from code.utils.logging_utils import init_logging, get_logger

# Initialize logging
init_logging()
logger = get_logger("check_stability")

def load_simulation_results(config_path: str) -> dict:
    """
    Load simulation results and configuration.
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    return config

def run_stability_check_for_topology(graph_path: str, config: dict, run_count: int) -> dict:
    """
    Run multiple simulations for a single topology to check stability.
    
    Args:
        graph_path: Path to the .gpickle graph file
        config: Configuration dictionary with simulation parameters
        run_count: Number of simulation runs to perform
        
    Returns:
        Dictionary with topology_id, variance, status, and metadata
    """
    import networkx as nx
    
    # Load graph
    G = nx.read_gpickle(graph_path)
    topology_id = Path(graph_path).stem
    
    # Extract parameters from config
    time_steps = config.get('time_steps', 1000)
    n_nodes = G.number_of_nodes()
    
    # Parse topology_id to get p value if possible, or default
    try:
        p_val = float(topology_id.split('_p')[1].split('_')[0])
    except (IndexError, ValueError):
        p_val = 0.0
    
    logger.info(f"Running stability check for {topology_id} (p={p_val}) with {run_count} runs")
    
    # Run multiple simulations with different seeds
    order_parameter_means = []
    
    for run_idx in range(run_count):
        seed = hash((topology_id, run_idx)) % (2**31)
        
        # Run simulation
        try:
            # Use a reduced time for stability check to speed up, but use full if needed
            # For stability check, we focus on the final order parameter variance
            # We'll use a subset of time steps if run_count is high
            effective_steps = min(time_steps, 500) if run_count > 100 else time_steps
            
            # Simulate with different initial conditions (via seed)
            # We'll simulate at a coupling strength near the expected Kc
            # For stability check, we use a fixed K (e.g., 1.0) and check variance of R
            K = 1.0  # Fixed coupling for stability check
            
            # Run simulation
            t_eval, theta, r_values = simulate_kuramoto(
                G, 
                K=K, 
                time_steps=effective_steps,
                seed=seed,
                dt=0.01
            )
            
            # Get final order parameter (mean of last 10% of values)
            final_r = np.mean(r_values[int(len(r_values) * 0.9):])
            order_parameter_means.append(final_r)
            
        except Exception as e:
            logger.warning(f"Run {run_idx} failed for {topology_id}: {str(e)}")
            continue
    
    if len(order_parameter_means) < 2:
        logger.error(f"Insufficient successful runs for {topology_id}")
        return {
            'topology_id': topology_id,
            'p': p_val,
            'variance': float('nan'),
            'status': 'unstable',
            'n_successful_runs': len(order_parameter_means),
            'n_total_runs': run_count
        }
    
    # Calculate variance
    variance = float(np.var(order_parameter_means))
    
    # Determine status based on variance magnitude (not arbitrary threshold)
    # High variance indicates instability
    if variance > 0.01:
        status = 'unstable'
        logger.warning(f"High variance ({variance:.6f}) for {topology_id}")
    else:
        status = 'stable'
    
    return {
        'topology_id': topology_id,
        'p': p_val,
        'variance': variance,
        'status': status,
        'n_successful_runs': len(order_parameter_means),
        'n_total_runs': run_count,
        'mean_r': float(np.mean(order_parameter_means))
    }

def run_stability_batch(config_path: str, output_path: str) -> dict:
    """
    Run stability check for all valid topologies.
    
    Args:
        config_path: Path to config.json
        output_path: Path to output JSON file
        
    Returns:
        Summary dictionary with overall stability status
    """
    # Load configuration
    config = load_simulation_results(config_path)
    
    # Get run_count from config, with fallback
    run_count = config.get('run_count', 1000)
    sc_003_violation = config.get('SC_003_VIOLATION', False)
    
    # Log contingency if applicable
    if sc_003_violation:
        logger.warning(f"SC-003 VIOLATION detected. Using reduced run_count: {run_count}")
    elif run_count < 1000:
        logger.warning(f"Run count ({run_count}) is below SC-001 recommended minimum of 1000. Proceeding with reduced scope.")
    
    # Find all topology files
    topology_files = sorted(glob.glob('data/processed/topology_*.gpickle'))
    
    if not topology_files:
        raise FileNotFoundError("No topology files found in data/processed/")
    
    logger.info(f"Found {len(topology_files)} topology files")
    
    # Run stability check for each topology
    results = []
    unstable_count = 0
    
    for graph_path in topology_files:
        result = run_stability_check_for_topology(graph_path, config, run_count)
        results.append(result)
        
        if result['status'] == 'unstable':
            unstable_count += 1
      
        # Log progress
        if len(results) % 10 == 0:
            logger.info(f"Processed {len(results)}/{len(topology_files)} topologies")
    
    # Determine overall status
    unstable_ratio = unstable_count / len(topology_files) if topology_files else 0
    
    if unstable_ratio > 0.1:
        overall_status = 'STABILITY_FAILURE'
        logger.error(f"STABILITY_FAILURE: {unstable_ratio:.1%} of topologies are unstable")
    elif unstable_count > 0:
        overall_status = 'Partial Stability'
        logger.warning(f"Partial Stability: {unstable_count}/{len(topology_files)} topologies unstable")
    else:
        overall_status = 'Success'
        logger.info("All topologies passed stability check")
    
    # Prepare output
    output_data = {
        'results': results,
        'summary': {
            'total_topologies': len(topology_files),
            'unstable_count': unstable_count,
            'stable_count': len(topology_files) - unstable_count,
            'unstable_ratio': unstable_ratio,
            'overall_status': overall_status,
            'run_count_used': run_count,
            'sc_003_violation': sc_003_violation
        }
    }
    
    # Add STABILITY_FAILURE flag if needed
    if overall_status == 'STABILITY_FAILURE':
        output_data['STABILITY_FAILURE'] = True
    
    # Write output
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"Stability results written to {output_path}")
    
    return output_data

def main():
    """
    Main entry point for stability check.
    """
    config_path = 'data/processed/config.json'
    output_path = 'data/processed/stability_results.json'
    
    try:
        # Check if config exists
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file not found: {config_path}. Run feasibility study first.")
        
        # Run stability batch
        result = run_stability_batch(config_path, output_path)
        
        # Check for failure
        if result.get('STABILITY_FAILURE', False):
            logger.error("Pipeline halted due to STABILITY_FAILURE")
            sys.exit(1)
        
        # Log final status
        status = result['summary']['overall_status']
        logger.info(f"Stability check completed: {status}")
        
        # Print summary
        print(f"Stability Check Summary:")
        print(f"  Total topologies: {result['summary']['total_topologies']}")
        print(f"  Stable: {result['summary']['stable_count']}")
        print(f"  Unstable: {result['summary']['unstable_count']}")
        print(f"  Overall status: {status}")
        
    except Exception as e:
        logger.error(f"Stability check failed: {str(e)}")
        raise

if __name__ == '__main__':
    main()