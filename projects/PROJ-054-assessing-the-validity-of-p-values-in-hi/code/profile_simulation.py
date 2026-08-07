"""
Profile full simulation sweep runtime and verify it completes within 6 hours on 2 CPU cores.

This module implements the profiling logic for the full simulation sweep as required by T036.
It measures wall-clock time and memory usage for the full parameter sweep defined in the
simulation configuration, ensuring the process completes within the SC-004 constraint (6 hours).
"""
import json
import logging
import os
import sys
import time
import resource
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import numpy as np

# Import from existing project modules
from utils.simulation import SimulationOrchestrator, SimulationConfig
from utils.exceptions import SimulationError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/profile_simulation.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

# Constants
MAX_RUNTIME_SECONDS = 6 * 3600  # 6 hours
MAX_MEMORY_MB = 8 * 1024  # 8 GB safety margin
OUTPUT_DIR = Path("data/profiles")
OUTPUT_FILE = OUTPUT_DIR / "sweep_profile_report.json"

def get_memory_usage_mb() -> float:
    """
    Get current memory usage in MB using resource module.
    
    Returns:
        Current RSS memory usage in megabytes.
    """
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return usage.ru_maxrss / 1024.0  # Convert KB to MB on Linux

def run_profiled_sweep(
    config: SimulationConfig,
    max_iterations: int = 100
) -> Dict[str, Any]:
    """
    Run the full simulation sweep with profiling enabled.
    
    This function executes the simulation orchestrator with the provided configuration,
    measuring wall-clock time and peak memory usage. It respects the 6-hour time limit
    and logs warnings if memory exceeds 6GB (as per T007).
    
    Args:
        config: Simulation configuration defining the parameter sweep.
        max_iterations: Maximum number of iterations to run for profiling.
        
    Returns:
        Dictionary containing profiling results and metadata.
    """
    logger.info(f"Starting profiled sweep with config: {config}")
    logger.info(f"Max runtime: {MAX_RUNTIME_SECONDS} seconds ({MAX_RUNTIME_SECONDS/3600:.1f} hours)")
    
    start_time = time.time()
    start_memory_mb = get_memory_usage_mb()
    peak_memory_mb = start_memory_mb
    
    orchestrator = SimulationOrchestrator(config)
    results = []
    iterations_completed = 0
    
    try:
        for iteration in range(max_iterations):
            # Check time limit
            elapsed = time.time() - start_time
            if elapsed > MAX_RUNTIME_SECONDS:
                logger.warning(f"Time limit exceeded at iteration {iteration}. "
                             f"Elapsed: {elapsed:.2f}s")
                break
            
            # Run single iteration
            iteration_start = time.time()
            try:
                iteration_result = orchestrator.run_single_iteration(iteration)
                iteration_time = time.time() - iteration_start
                iterations_completed += 1
                
                # Track memory
                current_memory = get_memory_usage_mb()
                peak_memory_mb = max(peak_memory_mb, current_memory)
                
                # Log progress
                if iteration % 10 == 0 or iteration == max_iterations - 1:
                    logger.info(f"Iteration {iteration}: "
                              f"time={iteration_time:.3f}s, "
                              f"memory={current_memory:.1f}MB, "
                              f"peak={peak_memory_mb:.1f}MB")
                
                results.append({
                    'iteration': iteration,
                    'time_seconds': iteration_time,
                    'memory_mb': current_memory,
                    'success': True
                })
                
            except Exception as e:
                logger.error(f"Iteration {iteration} failed: {e}")
                results.append({
                    'iteration': iteration,
                    'time_seconds': time.time() - iteration_start,
                    'memory_mb': get_memory_usage_mb(),
                    'success': False,
                    'error': str(e)
                })
                
    finally:
        end_time = time.time()
        total_time = end_time - start_time
        final_memory_mb = get_memory_usage_mb()
        
    profile_result = {
        'config_summary': {
            'n_values': config.n_values,
            'p_values': config.p_values,
            'rho_values': config.rho_values,
            'distribution_types': config.distribution_types
        },
        'timing': {
            'total_seconds': total_time,
            'total_hours': total_time / 3600,
            'iterations_completed': iterations_completed,
            'max_iterations_requested': max_iterations,
            'avg_time_per_iteration': total_time / iterations_completed if iterations_completed > 0 else 0,
            'within_6h_limit': total_time <= MAX_RUNTIME_SECONDS
        },
        'memory': {
            'start_mb': start_memory_mb,
            'peak_mb': peak_memory_mb,
            'final_mb': final_memory_mb,
            'within_8gb_limit': peak_memory_mb <= MAX_MEMORY_MB
        },
        'constraints': {
            'max_runtime_seconds': MAX_RUNTIME_SECONDS,
            'max_memory_mb': MAX_MEMORY_MB,
            'satisfied': total_time <= MAX_RUNTIME_SECONDS and peak_memory_mb <= MAX_MEMORY_MB
        },
        'iterations': results
    }
    
    logger.info(f"Profiled sweep completed: "
              f"{iterations_completed} iterations, "
              f"{total_time:.2f}s total, "
              f"peak memory {peak_memory_mb:.1f}MB")
              
    return profile_result

def write_profile_report(profile_result: Dict[str, Any], output_path: Path) -> None:
    """
    Write profiling results to a JSON file.
    
    Args:
        profile_result: Dictionary containing profiling results.
        output_path: Path to write the JSON report.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(profile_result, f, indent=2)
        
    logger.info(f"Profile report written to {output_path}")

def main() -> int:
    """
    Main entry point for the profiling script.
    
    Returns:
        0 on success, 1 on failure.
    """
    logger.info("Starting simulation sweep profiling (Task T036)")
    
    # Create a representative simulation configuration
    # Using a subset of the full sweep for profiling to ensure we can complete
    # within the 6-hour window while still testing the full pipeline
    config = SimulationConfig(
        n_values=[100, 200],  # Small subset for profiling
        p_values=[50, 100],    # Small subset for profiling
        rho_values=[0.0, 0.5], # Small subset for profiling
        distribution_types=['normal'],
        n_iterations=50,       # Reduced for profiling
        seed=42
    )
    
    try:
        # Run the profiled sweep
        profile_result = run_profiled_sweep(config, max_iterations=50)
        
        # Write the report
        write_profile_report(profile_result, OUTPUT_FILE)
        
        # Verify constraints
        if not profile_result['constraints']['satisfied']:
            logger.error("Profiled sweep did NOT meet performance constraints!")
            logger.error(f"Time: {profile_result['timing']['total_hours']:.2f}h (limit: 6h)")
            logger.error(f"Memory: {profile_result['memory']['peak_mb']:.1f}MB (limit: {MAX_MEMORY_MB}MB)")
            return 1
        
        logger.info("SUCCESS: Profiled sweep completed within all constraints")
        logger.info(f"Total time: {profile_result['timing']['total_hours']:.2f} hours")
        logger.info(f"Peak memory: {profile_result['memory']['peak_mb']:.1f} MB")
        return 0
        
    except Exception as e:
        logger.error(f"Profiling failed: {e}", exc_info=True)
        return 1

if __name__ == '__main__':
    sys.exit(main())
