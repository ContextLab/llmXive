"""
Performance verification script for GPE simulation.

This script runs simulations at two grid resolutions (256x256 for verification subset,
64x64 for full grid) to validate memory usage assumptions and runtime constraints.

It logs peak memory usage and execution time for each run to ensure they meet
the project's resource constraints (e.g., GitHub Actions runner limits).
"""
import os
import sys
import time
import resource
import traceback
from typing import Dict, Any, List, Optional

import numpy as np

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from utils.logger import get_logger, configure_logging
from utils.seed_manager import initialize_random_state
from config.grid_config import get_grid_resolution, get_domain_size, get_time_step, get_max_time, create_grid_config
from simulation.gpe_solver import GPEParameters, GPESolver, run_gpe_simulation
from models.entities import SimulationRun

# Configure logging
configure_logging(level="INFO")
logger = get_logger(__name__)

def get_peak_memory_mb() -> float:
    """Get peak memory usage in MB."""
    try:
        # Try Unix-specific resource module first
        rusage = resource.getrusage(resource.RUSAGE_SELF)
        # maxrss is in KB on Linux/macOS
        return rusage.ru_maxrss / 1024.0
    except AttributeError:
        # Fallback for Windows or if resource module is unavailable
        try:
            import psutil
            process = psutil.Process(os.getpid())
            return process.memory_info().peak_wset / (1024 * 1024)
        except Exception:
            logger.warning("Could not determine peak memory usage.")
            return 0.0

def run_verification_run(
    grid_size: int,
    omega: float,
    epsilon_dd: float,
    N: int,
    run_name: str,
    max_time: Optional[float] = None
) -> Dict[str, Any]:
    """
    Run a single GPE simulation and record performance metrics.

    Args:
        grid_size: Grid resolution (e.g., 64 or 256)
        omega: Rotation frequency
        epsilon_dd: Dipolar interaction strength
        N: Particle number
        run_name: Identifier for this run
        max_time: Maximum simulation time (optional, overrides config)

    Returns:
        Dictionary containing performance metrics.
    """
    logger.info(f"Starting verification run: {run_name} (Grid: {grid_size}x{grid_size})")

    # Initialize seed for reproducibility
    initialize_random_state(42)

    # Get grid parameters
    domain_size = get_domain_size()
    dt = get_time_step()
    if max_time is None:
        max_time = get_max_time()

    # Create grid config
    config = create_grid_config(
        grid_size=grid_size,
        domain_size=domain_size,
        dt=dt,
        max_time=max_time
    )

    # Create GPE parameters
    params = GPEParameters(
        omega=omega,
        epsilon_dd=epsilon_dd,
        N=N,
        grid_size=grid_size,
        domain_size=domain_size,
        dt=dt,
        max_time=max_time
    )

    # Record start memory and time
    start_memory_mb = get_peak_memory_mb()
    start_time = time.time()

    try:
        # Run simulation
        solver = GPESolver(params, config)
        result = run_gpe_simulation(solver, params, config)

        # Record end metrics
        end_time = time.time()
        end_memory_mb = get_peak_memory_mb()
        peak_memory_mb = max(start_memory_mb, end_memory_mb)

        # Calculate metrics
        runtime_seconds = end_time - start_time
        memory_growth_mb = peak_memory_mb - start_memory_mb

        logger.info(
            f"Run {run_name} completed successfully. "
            f"Runtime: {runtime_seconds:.2f}s, Peak Memory: {peak_memory_mb:.2f}MB, "
            f"Memory Growth: {memory_growth_mb:.2f}MB"
        )

        return {
            "run_name": run_name,
            "grid_size": grid_size,
            "omega": omega,
            "epsilon_dd": epsilon_dd,
            "N": N,
            "runtime_seconds": runtime_seconds,
            "peak_memory_mb": peak_memory_mb,
            "memory_growth_mb": memory_growth_mb,
            "status": "success",
            "error": None
        }

    except Exception as e:
        end_time = time.time()
        end_memory_mb = get_peak_memory_mb()
        runtime_seconds = end_time - start_time

        logger.error(f"Run {run_name} failed: {str(e)}")
        traceback.print_exc()

        return {
            "run_name": run_name,
            "grid_size": grid_size,
            "omega": omega,
            "epsilon_dd": epsilon_dd,
            "N": N,
            "runtime_seconds": runtime_seconds,
            "peak_memory_mb": end_memory_mb,
            "memory_growth_mb": 0.0,
            "status": "failed",
            "error": str(e)
        }

def main():
    """Main entry point for performance verification."""
    logger.info("=" * 60)
    logger.info("Starting GPE Simulation Performance Verification")
    logger.info("=" * 60)

    # Define test scenarios
    # 1. 256x256 subset (verification) - single point
    verification_runs = [
        {
            "grid_size": 256,
            "omega": 0.5,
            "epsilon_dd": 0.5,
            "N": 10000,
            "run_name": "verification_256x256"
        }
    ]

    # 2. 64x64 full grid scan - multiple points
    full_grid_runs = [
        {"grid_size": 64, "omega": 0.5, "epsilon_dd": 0.5, "N": 10000, "run_name": "full_64x64_01"},
        {"grid_size": 64, "omega": 0.5, "epsilon_dd": 1.0, "N": 10000, "run_name": "full_64x64_02"},
        {"grid_size": 64, "omega": 0.7, "epsilon_dd": 0.5, "N": 10000, "run_name": "full_64x64_03"},
        {"grid_size": 64, "omega": 0.7, "epsilon_dd": 1.0, "N": 10000, "run_name": "full_64x64_04"},
        {"grid_size": 64, "omega": 0.8, "epsilon_dd": 0.5, "N": 10000, "run_name": "full_64x64_05"},
        {"grid_size": 64, "omega": 0.8, "epsilon_dd": 1.0, "N": 10000, "run_name": "full_64x64_06"},
    ]

    all_results: List[Dict[str, Any]] = []

    # Run verification subset
    logger.info("\n--- Running Verification Subset (256x256) ---")
    for run_config in verification_runs:
        result = run_verification_run(**run_config)
        all_results.append(result)

    # Run full grid scan
    logger.info("\n--- Running Full Grid Scan (64x64) ---")
    for run_config in full_grid_runs:
        result = run_verification_run(**run_config)
        all_results.append(result)

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("PERFORMANCE VERIFICATION SUMMARY")
    logger.info("=" * 60)

    successful_runs = [r for r in all_results if r["status"] == "success"]
    failed_runs = [r for r in all_results if r["status"] == "failed"]

    if successful_runs:
        avg_runtime = np.mean([r["runtime_seconds"] for r in successful_runs])
        max_runtime = max([r["runtime_seconds"] for r in successful_runs])
        avg_memory = np.mean([r["peak_memory_mb"] for r in successful_runs])
        max_memory = max([r["peak_memory_mb"] for r in successful_runs])

        logger.info(f"Successful Runs: {len(successful_runs)}")
        logger.info(f"Failed Runs: {len(failed_runs)}")
        logger.info(f"Average Runtime: {avg_runtime:.2f}s")
        logger.info(f"Max Runtime: {max_runtime:.2f}s")
        logger.info(f"Average Peak Memory: {avg_memory:.2f}MB")
        logger.info(f"Max Peak Memory: {max_memory:.2f}MB")

        # Validate against assumptions
        # Assumption: 64x64 should complete in < 2 minutes per run
        # Assumption: 256x256 should complete in < 10 minutes (subset)
        # Assumption: Peak memory < 2GB for 64x64, < 4GB for 256x256
        if max_memory > 4096:
            logger.warning("WARNING: Peak memory exceeded 4GB assumption!")
        if max_runtime > 600:
            logger.warning("WARNING: Some runs exceeded 10-minute runtime assumption!")
    else:
        logger.error("No successful runs to summarize.")

    if failed_runs:
        logger.warning("\nFailed runs:")
        for r in failed_runs:
            logger.warning(f"  - {r['run_name']}: {r['error']}")

    logger.info("=" * 60)
    logger.info("Verification complete.")
    logger.info("=" * 60)

    # Return exit code based on success
    if failed_runs:
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()