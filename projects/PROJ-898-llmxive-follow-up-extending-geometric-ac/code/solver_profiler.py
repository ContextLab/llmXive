"""
CPU-only solver profiler for verifying the <300s/step assumption on 2-core hardware.

This script simulates solver execution by running the actual symbolic solver
on synthetic but structurally valid problems (representative of the GAM task space).
It measures wall-clock time and reports statistics to verify the performance constraint.

Usage:
    python code/solver_profiler.py [--num_trials N] [--output data/results/profiling_results.csv]
"""
import csv
import logging
import os
import time
from typing import List, Dict, Any, Optional
import numpy as np
import signal
import sys
import threading

# Import from project API
from code.symbolic_solver import SymbolicSolver, TimeoutError
from code.config import load_config, SolverConfig
from code.utils import setup_logging, set_deterministic_seed

# Constants
DEFAULT_NUM_TRIALS = 20
DEFAULT_OUTPUT_PATH = "data/results/profiling_results.csv"
TARGET_MAX_TIME_SECONDS = 300.0
DEFAULT_TIMEOUT_SECONDS = 350.0  # Slightly above target to detect failures

def setup_profiling_logger(level: int = logging.INFO) -> logging.Logger:
    """Set up a dedicated logger for profiling."""
    logger = logging.getLogger("solver_profiler")
    logger.setLevel(level)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

def generate_synthetic_problem(
    solver_config: SolverConfig,
    rng: np.random.Generator
) -> Dict[str, Any]:
    """
    Generate a synthetic problem instance representative of GAM tasks.
    
    Creates a problem with:
    - Variable number of constraints (simulating different topologies)
    - Random but valid constraint matrices
    - Dimensions matching expected GFM latent space sizes
    
    Args:
        solver_config: Configuration for solver parameters
        rng: NumPy random generator for reproducibility
        
    Returns:
        Dictionary containing problem definition (P, q, G, h, A, b)
    """
    # Simulate a problem with 50-150 variables and 100-300 constraints
    # This mimics the scale of real robotic manipulation tasks
    num_vars = rng.integers(50, 151)
    num_constraints = rng.integers(100, 301)
    
    # Create random constraint matrices
    # Gx <= h (inequality constraints)
    G = rng.standard_normal((num_constraints, num_vars))
    h = rng.standard_normal(num_constraints) * 10.0
    
    # Ax = b (equality constraints) - fewer constraints
    num_eq = rng.integers(10, 51)
    A = rng.standard_normal((num_eq, num_vars))
    b = rng.standard_normal(num_eq) * 5.0
    
    # Objective vector
    c = rng.standard_normal(num_vars)
    
    return {
        "num_vars": num_vars,
        "num_ineq": num_constraints,
        "num_eq": num_eq,
        "G": G,
        "h": h,
        "A": A,
        "b": b,
        "c": c
    }

def run_single_trial(
    trial_id: int,
    problem: Dict[str, Any],
    solver_config: SolverConfig,
    timeout_seconds: float,
    logger: logging.Logger
) -> Dict[str, Any]:
    """
    Run a single solver trial and measure execution time.
    
    Args:
        trial_id: Unique identifier for this trial
        problem: Synthetic problem instance
        solver_config: Solver configuration
        timeout_seconds: Maximum allowed time for this trial
        logger: Logger instance
        
    Returns:
        Dictionary with trial results including timing and status
    """
    solver = SymbolicSolver(solver_config)
    start_time = time.perf_counter()
    
    success = False
    timed_out = False
    error_msg = None
    
    try:
        # Set up timeout handling
        def timeout_handler(signum, frame):
            raise TimeoutError(f"Solver timed out after {timeout_seconds}s")
        
        # Register signal handler (Unix only)
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(int(timeout_seconds))
        
        try:
            # Run the solver
            result = solver.solve(
                P=None,  # Quadratic term (optional)
                q=problem["c"],
                G=problem["G"],
                h=problem["h"],
                A=problem["A"],
                b=problem["b"]
            )
            success = result is not None
        finally:
            # Cancel alarm and restore handler
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)
            
    except TimeoutError as e:
        timed_out = True
        error_msg = str(e)
        logger.warning(f"Trial {trial_id} timed out: {error_msg}")
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Trial {trial_id} failed with error: {error_msg}")
        
    end_time = time.perf_counter()
    elapsed_time = end_time - start_time
    
    return {
        "trial_id": trial_id,
        "num_vars": problem["num_vars"],
        "num_constraints": problem["num_ineq"] + problem["num_eq"],
        "elapsed_time_seconds": elapsed_time,
        "success": success,
        "timed_out": timed_out,
        "error_message": error_msg,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

def save_results(results: List[Dict[str, Any]], output_path: str, logger: logging.Logger):
    """Save profiling results to CSV."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    fieldnames = [
        "trial_id", "num_vars", "num_constraints", "elapsed_time_seconds",
        "success", "timed_out", "error_message", "timestamp"
    ]
    
    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    logger.info(f"Results saved to {output_path}")

def main():
    """Main entry point for the profiler."""
    logger = setup_profiling_logger()
    logger.info("Starting CPU-only solver profiler")
    
    # Load configuration
    config = load_config()
    solver_config = config.solver
    
    # Set seed for reproducibility
    set_deterministic_seed(config.experiment.seed)
    rng = np.random.default_rng(config.experiment.seed)
    
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="CPU-only solver profiler")
    parser.add_argument(
        "--num_trials", 
        type=int, 
        default=DEFAULT_NUM_TRIALS,
        help=f"Number of trials to run (default: {DEFAULT_NUM_TRIALS})"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=DEFAULT_OUTPUT_PATH,
        help=f"Output CSV path (default: {DEFAULT_OUTPUT_PATH})"
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT_SECONDS,
        help=f"Timeout per trial in seconds (default: {DEFAULT_TIMEOUT_SECONDS})"
    )
    args = parser.parse_args()
    
    num_trials = args.num_trials
    output_path = args.output
    timeout_seconds = args.timeout
    
    logger.info(f"Running {num_trials} trials with {timeout_seconds}s timeout")
    
    results = []
    for trial_id in range(1, num_trials + 1):
        logger.info(f"Running trial {trial_id}/{num_trials}")
        
        # Generate synthetic problem
        problem = generate_synthetic_problem(solver_config, rng)
        
        # Run trial
        result = run_single_trial(
            trial_id, problem, solver_config, timeout_seconds, logger
        )
        results.append(result)
        
        # Log individual results
        status = "SUCCESS" if result["success"] else "FAILED"
        if result["timed_out"]:
            status = "TIMEOUT"
        logger.info(
            f"Trial {trial_id}: {status} - "
            f"{problem['num_vars']} vars, "
            f"{problem['num_constraints']} constraints, "
            f"{result['elapsed_time_seconds']:.2f}s"
        )
    
    # Save results
    save_results(results, output_path, logger)
    
    # Compute and log summary statistics
    elapsed_times = [r["elapsed_time_seconds"] for r in results if r["success"]]
    if elapsed_times:
        mean_time = np.mean(elapsed_times)
        std_time = np.std(elapsed_times)
        max_time = np.max(elapsed_times)
        min_time = np.min(elapsed_times)
        
        logger.info("=" * 60)
        logger.info("PROFILING SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total trials: {num_trials}")
        logger.info(f"Successful trials: {len(elapsed_times)}")
        logger.info(f"Mean time: {mean_time:.2f}s")
        logger.info(f"Std dev: {std_time:.2f}s")
        logger.info(f"Min time: {min_time:.2f}s")
        logger.info(f"Max time: {max_time:.2f}s")
        
        # Verify against target
        if max_time < TARGET_MAX_TIME_SECONDS:
            logger.info(
                f"✓ PASS: All successful trials completed in < {TARGET_MAX_TIME_SECONDS}s"
            )
        else:
            logger.warning(
                f"✗ FAIL: Some trials exceeded {TARGET_MAX_TIME_SECONDS}s "
                f"(max: {max_time:.2f}s)"
            )
        logger.info("=" * 60)
    else:
        logger.warning("No successful trials to summarize")

if __name__ == "__main__":
    main()
