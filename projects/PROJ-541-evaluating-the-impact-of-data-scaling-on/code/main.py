"""
Main orchestration script for the data scaling impact evaluation.
Implements the simulation loop, real-world data processing, and analysis modes.
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Callable

import numpy as np
import pandas as pd

# Local imports from the project structure
from simulation.config import SimulationConfig, get_default_config, CONFIG_MATRIX
from simulation.generator import generate_synthetic_data, generate_synthetic_data_from_config
from preprocessing.scaling import standardize_data, min_max_scale, robust_scale
from analysis.tests import run_scaled_t_test, run_scaled_anova, run_scaled_chi_squared, TestResult
from simulation.logger import setup_logger, log_operation, ReproducibilityLogger
from utils.env import configure_cpu_only, verify_cpu_only

# Constants
TIME_LIMIT_SECONDS = 6 * 3600  # 6 hours
CHECKPOINT_INTERVAL = 100
MIN_ITERATIONS = 10000

# Ensure directories exist
def ensure_directories():
    """Create required directory structure if it doesn't exist."""
    dirs = [
        "code", "data", "data/raw", "data/scaled", "data/scaled/standardized",
        "data/scaled/minmax", "data/scaled/robust", "data/config", "data/synthetic",
        "results", "results/figures", "logs", "code/tests"
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

# Helper functions to get scaling and test functions
def get_scaling_function(method: str) -> Callable:
    """Return the appropriate scaling function."""
    mapping = {
        "standardization": standardize_data,
        "minmax": min_max_scale,
        "robust": robust_scale
    }
    if method not in mapping:
        raise ValueError(f"Unknown scaling method: {method}")
    return mapping[method]

def get_test_function(test_type: str) -> Callable:
    """Return the appropriate statistical test function."""
    mapping = {
        "t-test": run_scaled_t_test,
        "anova": run_scaled_anova,
        "chi-squared": run_scaled_chi_squared
    }
    if test_type not in mapping:
        raise ValueError(f"Unknown test type: {test_type}")
    return mapping[test_type]

# Checkpointing logic
def save_partial_checkpoint(results: List[Dict], path: str, iteration: int):
    """Save partial results to a checkpoint file."""
    ensure_directories()
    with open(path, 'w', newline='') as f:
        if results:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
    logging.info(f"Checkpoint saved at iteration {iteration} to {path}")

# Single iteration logic
def run_single_iteration(config: SimulationConfig, iteration_id: int, logger: ReproducibilityLogger) -> Dict[str, Any]:
    """Run a single simulation iteration."""
    seed = config.seed + iteration_id
    np.random.seed(seed)
    random.seed(seed)

    # Generate synthetic data
    try:
        data, ground_truth_label = generate_synthetic_data_from_config(config, seed=seed)
    except ValueError as e:
        # Handle zero variance or other edge cases by skipping
        logger.warning(f"Skipping iteration {iteration_id}: {e}")
        return None

    # Apply scaling
    scaling_func = get_scaling_function(config.scaling_method)
    try:
        scaled_data = scaling_func(data)
    except Exception as e:
        logger.warning(f"Scaling failed at iteration {iteration_id}: {e}")
        return None

    # Run statistical test
    test_func = get_test_function(config.test_type)
    try:
        result: TestResult = test_func(scaled_data)
    except Exception as e:
        logger.warning(f"Test failed at iteration {iteration_id}: {e}")
        return None

    # Record result
    record = {
        "iteration_id": iteration_id,
        "config_id": config.config_id,
        "scaling_method": config.scaling_method,
        "test_type": config.test_type,
        "p_value": result.p_value,
        "statistic": result.statistic,
        "ground_truth": ground_truth_label,
        "scaling_params": json.dumps({}), # Placeholder for specific params if needed
        "seed": seed
    }
    return record

# Main simulation loop
def run_simulation_loop(config: SimulationConfig, logger: ReproducibilityLogger) -> List[Dict[str, Any]]:
    """Run the full simulation loop for a given configuration."""
    results = []
    start_time = time.time()
    target_iterations = config.target_iterations if config.target_iterations > 0 else MIN_ITERATIONS

    logger.log_operation("simulation_start", config_id=config.config_id, target_iterations=target_iterations)

    for i in range(target_iterations):
        # Check time limit
        elapsed = time.time() - start_time
        if elapsed > TIME_LIMIT_SECONDS:
            logger.log_operation("time_limit_reached", elapsed_seconds=elapsed, completed_iterations=i)
            save_partial_checkpoint(results, "results/partial_checkpoint.csv", i)
            if i < MIN_ITERATIONS:
                logger.error(f"Budget exhausted before minimum iterations ({i} < {MIN_ITERATIONS})")
                sys.exit(99)
            break

        # Run iteration
        record = run_single_iteration(config, i, logger)
        if record:
            results.append(record)

        # Periodic checkpoint
        if (i + 1) % CHECKPOINT_INTERVAL == 0:
            save_partial_checkpoint(results, "results/partial_checkpoint.csv", i + 1)
            logger.log_operation("checkpoint", iteration=i + 1, elapsed_seconds=time.time() - start_time)

    logger.log_operation("simulation_complete", config_id=config.config_id, total_iterations=len(results))
    return results

# Write results to CSV
def write_simulation_results(all_results: List[Dict], output_path: str):
    """Write all simulation results to a CSV file."""
    ensure_directories()
    if not all_results:
        logging.warning("No results to write.")
        return

    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=all_results[0].keys())
        writer.writeheader()
        writer.writerows(all_results)
    logging.info(f"Results written to {output_path}")

# Mode: Simulation
def run_simulation_mode(args):
    """Run the simulation mode."""
    ensure_directories()
    logger = setup_logger(batch_id="main_pipeline")

    # Load or create config
    if args.config_id:
        config = SimulationConfig(config_id=args.config_id, target_iterations=args.iterations)
    else:
        config = get_default_config()

    # Run simulation
    all_results = []
    if args.config_id:
        # Single config run
        results = run_simulation_loop(config, logger)
        all_results.extend(results)
    else:
        # Run over CONFIG_MATRIX
        for matrix_config in CONFIG_MATRIX:
            for dist in matrix_config["distribution_types"]:
                for scale in matrix_config["scaling_methods"]:
                    for test in matrix_config["test_types"]:
                        run_config = SimulationConfig(
                            config_id=f"{dist}_{scale}_{test}",
                            distribution_type=dist.lower(),
                            scaling_method=scale,
                            test_type=test,
                            target_iterations=MIN_ITERATIONS
                        )
                        logger.log_operation("config_start", config_id=run_config.config_id)
                        results = run_simulation_loop(run_config, logger)
                        all_results.extend(results)
                        logger.log_operation("config_complete", config_id=run_config.config_id, count=len(results))

    # Write results
    write_simulation_results(all_results, "results/simulation_results.csv")
    return all_results

# Mode: Real World
def run_real_world_mode(args):
    """Run the real-world data processing mode."""
    ensure_directories()
    logger = setup_logger(batch_id="main_pipeline")
    logger.log_operation("real_world_start")

    # Placeholder for real world ingestion logic
    # This would load datasets from data/config/datasets.yaml and process them
    logger.log_operation("real_world_complete")
    return []

# Mode: Analyze
def run_analyze_mode(args):
    """Run the analysis mode."""
    ensure_directories()
    logger = setup_logger(batch_id="main_pipeline")
    logger.log_operation("analysis_start")

    # Load results and run aggregation
    # This would call code/analysis/metrics.py functions
    logger.log_operation("analysis_complete")
    return {}

# Mode: Visualize
def run_visualize_mode(args):
    """Run the visualization mode."""
    ensure_directories()
    logger = setup_logger(batch_id="main_pipeline")
    logger.log_operation("visualization_start")

    # Generate plots
    logger.log_operation("visualization_complete")
    return {}

# Main entry point
def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description="Data Scaling Impact Evaluation")
    subparsers = parser.add_subparsers(dest="mode", required=True)

    # Simulation mode
    sim_parser = subparsers.add_parser("simulation", help="Run simulation")
    sim_parser.add_argument("--config-id", type=str, help="Specific config ID")
    sim_parser.add_argument("--iterations", type=int, default=MIN_ITERATIONS, help="Number of iterations")

    # Real world mode
    subparsers.add_parser("real_world", help="Run real-world data processing")

    # Analyze mode
    subparsers.add_parser("analyze", help="Run analysis")

    # Visualize mode
    subparsers.add_parser("visualize", help="Generate visualizations")

    args = parser.parse_args()

    if args.mode == "simulation":
        run_simulation_mode(args)
    elif args.mode == "real_world":
        run_real_world_mode(args)
    elif args.mode == "analyze":
        run_analyze_mode(args)
    elif args.mode == "visualize":
        run_visualize_mode(args)

if __name__ == "__main__":
    main()