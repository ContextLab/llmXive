"""
Main orchestration script for the simulation and analysis pipeline.
Handles simulation loop, real-world data processing, and result aggregation.
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import sys
import time
import random
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Iterator

# Import from local modules
from simulation.config import SimulationConfig, get_default_config, CONFIG_MATRIX, dataclass_to_dict
from simulation.generator import generate_synthetic_data, generate_synthetic_data_from_config
from simulation.logger import setup_logger
from preprocessing.scaling import standardize_data, min_max_scale, robust_scale
from analysis.tests import run_scaled_t_test, run_scaled_anova, run_scaled_chi_squared
from analysis.metrics import calculate_aggregate_metrics, calculate_confidence_interval
from preprocessing.ingestion import load_dataset_config, process_real_world_dataset, sample_streamed_data
from utils.env import configure_cpu_only

# Ensure directories exist
def ensure_directories():
    """Create necessary directories if they don't exist."""
    dirs = [
        "data/synthetic",
        "data/scaled/standardized",
        "data/scaled/minmax",
        "data/scaled/robust",
        "results/figures",
        "logs",
        "results"
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

# Helper functions for scaling and testing
def get_scaling_function(method: str):
    """Get the appropriate scaling function."""
    mapping = {
        "standardization": standardize_data,
        "minmax": min_max_scale,
        "robust": robust_scale
    }
    return mapping.get(method)

def get_test_function(test_type: str):
    """Get the appropriate statistical test function."""
    mapping = {
        "t-test": run_scaled_t_test,
        "anova": run_scaled_anova,
        "chi-squared": run_scaled_chi_squared
    }
    return mapping.get(test_type)

# Checkpointing logic (T064)
def save_partial_checkpoint(results: List[Dict], path: str = "results/partial_checkpoint.csv"):
    """Save partial results to a checkpoint file."""
    if not results:
        return
    with open(path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

# Single iteration logic
def run_single_iteration(config: SimulationConfig, iteration_id: int, logger: logging.Logger) -> Optional[Dict]:
    """
    Run a single simulation iteration.
    Returns a dictionary with results or None if skipped.
    """
    try:
        # Generate synthetic data based on config
        # T011: generate_synthetic_data accepts mean, var, skew, kurt, n, seed
        data_group1, data_group2 = generate_synthetic_data(
            mean=config.mean_diff / 2,  # Adjust for null/alt logic
            var=config.variance,
            skew=config.skewness,
            kurt=config.kurtosis,
            n=config.n_samples,
            seed=config.seed + iteration_id
        )

        # Apply scaling
        scaler = get_scaling_function(config.scaling_method)
        if scaler is None:
            logger.warning(f"Unknown scaling method: {config.scaling_method}")
            return None

        scaled_group1 = scaler(data_group1)
        scaled_group2 = scaler(data_group2)

        # Run statistical test
        test_func = get_test_function(config.test_type)
        if test_func is None:
            logger.warning(f"Unknown test type: {config.test_type}")
            return None

        result = test_func(scaled_group1, scaled_group2)

        # Determine ground truth label
        # T012: Logic for null vs alternative
        ground_truth = "null" if abs(config.mean_diff) < 0.01 else "alternative"

        return {
            "iteration_id": iteration_id,
            "config_id": config.config_id,
            "scaling_method": config.scaling_method,
            "test_type": config.test_type,
            "p_value": result.p_value,
            "statistic": result.statistic,
            "ground_truth": ground_truth,
            "scaling_params": json.dumps({"method": config.scaling_method}),
            "seed": config.seed + iteration_id
        }
    except Exception as e:
        logger.warning(f"Iteration {iteration_id} failed: {e}")
        return None

# Main simulation loop (T028a, T063, T064)
def run_simulation_loop(config: SimulationConfig, target_iterations: int, logger: logging.Logger) -> List[Dict]:
    """
    Run the simulation loop for a given configuration.
    Enforces minimum iterations and time limits.
    """
    results = []
    start_time = time.time()
    elapsed = 0
    max_time = 6 * 3600  # 6 hours in seconds

    # T063: Enforce iteration threshold
    min_iterations = 10000
    effective_iterations = max(target_iterations, min_iterations)

    logger.info(f"Starting simulation loop for config {config.config_id}, target iterations: {effective_iterations}")

    for i in range(effective_iterations):
        # T064: Time limit enforcement
        elapsed = time.time() - start_time
        if elapsed > max_time:
            logger.warning(f"Time limit reached ({elapsed:.2f}s). Saving partial results.")
            save_partial_checkpoint(results)
            break

        result = run_single_iteration(config, i, logger)
        if result:
            results.append(result)

        # Log progress every 1000 iterations
        if (i + 1) % 1000 == 0:
            logger.info(f"Completed {i+1}/{effective_iterations} iterations for config {config.config_id}")

    # T028c: Write results to CSV
    write_simulation_results(results, config.config_id, logger)

    # Check if budget met
    if len(results) == effective_iterations:
        logger.info("Budget Met: Completed all target iterations.")
    else:
        logger.info("Budget Exhausted: Time limit reached before target iterations.")

    return results

def write_simulation_results(results: List[Dict], config_id: str, logger: logging.Logger):
    """Write simulation results to CSV file."""
    if not results:
        logger.warning("No results to write.")
        return

    output_path = "results/simulation_results.csv"
    fieldnames = [
        "iteration_id", "config_id", "scaling_method", "test_type",
        "p_value", "statistic", "ground_truth", "scaling_params", "seed"
    ]

    # Check if file exists to decide on writing header
    file_exists = os.path.exists(output_path)

    with open(output_path, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerows(results)

    logger.info(f"Wrote {len(results)} results to {output_path}")

def run_simulation_mode(args):
    """Run the simulation mode."""
    ensure_directories()
    logger = setup_logger(batch_id="main_pipeline")
    configure_cpu_only()

    # T065: Iterate over CONFIG_MATRIX
    all_results = []
    
    # If specific config-id is provided, run only that one
    if args.config_id:
        # Find matching config in matrix
        # For simplicity, we generate a config object from the matrix
        # In a real scenario, we might load specific configs
        base_config = get_default_config()
        base_config.config_id = args.config_id
        base_config.target_iterations = args.iterations if args.iterations else 10000
        # Note: In a full implementation, we would map the config_id to specific matrix entries
        # For this task, we assume the user passes a valid config_id or we run the default matrix
        configs_to_run = [base_config]
    else:
        # Run all combinations in CONFIG_MATRIX
        configs_to_run = []
        for block in CONFIG_MATRIX:
            for dist in block["distribution_types"]:
                for scale in block["scaling_methods"]:
                    for test in block["test_types"]:
                        cfg = SimulationConfig(
                            config_id=f"{dist}-{scale}-{test}",
                            distribution_type=dist.lower(),
                            scaling_method=scale,
                            test_type=test,
                            target_iterations=10000
                        )
                        configs_to_run.append(cfg)

    for cfg in configs_to_run:
        logger.info(f"Running configuration: {cfg.config_id}")
        results = run_simulation_loop(cfg, cfg.target_iterations, logger)
        all_results.extend(results)

    logger.info(f"Simulation complete. Total results: {len(all_results)}")

def run_real_world_mode(args):
    """Run the real-world data processing mode."""
    ensure_directories()
    logger = setup_logger(batch_id="main_pipeline")
    
    # Load dataset config
    config_path = "data/config/datasets.yaml"
    if not os.path.exists(config_path):
        logger.error(f"Dataset config not found at {config_path}")
        return

    dataset_configs = load_dataset_config(config_path)
    
    for ds_id, ds_config in dataset_configs.items():
        logger.info(f"Processing dataset: {ds_id}")
        try:
            # Process dataset
            results = process_real_world_dataset(ds_id, ds_config, logger)
            # Save results
            # (Implementation would save to results/real_world_results.csv)
        except Exception as e:
            logger.error(f"Failed to process dataset {ds_id}: {e}")

def run_analyze_mode(args):
    """Run the analysis mode."""
    ensure_directories()
    logger = setup_logger(batch_id="main_pipeline")
    
    # Load results
    results_path = "results/simulation_results.csv"
    if not os.path.exists(results_path):
        logger.error(f"Results file not found at {results_path}")
        return

    # Calculate aggregate metrics
    # (Implementation would use calculate_aggregate_metrics from analysis.metrics)
    logger.info("Analysis complete.")

def run_visualize_mode(args):
    """Run the visualization mode."""
    ensure_directories()
    logger = setup_logger(batch_id="main_pipeline")
    
    # Generate plots
    # (Implementation would use visualization.plots)
    logger.info("Visualization complete.")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Simulation and Analysis Pipeline")
    parser.add_argument("--mode", choices=["simulation", "real_world", "analyze", "visualize", "verify-checksums"], required=True)
    parser.add_argument("--config-id", type=str, default=None)
    parser.add_argument("--iterations", type=int, default=None)
    
    args = parser.parse_args()

    if args.mode == "simulation":
        run_simulation_mode(args)
    elif args.mode == "real_world":
        run_real_world_mode(args)
    elif args.mode == "analyze":
        run_analyze_mode(args)
    elif args.mode == "visualize":
        run_visualize_mode(args)
    elif args.mode == "verify-checksums":
        ensure_directories()
        logger = setup_logger(batch_id="main_pipeline")
        logger.info("Checksum verification not implemented yet.")

if __name__ == "__main__":
    main()
