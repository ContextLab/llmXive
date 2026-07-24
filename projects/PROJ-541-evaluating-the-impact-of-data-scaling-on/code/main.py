from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import sys
import time
from datetime import datetime
from multiprocessing import Pool, cpu_count, set_start_method
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from simulation.config import CONFIG_MATRIX, SimulationConfig, dataclass_to_dict
from simulation.generator import generate_synthetic_data
from simulation.logger import setup_logger, inject_batch_context
from simulation.persistence import save_seed_config_entry
from preprocessing.scaling import standardize_data, min_max_scale, robust_scale
from analysis.tests import run_scaled_t_test, run_scaled_anova, run_scaled_chi_squared
from simulation.schema import validate_seed_config, save_seed_config

# Ensure multiprocessing starts correctly (fork on Linux/Mac, spawn on Windows)
try:
    set_start_method('spawn', force=True)
except RuntimeError:
    pass

logger = setup_logger("main")

def ensure_directories() -> None:
    """Ensure all required directories exist."""
    dirs = [
        "data/raw", "data/scaled", "data/scaled/standardized",
        "data/scaled/minmax", "data/scaled/robust", "data/config",
        "data/synthetic", "results/figures", "logs"
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
    logger.info("Directories ensured.")

def get_scaling_function(method: str):
    """Return the scaling function based on the method name."""
    if method == "standardize":
        return standardize_data
    elif method == "minmax":
        return min_max_scale
    elif method == "robust":
        return robust_scale
    else:
        raise ValueError(f"Unknown scaling method: {method}")

def get_test_function(test_type: str):
    """Return the test function based on the test type name."""
    if test_type == "t_test":
        return run_scaled_t_test
    elif test_type == "anova":
        return run_scaled_anova
    elif test_type == "chi_squared":
        return run_scaled_chi_squared
    else:
        raise ValueError(f"Unknown test type: {test_type}")

def save_checkpoint(
    completed_iterations: int,
    partial_results_df: pd.DataFrame,
    time_remaining: float
) -> None:
    """Save partial results to a checkpoint file."""
    checkpoint_path = "results/partial_checkpoint.csv"
    if not partial_results_df.empty:
        partial_results_df.to_csv(checkpoint_path, index=False)
        logger.info(f"Checkpoint saved at iteration {completed_iterations}.")
    else:
        logger.warning("No results to save in checkpoint.")

def run_single_iteration(
    config: SimulationConfig,
    scaling_method: str,
    test_type: str,
    iteration_id: int,
    seed: int
) -> Dict[str, Any]:
    """Run a single simulation iteration."""
    try:
        # Generate synthetic data
        data, ground_truth_label = generate_synthetic_data(config, n=1000, seed=seed)
        
        # Apply scaling
        scale_func = get_scaling_function(scaling_method)
        scaled_data = scale_func(data)
        
        # Run test
        test_func = get_test_function(test_type)
        result = test_func(scaled_data)
        
        return {
            "iteration_id": iteration_id,
            "config_id": config.config_id,
            "scaling_method": scaling_method,
            "test_type": test_type,
            "p_value": result.p_value,
            "statistic": result.statistic,
            "ground_truth": ground_truth_label,
            "scaling_params": str(scale_func.__name__), # Simplified for CSV
            "seed": seed
        }
    except Exception as e:
        logger.error(f"Iteration {iteration_id} failed: {e}")
        return {
            "iteration_id": iteration_id,
            "config_id": config.config_id,
            "scaling_method": scaling_method,
            "test_type": test_type,
            "p_value": None,
            "statistic": None,
            "ground_truth": None,
            "scaling_params": None,
            "seed": seed
        }

def write_simulation_results(results: List[Dict[str, Any]], filepath: str) -> None:
    """Write simulation results to a CSV file."""
    if not results:
        logger.warning("No results to write.")
        return
    
    df = pd.DataFrame(results)
    df.to_csv(filepath, index=False)
    logger.info(f"Results written to {filepath}")

def _worker(args: Tuple) -> Dict[str, Any]:
    """Wrapper for multiprocessing worker."""
    config, scaling_method, test_type, iteration_id, seed = args
    return run_single_iteration(config, scaling_method, test_type, iteration_id, seed)

def run_simulation_loop(
    configs: List[SimulationConfig],
    target_iterations: int,
    scaling_methods: List[str],
    test_types: List[str],
    max_time_seconds: int = 21600
) -> pd.DataFrame:
    """Run the simulation loop with multiprocessing parallelization."""
    ensure_directories()
    start_time = time.time()
    all_results = []
    
    # Prepare tasks
    tasks = []
    iteration_counter = 0
    
    for config in configs:
        for scale_method in scaling_methods:
            for test_type in test_types:
                for _ in range(target_iterations):
                    seed = np.random.randint(0, 2**31)
                    tasks.append((config, scale_method, test_type, iteration_counter, seed))
                    iteration_counter += 1
    
    logger.info(f"Total tasks prepared: {len(tasks)}")
    
    # Use multiprocessing pool
    num_workers = min(cpu_count(), 8) # Cap workers to avoid oversubscription
    logger.info(f"Starting multiprocessing pool with {num_workers} workers.")
    
    with Pool(processes=num_workers) as pool:
        # Process tasks in chunks to manage memory and allow checkpointing
        chunk_size = max(1, len(tasks) // (num_workers * 4))
        for i in range(0, len(tasks), chunk_size):
            chunk = tasks[i : i + chunk_size]
            
            # Check time limit
            elapsed = time.time() - start_time
            if elapsed > max_time_seconds:
                logger.warning(f"Time limit reached at {elapsed:.1f}s. Stopping.")
                break
            
            # Execute chunk in parallel
            chunk_results = pool.map(_worker, chunk)
            all_results.extend(chunk_results)
            
            # Checkpoint every chunk
            if len(all_results) % 100 == 0:
                save_checkpoint(len(all_results), pd.DataFrame(all_results), max_time_seconds - elapsed)
    
    # Write final results
    output_path = "results/simulation_results.csv"
    write_simulation_results(all_results, output_path)
    
    logger.info(f"Simulation loop completed. Total iterations: {len(all_results)}")
    return pd.DataFrame(all_results)

def run_simulation_mode(args: argparse.Namespace) -> int:
    """Run the simulation mode."""
    configs = CONFIG_MATRIX
    scaling_methods = ["standardize", "minmax", "robust"]
    test_types = ["t_test", "anova", "chi_squared"]
    
    iterations = args.iterations if hasattr(args, 'iterations') and args.iterations else 100
    logger.info(f"Running simulation with {iterations} iterations per config.")
    
    df = run_simulation_loop(configs, iterations, scaling_methods, test_types)
    
    if df.empty:
        return 99
    
    return 0

def run_real_world_mode(args: argparse.Namespace) -> int:
    """Run the real-world data mode."""
    # Placeholder for real-world logic
    logger.info("Real-world mode not fully implemented in this snippet.")
    return 0

def run_analyze_mode(args: argparse.Namespace) -> int:
    """Run the analysis mode."""
    # Placeholder for analysis logic
    logger.info("Analysis mode not fully implemented in this snippet.")
    return 0

def run_visualize_mode(args: argparse.Namespace) -> int:
    """Run the visualization mode."""
    # Placeholder for visualization logic
    logger.info("Visualization mode not fully implemented in this snippet.")
    return 0

def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Simulation Pipeline")
    subparsers = parser.add_subparsers(dest="mode", required=True)
    
    # Simulation subcommand
    sim_parser = subparsers.add_parser("simulation", help="Run simulation")
    sim_parser.add_argument("--iterations", type=int, default=100, help="Number of iterations per config")
    
    # Real-world subcommand
    real_parser = subparsers.add_parser("real_world", help="Run real-world analysis")
    
    # Analyze subcommand
    analyze_parser = subparsers.add_parser("analyze", help="Run analysis")
    
    # Visualize subcommand
    viz_parser = subparsers.add_parser("visualize", help="Run visualization")
    
    args = parser.parse_args()
    
    if args.mode == "simulation":
        return run_simulation_mode(args)
    elif args.mode == "real_world":
        return run_real_world_mode(args)
    elif args.mode == "analyze":
        return run_analyze_mode(args)
    elif args.mode == "visualize":
        return run_visualize_mode(args)
    else:
        parser.print_help()
        return 1

if __name__ == "__main__":
    sys.exit(main())