"""
Main entry point for the llmXive automated science pipeline.
Orchestrates simulation, real‑world data processing, analysis, and visualization.
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
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

from simulation.config import CONFIG_MATRIX, SimulationConfig
from simulation.generator import generate_synthetic_data
from simulation.logger import setup_logger, inject_batch_context, save_seed_config
from simulation.persistence import save_synthetic_data
from preprocessing.scaling import standardize_data, min_max_scale, robust_scale
from analysis.tests import (
    run_scaled_t_test,
    run_scaled_anova,
    run_scaled_chi_squared,
    ScalingMethod,
    TestResult,
)
from simulation.logger import log_operation

# Constants for iteration logic (T028d)
TARGET_ITERATIONS = 10000
MAX_RUNTIME_SECONDS = 5.5 * 3600  # 5.5 hours

logger = setup_logger("main")

def get_scaling_function(method: str):
    """Return the scaling function corresponding to the method name."""
    mapping = {
        "standardize": standardize_data,
        "minmax": min_max_scale,
        "robust": robust_scale,
    }
    if method not in mapping:
        raise ValueError(f"Unknown scaling method: {method}")
    return mapping[method]

def get_test_function(test_type: str):
    """Return the test function corresponding to the test type."""
    mapping = {
        "t_test": run_scaled_t_test,
        "anova": run_scaled_anova,
        "chi_squared": run_scaled_chi_squared,
    }
    if test_type not in mapping:
        raise ValueError(f"Unknown test type: {test_type}")
    return mapping[test_type]

def save_checkpoint(results: List[Dict], iteration_count: int, checkpoint_path: str = "results/partial_checkpoint.csv"):
    """Save partial results to a CSV file."""
    logger.info(f"Saving checkpoint at iteration {iteration_count}")
    Path(checkpoint_path).parent.mkdir(parents=True, exist_ok=True)
    with open(checkpoint_path, "w", newline="") as f:
        if results:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
        else:
            f.write("")  # Empty file if no results yet

def write_simulation_results(results: List[Dict], output_path: str):
    """
    Aggregate results and write to a CSV file.
    Schema: iteration_id, config_id, scaling_method, test_type, p_value, statistic, ground_truth, scaling_params, seed
    """
    logger.info(f"Writing {len(results)} results to {output_path}")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    if not results:
        logger.warning("No results to write.")
        # Create empty file with headers to ensure schema exists
        with open(output_path, "w", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "iteration_id",
                    "config_id",
                    "scaling_method",
                    "test_type",
                    "p_value",
                    "statistic",
                    "ground_truth",
                    "scaling_params",
                    "seed",
                ],
            )
            writer.writeheader()
        return

    required_fields = [
        "iteration_id",
        "config_id",
        "scaling_method",
        "test_type",
        "p_value",
        "statistic",
        "ground_truth",
        "scaling_params",
        "seed",
    ]

    cleaned_results = []
    for r in results:
        cleaned = {}
        for field in required_fields:
            val = r.get(field)
            if val is None:
                val = ""
            cleaned[field] = val
        cleaned_results.append(cleaned)

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=required_fields)
        writer.writeheader()
        writer.writerows(cleaned_results)

def run_single_iteration(
    config: SimulationConfig,
    iteration_id: int,
    scaling_method: str,
    test_type: str,
    seed: int,
) -> Dict[str, Any] | None:
    """Run a single simulation iteration."""
    try:
        # Generate data
        data, ground_truth = generate_synthetic_data(config, seed=seed)

        # Apply scaling
        scale_func = get_scaling_function(scaling_method)
        try:
            scaled_data, scaling_params = scale_func(data)
        except ValueError as e:
            logger.warning(f"Scaling failed for {scaling_method}: {e}. Skipping.")
            return None  # Skip this iteration

        # Run test
        test_func = get_test_function(test_type)
        try:
            result: TestResult = test_func(scaled_data)
        except ValueError as e:
            logger.warning(f"Test failed for {test_type}: {e}. Skipping.")
            return None  # Skip this iteration

        return {
            "iteration_id": iteration_id,
            "config_id": f"config_{config.distribution_type}_{seed}",
            "scaling_method": scaling_method,
            "test_type": test_type,
            "p_value": float(result.p_value),
            "statistic": float(result.statistic),
            "ground_truth": ground_truth,
            "scaling_params": json.dumps(scaling_params),
            "seed": seed,
        }
    except Exception as e:
        logger.error(f"Iteration {iteration_id} failed: {e}", exc_info=True)
        return None

def enforce_iteration_logic(current_iterations: int, start_time: float) -> int:
    """
    Enforce minimum iteration threshold.
    Returns target iterations if successful, or raises an error if time limit hit before target.
    """
    elapsed = time.time() - start_time
    if elapsed > MAX_RUNTIME_SECONDS:
        if current_iterations < TARGET_ITERATIONS:
            msg = (
                f"FIDELITY VIOLATION: Insufficient iterations ({current_iterations} < {TARGET_ITERATIONS}) "
                f"due to time limit ({elapsed:.1f}s > {MAX_RUNTIME_SECONDS}s)"
            )
            logger.error(msg)
            raise RuntimeError(msg)
    return TARGET_ITERATIONS

def run_simulation_loop(
    target_iterations: int = TARGET_ITERATIONS,
    config_matrix: Optional[List[SimulationConfig]] = None,
    scaling_methods: Optional[List[str]] = None,
    test_types: Optional[List[str]] = None,
    output_path: str = "results/simulation_results.csv",
    checkpoint_path: str = "results/partial_checkpoint.csv",
    checkpoint_interval: int = 1000,
) -> pd.DataFrame:
    """
    Orchestrate the simulation loop over all configurations, scaling methods, and test types.
    Aggregates results and writes to CSV.
    """
    logger.info(f"Starting simulation loop for {target_iterations} iterations")

    if config_matrix is None:
        config_matrix = CONFIG_MATRIX
    if scaling_methods is None:
        scaling_methods = ["standardize", "minmax", "robust"]
    if test_types is None:
        test_types = ["t_test", "anova", "chi_squared"]

    all_results: List[Dict[str, Any]] = []
    iteration_counter = 0
    start_time = time.time()

    total_runs_needed = target_iterations
    current_runs = 0
    seed = 42

    while current_runs < total_runs_needed:
        if current_runs > 0 and current_runs % 100 == 0:
            enforce_iteration_logic(current_runs, start_time)
            if current_runs % checkpoint_interval == 0:
                save_checkpoint(all_results, current_runs, checkpoint_path)

        for config in config_matrix:
            for scale in scaling_methods:
                for test in test_types:
                    if current_runs >= total_runs_needed:
                        break

                    result = run_single_iteration(config, current_runs, scale, test, seed)
                    if result is not None:
                        all_results.append(result)
                        current_runs += 1

                    seed += 1
                if current_runs >= total_runs_needed:
                    break
            if current_runs >= total_runs_needed:
                break

    enforce_iteration_logic(current_runs, start_time)
    write_simulation_results(all_results, output_path)

    logger.info(f"Simulation loop completed. {len(all_results)} results written to {output_path}")
    return pd.DataFrame(all_results)

def run_real_world_mode():
    """Placeholder for real-world data processing."""
    logger.info("Running real-world mode")
    # Implementation would go here (T038)

def run_analyze_mode():
    """Placeholder for analysis."""
    logger.info("Running analysis mode")
    # Implementation would go here (T029)

def run_visualize_mode():
    """Placeholder for visualization."""
    logger.info("Running visualization mode")
    # Implementation would go here (T030)

def main():
    """
    CLI entry point.

    The original implementation used sub‑parsers with positional sub‑commands.
    Quickstart scripts (and the CI run‑book) invoke the script with a ``--mode`` flag.
    To maintain backward compatibility we accept both styles.
    """
    parser = argparse.ArgumentParser(description="llmXive Automated Science Pipeline")

    # New ``--mode`` flag – mirrors the sub‑command names.
    parser.add_argument(
        "--mode",
        choices=["simulation", "real_world", "analyze", "visualize"],
        help="Mode to run (alternative to sub‑command syntax)",
    )

    subparsers = parser.add_subparsers(dest="subcommand", help="Mode to run (sub‑command syntax)")

    # Simulation mode
    sim_parser = subparsers.add_parser("simulation", help="Run simulation loop")
    sim_parser.add_argument(
        "--iterations",
        type=int,
        default=TARGET_ITERATIONS,
        help="Number of iterations",
    )
    sim_parser.add_argument(
        "--output",
        type=str,
        default="results/simulation_results.csv",
        help="Output CSV path",
    )

    # Real world mode
    subparsers.add_parser("real_world", help="Run real‑world data pipeline")

    # Analyze mode
    subparsers.add_parser("analyze", help="Run analysis pipeline")

    # Visualize mode
    subparsers.add_parser("visualize", help="Run visualization pipeline")

    args = parser.parse_args()

    # Resolve which mode the user requested.
    mode = args.mode or args.subcommand

    if mode == "simulation":
        run_simulation_loop(target_iterations=args.iterations, output_path=args.output)
    elif mode == "real_world":
        run_real_world_mode()
    elif mode == "analyze":
        run_analyze_mode()
    elif mode == "visualize":
        run_visualize_mode()
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
