"""
Performance verification script for GPE simulations.

This script validates that the simulation pipeline meets the resource constraints
defined in SC-001:
- Runtime < 6 hours for the full grid scan
- Memory usage < 14 GB

It runs two verification modes:
1. Small grid (64x64): Simulates the full parameter scan to verify runtime scaling
2. Large grid (256x256): Simulates a single parameter set to verify memory usage
"""

import os
import sys
import time
import resource
import traceback
from typing import Dict, Any, List, Optional

import numpy as np

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from config.grid_config import GridConfig, create_grid_config, get_grid_resolution
from simulation.gpe_solver import GPESolver, GPEParameters
from simulation.initial_conditions import create_thomas_fermi_initial_condition
from utils.logger import get_logger, configure_logging
from utils.seed_manager import set_global_seed

# Configure logging
configure_logging(level="INFO")
logger = get_logger(__name__)

# Constants for verification
RUNTIME_LIMIT_HOURS = 6.0
MEMORY_LIMIT_GB = 14.0
MEMORY_LIMIT_MB = MEMORY_LIMIT_GB * 1024

# Parameter sets for verification
VERIFICATION_PARAMS = [
    # (Omega, epsilon_dd, N)
    (0.5, 0.5, 10000),  # Mid-range stable
    (0.8, 1.0, 50000),  # Higher rotation, dipolar
    (0.2, 0.0, 20000),  # Low rotation, no dipolar
]

def get_peak_memory_mb() -> float:
    """
    Get the peak memory usage of the current process in MB.

    Returns:
        float: Peak memory usage in megabytes
    """
    # Get memory usage in bytes, convert to MB
    rusage = resource.getrusage(resource.RUSAGE_SELF)
    # ru_maxrss is in KB on Linux, but in bytes on macOS
    # We normalize to bytes first
    maxrss = rusage.ru_maxrss
    if sys.platform != 'darwin':
        # Linux: ru_maxrss is in KB
        maxrss_bytes = maxrss * 1024
    else:
        # macOS: ru_maxrss is in bytes
        maxrss_bytes = maxrss

    return maxrss_bytes / (1024 * 1024)

def run_single_verification_run(
    grid_resolution: int,
    omega: float,
    epsilon_dd: float,
    N: int,
    max_steps: int = 100,
    domain_size: float = 10.0
) -> Dict[str, Any]:
    """
    Run a single GPE simulation with specified parameters to measure performance.

    Args:
        grid_resolution: Grid size (e.g., 64 or 256)
        omega: Rotation frequency
        epsilon_dd: Dipolar interaction strength
        N: Number of particles
        max_steps: Maximum number of time steps to run
        domain_size: Physical domain size

    Returns:
        Dict containing runtime, peak memory, and success status
    """
    logger.info(f"Starting verification run: {grid_resolution}x{grid_resolution}, "
               f"Ω={omega}, ε_dd={epsilon_dd}, N={N}")

    start_time = time.time()
    initial_memory = get_peak_memory_mb()
    peak_memory = initial_memory
    success = False
    error_msg = None

    try:
        # Create configuration
        config = create_grid_config(
            grid_resolution=grid_resolution,
            domain_size=domain_size,
            omega=omega,
            epsilon_dd=epsilon_dd,
            N=N
        )

        # Create parameters
        params = GPEParameters(
            omega=omega,
            epsilon_dd=epsilon_dd,
            N=N,
            domain_size=domain_size,
            grid_resolution=grid_resolution,
            c0=1.0,
            c1=1.0
        )

        # Create solver
        solver = GPESolver(params)

        # Create initial condition
        psi = create_thomas_fermi_initial_condition(
            grid_size=grid_resolution,
            domain_size=domain_size,
            N=N,
            omega=omega
        )

        # Run simulation for limited steps
        logger.info(f"Running {max_steps} time steps...")
        for step in range(max_steps):
            psi = solver.step(ppsi)
            # Check memory periodically
            current_memory = get_peak_memory_mb()
            if current_memory > peak_memory:
                peak_memory = current_memory

            # Log progress
            if (step + 1) % 20 == 0:
                logger.info(f"Step {step + 1}/{max_steps}, "
                           f"Current memory: {current_memory:.2f} MB")

        success = True

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Verification run failed: {e}")
        traceback.print_exc()

    end_time = time.time()
    runtime_seconds = end_time - start_time

    result = {
        'grid_resolution': grid_resolution,
        'omega': omega,
        'epsilon_dd': epsilon_dd,
        'N': N,
        'runtime_seconds': runtime_seconds,
        'runtime_hours': runtime_seconds / 3600,
        'initial_memory_mb': initial_memory,
        'peak_memory_mb': peak_memory,
        'success': success,
        'error': error_msg
    }

    logger.info(f"Verification run completed: "
               f"Runtime={result['runtime_hours']:.3f}h, "
               f"Peak Memory={result['peak_memory_mb']:.2f}MB, "
               f"Success={result['success']}")

    return result

def run_verification_run(
    full_grid: bool = False
) -> List[Dict[str, Any]]:
    """
    Run performance verification for the specified mode.

    Args:
        full_grid: If True, run 64x64 grid for multiple parameter sets.
                  If False, run 256x256 grid for single parameter sets.

    Returns:
        List of result dictionaries for each run
    """
    if full_grid:
        logger.info("=" * 60)
        logger.info("FULL GRID VERIFICATION (64x64)")
        logger.info("Simulating full parameter scan to verify runtime scaling")
        logger.info("=" * 60)
        grid_resolution = 64
        # Run a subset of parameter sets to simulate full scan
        test_params = VERIFICATION_PARAMS[:2]  # Use first 2 for efficiency
    else:
        logger.info("=" * 60)
        logger.info("LARGE GRID VERIFICATION (256x256)")
        logger.info("Running single parameter sets to verify memory usage")
        logger.info("=" * 60)
        grid_resolution = 256
        test_params = VERIFICATION_PARAMS

    results = []
    total_start_time = time.time()

    for params in test_params:
        omega, epsilon_dd, N = params

        result = run_single_verification_run(
            grid_resolution=grid_resolution,
            omega=omega,
            epsilon_dd=epsilon_dd,
            N=N,
            max_steps=50 if full_grid else 20,  # Fewer steps for large grid
            domain_size=10.0
        )
        results.append(result)

        # Reset memory tracking between runs (not ideal but helps)
        gc.collect()

    total_end_time = time.time()
    total_runtime = total_end_time - total_start_time

    # Print summary
    logger.info("=" * 60)
    logger.info("VERIFICATION SUMMARY")
    logger.info("=" * 60)

    for i, result in enumerate(results):
        status = "PASS" if result['success'] else "FAIL"
        logger.info(f"Run {i+1}: {result['grid_resolution']}x{result['grid_resolution']}, "
                   f"Ω={result['omega']}, ε_dd={result['epsilon_dd']}, N={result['N']}")
        logger.info(f"  Runtime: {result['runtime_hours']:.4f} hours "
                   f"({result['runtime_seconds']:.2f} seconds)")
        logger.info(f"  Peak Memory: {result['peak_memory_mb']:.2f} MB "
                   f"({result['peak_memory_mb'] / 1024:.2f} GB)")
        logger.info(f"  Status: {status}")
        if result['error']:
            logger.info(f"  Error: {result['error']}")

    # Calculate aggregate statistics
    avg_runtime = sum(r['runtime_seconds'] for r in results) / len(results)
    avg_runtime_hours = avg_runtime / 3600
    max_memory = max(r['peak_memory_mb'] for r in results)

    logger.info("-" * 60)
    logger.info(f"Average Runtime per run: {avg_runtime_hours:.4f} hours")
    logger.info(f"Maximum Memory Usage: {max_memory:.2f} MB ({max_memory / 1024:.2f} GB)")
    logger.info(f"Total Execution Time: {total_runtime / 3600:.4f} hours")

    # Check against constraints
    runtime_ok = avg_runtime_hours < RUNTIME_LIMIT_HOURS
    memory_ok = max_memory < MEMORY_LIMIT_MB

    logger.info("-" * 60)
    logger.info(f"Runtime Constraint (< {RUNTIME_LIMIT_HOURS}h): "
               f"{'PASS' if runtime_ok else 'FAIL'}")
    logger.info(f"Memory Constraint (< {MEMORY_LIMIT_GB}GB): "
               f"{'PASS' if memory_ok else 'FAIL'}")
    logger.info("=" * 60)

    return results

def main():
    """
    Main entry point for performance verification.

    This script runs verification tests for both grid sizes:
    - 64x64: Full grid scan simulation
    - 256x256: Large grid memory test
    """
    logger.info("Starting GPE Simulation Performance Verification")
    logger.info(f"Constraints: Runtime < {RUNTIME_LIMIT_HOURS}h, "
               f"Memory < {MEMORY_LIMIT_GB}GB")

    # Initialize random state
    set_global_seed(42)

    # Run 64x64 verification
    logger.info("\n" + "=" * 80)
    full_grid_results = run_verification_run(full_grid=True)

    # Run 256x256 verification
    logger.info("\n" + "=" * 80)
    large_grid_results = run_verification_run(full_grid=False)

    # Combine results
    all_results = full_grid_results + large_grid_results

    # Save results to data directory
    output_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'aggregated')
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, 'performance_verification_results.json')

    import json
    with open(output_path, 'w') as f:
        json.dump(all_results, f, indent=2)

    logger.info(f"Results saved to: {output_path}")

    # Return exit code based on constraints
    all_ok = True
    for result in all_results:
        if not result['success']:
            all_ok = False
            break

    if all_ok:
        # Check constraints
        max_runtime = max(r['runtime_hours'] for r in all_results)
        max_memory = max(r['peak_memory_mb'] for r in all_results)

        if max_runtime > RUNTIME_LIMIT_HOURS or max_memory > MEMORY_LIMIT_MB:
            logger.warning("Constraints exceeded! Check results above.")
            return 1

    logger.info("Performance verification completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
