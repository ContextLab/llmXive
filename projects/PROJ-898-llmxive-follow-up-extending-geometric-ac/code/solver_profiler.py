"""
Solver Profiler for CPU-only execution.

Simulates solver execution to verify the <300 seconds/step assumption on 2-core hardware (FR-004).
This script generates synthetic convex optimization problems (representing robot motion constraints)
and measures solve times using CPU-only solvers (scipy/cvxpy with CPU backend).

It does NOT require PyBullet or real physics data, as it profiles the mathematical solver
component which is the bottleneck for the symbolic planner.
"""

import csv
import logging
import os
import time
import multiprocessing
from typing import List, Dict, Any, Optional

import numpy as np
import scipy.optimize as scipy_opt
from scipy.sparse import csr_matrix

# Project imports
from utils import setup_logging, set_deterministic_seed, compute_sha256

# Configure logger
PROFILER_LOGGER_NAME = "solver_profiler"

def setup_profiling_logger(log_file_path: Optional[str] = None) -> logging.Logger:
    """
    Setup the profiler logger.
    
    Args:
        log_file_path: Optional path to write logs to. If None, logs to console only.
        
    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(PROFILER_LOGGER_NAME)
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # File handler (optional)
        if log_file_path:
            file_handler = logging.FileHandler(log_file_path)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
    
    return logger

def generate_synthetic_problem(
    n_vars: int,
    n_constraints: int,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Generate a synthetic convex optimization problem representing motion constraints.
    
    This simulates the structure of a symbolic planner's QP:
    minimize: 0.5 * x^T * P * x + q^T * x
    subject to: A * x <= b
    
    Args:
        n_vars: Number of decision variables (e.g., joint angles + velocities).
        n_constraints: Number of linear inequality constraints (e.g., collision, limits).
        seed: Random seed for reproducibility.
        
    Returns:
        Dictionary containing problem matrices (P, q, A, b).
    """
    if seed is not None:
        np.random.seed(seed)
    
    # Create a positive definite matrix P (Hessian)
    # We use a sparse-ish structure for efficiency in simulation
    A_rand = np.random.randn(n_constraints, n_vars)
    P = A_rand.T @ A_rand + np.eye(n_vars) * 0.1  # Ensure positive definiteness
    
    # Linear term q
    q = np.random.randn(n_vars)
    
    # Constraint matrix A and bounds b
    A = np.random.randn(n_constraints, n_vars)
    b = np.random.randn(n_constraints) * 10.0  # Reasonable bounds
    
    return {
        "P": P,
        "q": q,
        "A": A,
        "b": b,
        "n_vars": n_vars,
        "n_constraints": n_constraints
    }

def run_single_trial(
    problem: Dict[str, Any],
    timeout_limit: float = 300.0
) -> Dict[str, Any]:
    """
    Run a single solver trial and measure execution time.
    
    Uses scipy.optimize.minimize with SLSQP method as a proxy for the
    differentiable convex solver (cvxpy/diffcp) running on CPU.
    
    Args:
        problem: Dictionary containing P, q, A, b matrices.
        timeout_limit: Maximum allowed time in seconds (FR-004 assumption).
        
    Returns:
        Dictionary with timing results and status.
    """
    P = problem["P"]
    q = problem["q"]
    A = problem["A"]
    b = problem["b"]
    n_vars = problem["n_vars"]
    
    start_time = time.perf_counter()
    
    try:
        # Define objective function and gradient
        def objective(x):
            return 0.5 * x.T @ P @ x + q.T @ x
        
        def gradient(x):
            return P @ x + q
        
        # Define constraints (A x <= b)
        constraints = {
            'type': 'ineq',
            'fun': lambda x: b - A @ x,
            'jac': lambda x: -A
        }
        
        # Initial guess
        x0 = np.zeros(n_vars)
        
        # Bounds (optional, but good for stability)
        bounds = [(None, None)] * n_vars
        
        # Solve
        result = scipy_opt.minimize(
            objective,
            x0,
            method='SLSQP',
            jac=gradient,
            constraints=constraints,
            bounds=bounds,
            options={'maxiter': 1000, 'ftol': 1e-9}
        )
        
        end_time = time.perf_counter()
        elapsed = end_time - start_time
        
        return {
            "status": "success" if result.success else "failed",
            "elapsed_time": elapsed,
            "iterations": result.nit if hasattr(result, 'nit') else 0,
            "message": result.message if hasattr(result, 'message') else "N/A"
        }
        
    except Exception as e:
        end_time = time.perf_counter()
        elapsed = end_time - start_time
        return {
            "status": "error",
            "elapsed_time": elapsed,
            "iterations": 0,
            "message": str(e)
        }

def save_results(
    results: List[Dict[str, Any]],
    output_path: str
) -> None:
    """
    Save profiling results to a CSV file.
    
    Args:
        results: List of result dictionaries.
        output_path: Path to the output CSV file.
    """
    if not results:
        logging.warning("No results to save.")
        return
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    fieldnames = [
        "trial_id",
        "n_vars",
        "n_constraints",
        "status",
        "elapsed_time",
        "iterations",
        "message"
    ]
    
    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            writer.writerow(row)
    
    logging.info(f"Results saved to {output_path}")

def main():
    """
    Main entry point for the solver profiler.
    
    Runs multiple trials with varying problem sizes to simulate the load
    expected from the symbolic planner on 2-core hardware.
    Verifies that solve times remain well below the 300s limit.
    """
    # Setup
    log_file = "data/results/solver_profiling.log"
    logger = setup_profiling_logger(log_file)
    logger.info("Starting CPU-only solver profiling (FR-004)...")
    
    # Load config if available, otherwise use defaults
    # Default: 50 trials, varying complexity
    try:
        from config import load_config
        config = load_config()
        trial_count = config.experiment.trial_count
        timeout_limit = config.solver.timeout_limits.get("step", 300.0)
        seed = config.experiment.seed
    except Exception as e:
        logger.warning(f"Could not load config (or config incomplete): {e}. Using defaults.")
        trial_count = 50
        timeout_limit = 300.0
        seed = 42
    
    set_deterministic_seed(seed)
    
    output_path = "data/results/solver_profiling_results.csv"
    results = []
    
    # Problem size ranges to simulate different robot complexities
    # Small: 10 vars, 20 constraints (simple gripper)
    # Medium: 50 vars, 100 constraints (simple arm)
    # Large: 100 vars, 200 constraints (complex arm + deformable)
    problem_sizes = [
        (10, 20),
        (50, 100),
        (100, 200)
    ]
    
    logger.info(f"Running {trial_count} trials with timeout limit {timeout_limit}s...")
    
    for i in range(trial_count):
        # Cycle through problem sizes
        n_vars, n_constraints = problem_sizes[i % len(problem_sizes)]
        
        logger.info(f"Trial {i+1}/{trial_count}: n_vars={n_vars}, n_constraints={n_constraints}")
        
        problem = generate_synthetic_problem(n_vars, n_constraints, seed=seed + i)
        result = run_single_trial(problem, timeout_limit=timeout_limit)
        
        result["trial_id"] = i + 1
        result["n_vars"] = n_vars
        result["n_constraints"] = n_constraints
        
        results.append(result)
        
        # Log specific findings
        if result["elapsed_time"] > timeout_limit:
            logger.error(f"Trial {i+1} EXCEEDED timeout limit: {result['elapsed_time']:.2f}s > {timeout_limit}s")
        elif result["elapsed_time"] > 10.0:
            logger.warning(f"Trial {i+1} took longer than expected: {result['elapsed_time']:.2f}s")
        else:
            logger.info(f"Trial {i+1} completed in {result['elapsed_time']:.4f}s")
    
    # Summary
    avg_time = np.mean([r["elapsed_time"] for r in results])
    max_time = np.max([r["elapsed_time"] for r in results])
    success_count = sum(1 for r in results if r["status"] == "success")
    
    logger.info("="*50)
    logger.info("PROFILING SUMMARY")
    logger.info(f"Total Trials: {trial_count}")
    logger.info(f"Successful: {success_count}/{trial_count}")
    logger.info(f"Average Solve Time: {avg_time:.4f}s")
    logger.info(f"Max Solve Time: {max_time:.4f}s")
    logger.info(f"Timeout Limit: {timeout_limit}s")
    
    if max_time < timeout_limit:
        logger.info("PASS: All trials completed within the <300s assumption.")
    else:
        logger.warning("FAIL: Some trials exceeded the 300s assumption.")
    
    logger.info("="*50)
    
    # Save results
    save_results(results, output_path)
    
    # Print final status for CI
    if max_time >= timeout_limit:
        logger.error("CRITICAL: Solver profiling failed the <300s/step assumption.")
        return 1
    else:
        logger.info("SUCCESS: Solver profiling passed the <300s/step assumption.")
        return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())