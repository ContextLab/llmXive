"""
Simulation Loop Orchestrator for US3.

Orchestrates the generation of synthetic data, application of scaling methods,
execution of statistical tests, and aggregation of results into a persistent CSV.

This module implements the core simulation loop required for Task T027.
"""
import os
import sys
import time
import logging
import csv
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import asdict
import numpy as np
import pandas as pd

# Project root path
PROJECT_ROOT = Path(__file__).parent.parent.parent
RESULTS_DIR = PROJECT_ROOT / "results"
LOGS_DIR = PROJECT_ROOT / "logs"

# Ensure directories exist
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Import project modules
from simulation.config import SimulationConfig, get_default_config
from simulation.logger import setup_logger
from simulation.generator import generate_synthetic_data
from preprocessing.scaling import standardize_data, min_max_scale, robust_scale
from analysis.tests import (
    ScalingMethod,
    TestResult,
    run_scaled_t_test,
    run_scaled_anova,
    run_scaled_chi_squared,
    run_pipeline
)

logger = setup_logger("orchestrator")


def get_scaling_functions() -> Dict[str, callable]:
    """
    Returns a dictionary of available scaling functions.
    """
    return {
        "standardize": standardize_data,
        "min_max": min_max_scale,
        "robust": robust_scale
    }


def save_test_result(result: TestResult, csv_path: Path):
    """
    Appends a single TestResult to the CSV file.
    Creates the file with headers if it does not exist.
    """
    file_exists = csv_path.exists()
    with open(csv_path, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            # Write header based on TestResult dataclass fields
            header = list(asdict(result).keys())
            writer.writerow(header)
        
        # Write data
        row = list(asdict(result).values())
        writer.writerow(row)


def run_simulation_loop(
    config: Optional[SimulationConfig] = None,
    output_csv: Optional[str] = None,
    time_limit_seconds: int = 300,
    start_iteration: int = 0
) -> Dict[str, Any]:
    """
    Runs the simulation loop for a specified number of iterations or time limit.
    
    Args:
        config: Simulation configuration. If None, uses default.
        output_csv: Path to the output CSV file. Defaults to results/simulation_results.csv.
        time_limit_seconds: Maximum time to run in seconds.
        start_iteration: Starting iteration number (for resuming).
        
    Returns:
        Dictionary containing run statistics (iterations_run, time_elapsed, etc.)
    """
    if config is None:
        config = get_default_config()
    
    if output_csv is None:
        output_csv = str(RESULTS_DIR / "simulation_results.csv")
    
    csv_path = Path(output_csv)
    
    logger.info(f"Starting simulation loop with config: {config}")
    logger.info(f"Output CSV: {csv_path}")
    logger.info(f"Time limit: {time_limit_seconds}s")
    
    scaling_funcs = get_scaling_functions()
    scaling_names = list(scaling_funcs.keys())
    
    iterations_run = 0
    start_time = time.time()
    last_checkpoint = start_time
    
    # Define the number of iterations to attempt per batch
    # We use a large number but break on time limit
    max_iterations = 10000 
    
    for i in range(start_iteration, start_iteration + max_iterations):
        # Check time limit
        current_time = time.time()
        elapsed = current_time - start_time
        
        if elapsed >= time_limit_seconds:
            logger.info(f"Time limit ({time_limit_seconds}s) reached. Stopping loop.")
            break
        
        # Checkpoint every 10 seconds to report progress
        if current_time - last_checkpoint >= 10:
            logger.info(f"Iteration {i}: Completed {i - start_iteration} iterations in {elapsed:.1f}s")
            last_checkpoint = current_time
        
        try:
            # 1. Generate Synthetic Data
            # Generate data for null hypothesis (mean_diff = 0)
            # We vary the distribution type based on config or cycle through them
            dist_type = config.distribution_types[i % len(config.distribution_types)]
            
            data_null = generate_synthetic_data(
                n_samples=config.n_samples,
                mean_diff=0.0,
                std_dev=1.0,
                skewness=0.0,
                distribution_type=dist_type,
                seed=config.seed + i
            )
            
            # Generate data for alternative hypothesis (mean_diff = 1.0)
            data_alt = generate_synthetic_data(
                n_samples=config.n_samples,
                mean_diff=1.0,
                std_dev=1.0,
                skewness=0.0,
                distribution_type=dist_type,
                seed=config.seed + i + 1000
            )
            
            # 2. Apply Scaling and Run Tests
            # We run tests on both Null and Alternative data to check Type I error and Power
            
            results_batch = []
            
            for scale_name, scale_func in scaling_funcs.items():
                # Process Null Hypothesis Data (for Type I Error)
                try:
                    scaled_null = scale_func(data_null)
                    # Run t-test on scaled null data
                    res_null = run_scaled_t_test(scaled_null[0], scaled_null[1], scale_name, "t-test")
                    results_batch.append(res_null)
                    
                    # Run ANOVA on scaled null data (if applicable, though t-test is primary)
                    # For simplicity in this loop, we focus on t-test for continuous data
                except Exception as e:
                    logger.warning(f"Error processing Null data with {scale_name}: {e}")
                    continue
                
                # Process Alternative Hypothesis Data (for Power)
                try:
                    scaled_alt = scale_func(data_alt)
                    res_alt = run_scaled_t_test(scaled_alt[0], scaled_alt[1], scale_name, "t-test")
                    # Mark this result as coming from alternative hypothesis
                    # We can store this in the metadata or a separate column if needed
                    # For now, we append to results
                    results_batch.append(res_alt)
                except Exception as e:
                    logger.warning(f"Error processing Alt data with {scale_name}: {e}")
                    continue
            
            # 3. Save Results
            for res in results_batch:
                save_test_result(res, csv_path)
            
            iterations_run += 1
            
        except Exception as e:
            logger.error(f"Iteration {i} failed: {e}")
            continue
    
    total_time = time.time() - start_time
    
    summary = {
        "iterations_run": iterations_run,
        "time_elapsed_seconds": total_time,
        "output_csv": str(csv_path),
        "config_used": asdict(config),
        "status": "completed" if (time.time() - start_time) < time_limit_seconds else "time_limit_reached"
    }
    
    logger.info(f"Simulation loop finished. Iterations: {iterations_run}, Time: {total_time:.1f}s")
    
    return summary


def main():
    """
    Entry point for the simulation orchestrator.
    """
    logger.info("Running Simulation Orchestrator (T027)")
    
    config = get_default_config()
    # Override for a quick run if needed, but keep it realistic
    config.n_iterations = 100 
    config.seed = 42
    
    summary = run_simulation_loop(
        config=config,
        time_limit_seconds=120, # Run for 2 minutes
        start_iteration=0
    )
    
    # Save summary to JSON
    summary_path = RESULTS_DIR / "simulation_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Summary saved to {summary_path}")
    print(f"Simulation complete. Results saved to {summary['output_csv']}")
    print(f"Summary: {summary['iterations_run']} iterations in {summary['time_elapsed_seconds']:.2f}s")


if __name__ == "__main__":
    main()
