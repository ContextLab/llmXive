from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import sys
import time
import random
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

# Local imports
from simulation.config import SimulationConfig, get_default_config
from simulation.generator import generate_synthetic_data_from_config
from preprocessing.scaling import standardize_data, min_max_scale, robust_scale
from analysis.tests import run_scaled_t_test, run_scaled_anova, run_scaled_chi_squared, TestResult, ScalingMethod
from simulation.logger import setup_logger
from preprocessing.ingestion import process_real_world_dataset, load_dataset_config, run_ingestion_pipeline
from analysis.metrics import calculate_aggregate_metrics, run_full_analysis_pipeline
from visualization.plots import generate_error_rate_plot

# Constants
TIME_LIMIT_SECONDS = 6 * 3600  # 6 hours
CHECKPOINT_INTERVAL = 1000     # Check time every 1000 iterations
PARTIAL_CHECKPOINT_PATH = "results/partial_checkpoint.csv"
RESULTS_PATH = "results/simulation_results.csv"

# Ensure directories exist
def ensure_directories():
    dirs = [
        "code", "data", "data/raw", "data/scaled", "data/scaled/standardized",
        "data/scaled/minmax", "data/scaled/robust", "data/config",
        "results", "results/figures", "logs", "data/synthetic"
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

# Helper to get scaling function
def get_scaling_function(method: str):
    if method == "standardization":
        return standardize_data
    elif method == "minmax":
        return min_max_scale
    elif method == "robust":
        return robust_scale
    else:
        raise ValueError(f"Unknown scaling method: {method}")

# Helper to get test function
def get_test_function(test_type: str):
    if test_type == "t-test":
        return run_scaled_t_test
    elif test_type == "anova":
        return run_scaled_anova
    elif test_type == "chi-squared":
        return run_scaled_chi_squared
    else:
        raise ValueError(f"Unknown test type: {test_type}")

# Run a single iteration
def run_single_iteration(iteration_id: int, config: SimulationConfig, seed: int, logger: logging.Logger) -> Dict[str, Any]:
    """
    Run one simulation iteration: generate data, scale, test, return result dict.
    """
    try:
        # Generate synthetic data
        data_dict = generate_synthetic_data_from_config(config, seed=seed)
        
        if data_dict is None:
            logger.warning(f"Iteration {iteration_id}: Skipped due to generation failure (e.g., zero variance)")
            return None

        # Extract data
        group_a = data_dict['group_a']
        group_b = data_dict['group_b']
        ground_truth = data_dict['ground_truth_label'] # 'null' or 'alternative'

        # Apply scaling
        scaler = get_scaling_function(config.scaling_method)
        scaled_a = scaler(group_a)
        scaled_b = scaler(group_b)

        # Run test
        test_func = get_test_function(config.test_type)
        result: TestResult = test_func(scaled_a, scaled_b)

        return {
            "iteration_id": iteration_id,
            "config_id": config.config_id,
            "scaling_method": config.scaling_method,
            "test_type": config.test_type,
            "p_value": result.p_value,
            "statistic": result.statistic,
            "ground_truth": ground_truth,
            "scaling_params": json.dumps(result.scaling_params),
            "seed": seed,
            "effect_size": result.effect_size
        }
    except Exception as e:
        logger.error(f"Iteration {iteration_id} failed: {str(e)}")
        return None

# Save partial checkpoint
def save_partial_checkpoint(results: List[Dict[str, Any]], logger: logging.Logger):
    """Save current results to partial checkpoint file."""
    if not results:
        return
    
    try:
        # Ensure results directory exists
        os.makedirs("results", exist_ok=True)
        
        fieldnames = [
            "iteration_id", "config_id", "scaling_method", "test_type", 
            "p_value", "statistic", "ground_truth", "scaling_params", "seed", "effect_size"
        ]
        
        with open(PARTIAL_CHECKPOINT_PATH, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        
        logger.info(f"Saved {len(results)} results to partial checkpoint: {PARTIAL_CHECKPOINT_PATH}")
    except Exception as e:
        logger.error(f"Failed to save partial checkpoint: {str(e)}")

# Run simulation loop with time limit enforcement
def run_simulation_loop(configs: List[SimulationConfig], target_iterations: int, logger: logging.Logger) -> List[Dict[str, Any]]:
    """
    Run simulation loop over all configs with time limit enforcement.
    Returns list of all results.
    """
    all_results = []
    start_time = time.time()
    total_iterations = 0
    
    logger.info(f"Starting simulation loop. Target iterations per config: {target_iterations}")
    logger.info(f"Time limit: {TIME_LIMIT_SECONDS} seconds ({TIME_LIMIT_SECONDS/3600} hours)")

    for config in configs:
        logger.info(f"Processing config: {config.config_id}")
        config_results = []
        iterations_completed = 0
        
        for i in range(target_iterations):
            # Check time limit
            elapsed = time.time() - start_time
            if elapsed > TIME_LIMIT_SECONDS:
                logger.warning(f"TIME LIMIT EXCEEDED after {iterations_completed} iterations for config {config.config_id}")
                logger.warning(f"Total elapsed time: {elapsed:.2f} seconds")
                logger.warning("Saving partial checkpoint and exiting...")
                
                # Save partial results before exit
                save_partial_checkpoint(all_results + config_results, logger)
                
                # Log budget status
                if iterations_completed >= target_iterations:
                    logger.info("Budget Met: Completed all target iterations before time limit.")
                else:
                    logger.info("Budget Exhausted: Time limit reached before completing target iterations.")
                
                # Write final partial results to main results file as well
                if all_results or config_results:
                    save_results_to_csv(all_results + config_results, logger)
                
                return all_results + config_results

            # Run iteration
            result = run_single_iteration(
                iteration_id=total_iterations,
                config=config,
                seed=random.randint(0, 2**31 - 1),
                logger=logger
            )
            
            if result:
                config_results.append(result)
                all_results.append(result)
            
            iterations_completed += 1
            total_iterations += 1

            # Periodic checkpoint
            if iterations_completed % CHECKPOINT_INTERVAL == 0:
                logger.info(f"Completed {iterations_completed} iterations for config {config.config_id}")
                save_partial_checkpoint(all_results, logger)

        logger.info(f"Completed {iterations_completed} iterations for config {config.config_id}")

    # Final checkpoint
    elapsed = time.time() - start_time
    logger.info(f"Simulation loop completed. Total time: {elapsed:.2f} seconds")
    logger.info(f"Total iterations: {total_iterations}")
    
    if total_iterations == len(configs) * target_iterations:
        logger.info("Budget Met: Completed all target iterations for all configs.")
    else:
        logger.info("Budget Exhausted: Time limit reached.")

    save_results_to_csv(all_results, logger)
    return all_results

def save_results_to_csv(results: List[Dict[str, Any]], logger: logging.Logger):
    """Save results to the main results CSV file."""
    if not results:
        logger.warning("No results to save.")
        return
    
    try:
        os.makedirs("results", exist_ok=True)
        fieldnames = [
            "iteration_id", "config_id", "scaling_method", "test_type", 
            "p_value", "statistic", "ground_truth", "scaling_params", "seed", "effect_size"
        ]
        
        with open(RESULTS_PATH, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        
        logger.info(f"Saved {len(results)} results to {RESULTS_PATH}")
    except Exception as e:
        logger.error(f"Failed to save results to CSV: {str(e)}")

def run_simulation_mode(args):
    """Run simulation mode."""
    ensure_directories()
    logger = setup_logger(batch_id="main_pipeline")
    
    # Load or create config
    if args.config_id:
        # Load specific config if available, otherwise create default
        config = SimulationConfig(
            config_id=args.config_id,
            distribution_type="normal",
            scaling_method="standardization",
            test_type="t-test",
            n_samples=100,
            mean_diff=0.0 if args.iterations is None or args.iterations == 0 else 1.0, # Simplified logic
            variance=1.0,
            skewness=0.0,
            kurtosis=3.0
        )
        configs = [config]
    else:
        # Use default config matrix logic (simplified for now)
        configs = [get_default_config()]
    
    target_iterations = args.iterations if args.iterations else 10000
    
    logger.info(f"Running simulation with {len(configs)} configs, {target_iterations} iterations each")
    
    results = run_simulation_loop(configs, target_iterations, logger)
    
    # Run aggregation if results exist
    if results:
        logger.info("Running aggregation on simulation results...")
        try:
            run_full_analysis_pipeline(None) # Triggers analysis from file
        except Exception as e:
            logger.error(f"Aggregation failed: {str(e)}")
    
    logger.info("Simulation mode completed.")

def run_real_world_mode(args):
    """Run real-world data mode."""
    ensure_directories()
    logger = setup_logger(batch_id="main_pipeline")
    
    logger.info("Starting real-world data ingestion and analysis...")
    
    try:
        # Run ingestion pipeline
        run_ingestion_pipeline(logger)
        
        # Process datasets
        process_real_world_dataset(logger)
        
        # Run analysis
        run_full_analysis_pipeline(logger)
        
        logger.info("Real-world mode completed.")
    except Exception as e:
        logger.error(f"Real-world mode failed: {str(e)}")
        raise

def run_analyze_mode(args):
    """Run analysis mode only."""
    ensure_directories()
    logger = setup_logger(batch_id="main_pipeline")
    
    logger.info("Running analysis on existing results...")
    
    try:
        run_full_analysis_pipeline(logger)
        logger.info("Analysis mode completed.")
    except Exception as e:
        logger.error(f"Analysis mode failed: {str(e)}")
        raise

def run_visualize_mode(args):
    """Run visualization mode."""
    ensure_directories()
    logger = setup_logger(batch_id="main_pipeline")
    
    logger.info("Generating visualizations...")
    
    try:
        # Generate error rate plot
        generate_error_rate_plot(logger)
        logger.info("Visualization mode completed.")
    except Exception as e:
        logger.error(f"Visualization mode failed: {str(e)}")
        raise

def main():
    parser = argparse.ArgumentParser(description="Main pipeline for data scaling impact evaluation")
    subparsers = parser.add_subparsers(dest="mode", help="Mode to run")
    
    # Simulation mode
    sim_parser = subparsers.add_parser("simulation", help="Run simulation")
    sim_parser.add_argument("--config-id", type=str, help="Specific config ID")
    sim_parser.add_argument("--iterations", type=int, help="Number of iterations per config")
    
    # Real-world mode
    real_parser = subparsers.add_parser("real_world", help="Run real-world data analysis")
    
    # Analyze mode
    analyze_parser = subparsers.add_parser("analyze", help="Run analysis only")
    
    # Visualize mode
    viz_parser = subparsers.add_parser("visualize", help="Generate visualizations")
    
    # Verify checksums (placeholder for completeness)
    verify_parser = subparsers.add_parser("verify-checksums", help="Verify data checksums")
    
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
        logger = setup_logger(batch_id="main_pipeline")
        logger.info("Checksum verification not fully implemented yet.")
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()