"""Main entry point for the simulation and analysis pipeline."""
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

import pandas as pd

from simulation.config import CONFIG_MATRIX, SimulationConfig
from simulation.generator import generate_synthetic_data
from simulation.logger import setup_logger, inject_batch_context
from simulation.persistence import save_synthetic_data
from preprocessing.scaling import standardize_data, min_max_scale, robust_scale
from analysis.tests import run_scaled_t_test, run_scaled_anova, run_scaled_chi_squared, ScalingMethod, TestResult

# Configure root logger
logging.basicConfig(level=logging.INFO)
logger = setup_logger("main")

# Constants
RESULTS_DIR = Path("results")
DATA_DIR = Path("data")
SIMULATIONS_DIR = RESULTS_DIR / "simulations"
FIGURES_DIR = RESULTS_DIR / "figures"

# Ensure directories exist
def ensure_directories() -> None:
    """Create necessary output directories."""
    RESULTS_DIR.mkdir(exist_ok=True)
    SIMULATIONS_DIR.mkdir(exist_ok=True)
    FIGURES_DIR.mkdir(exist_ok=True)
    DATA_DIR.mkdir(exist_ok=True)
    (DATA_DIR / "synthetic").mkdir(exist_ok=True)
    (DATA_DIR / "scaled" / "standardized").mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "scaled" / "minmax").mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "scaled" / "robust").mkdir(parents=True, exist_ok=True)

# Scaling function mapping
SCALING_FUNCTIONS: Dict[str, callable] = {
    "standardize": standardize_data,
    "minmax": min_max_scale,
    "robust": robust_scale,
}

def get_scaling_function(method: str) -> callable:
    """Get the scaling function by name."""
    if method not in SCALING_FUNCTIONS:
        raise ValueError(f"Unknown scaling method: {method}. Choose from {list(SCALING_FUNCTIONS.keys())}")
    return SCALING_FUNCTIONS[method]

# Test function mapping
TEST_FUNCTIONS: Dict[str, callable] = {
    "t_test": run_scaled_t_test,
    "anova": run_scaled_anova,
    "chi_squared": run_scaled_chi_squared,
}

def get_test_function(test_type: str) -> callable:
    """Get the test function by name."""
    if test_type not in TEST_FUNCTIONS:
        raise ValueError(f"Unknown test type: {test_type}. Choose from {list(TEST_FUNCTIONS.keys())}")
    return TEST_FUNCTIONS[test_type]

# Checkpointing
def save_checkpoint(
    completed_iterations: int,
    partial_results_df: pd.DataFrame,
    time_remaining: Optional[float] = None
) -> None:
    """Save the current state of the simulation to a checkpoint file."""
    checkpoint_path = RESULTS_DIR / "partial_checkpoint.csv"
    partial_results_df.to_csv(checkpoint_path, index=False)
    logger.info(f"Checkpoint saved at iteration {completed_iterations} to {checkpoint_path}")

# Core Simulation Logic
def run_single_iteration(
    iteration_id: int,
    config: SimulationConfig,
    scaling_method: str,
    test_type: str,
    seed: int
) -> Dict[str, Any]:
    """
    Run a single simulation iteration.
    
    1. Generate synthetic data based on config.
    2. Apply scaling.
    3. Run statistical test.
    4. Return results dictionary.
    """
    # Generate data
    data, ground_truth = generate_synthetic_data(config, n=1000, seed=seed)
    
    # Apply scaling
    scale_func = get_scaling_function(scaling_method)
    scaled_data = scale_func(data)
    
    # Run test
    test_func = get_test_function(test_type)
    result: TestResult = test_func(scaled_data)
    
    # Prepare scaling params for logging (simplified for now)
    scaling_params = json.dumps({"method": scaling_method})
    
    return {
        "iteration_id": iteration_id,
        "config_id": f"config_{config.distribution_type}_{seed}",
        "scaling_method": scaling_method,
        "test_type": test_type,
        "p_value": result.p_value,
        "statistic": result.statistic,
        "ground_truth": ground_truth,
        "scaling_params": scaling_params,
        "seed": seed,
    }

def write_simulation_results(results: List[Dict[str, Any]], output_path: str) -> None:
    """
    Aggregate simulation results and write to a CSV file.
    
    Args:
        results: List of result dictionaries.
        output_path: Path to the output CSV file.
    """
    if not results:
        logger.warning("No results to write.")
        # Create empty file with headers if needed, or just ensure file exists
        Path(output_path).touch()
        return

    # Define expected schema columns
    expected_columns = [
        "iteration_id", "config_id", "scaling_method", "test_type",
        "p_value", "statistic", "ground_truth", "scaling_params", "seed"
    ]
    
    # Validate and normalize results
    normalized_results = []
    for res in results:
        row = {}
        for col in expected_columns:
            row[col] = res.get(col, "")
        normalized_results.append(row)
    
    df = pd.DataFrame(normalized_results)
    df.to_csv(output_path, index=False)
    logger.info(f"Wrote {len(results)} results to {output_path}")

def run_simulation_loop(
    target_iterations: int,
    config_matrix: Optional[List[SimulationConfig]] = None,
    scaling_methods: Optional[List[str]] = None,
    test_types: Optional[List[str]] = None,
    output_path: Optional[str] = None
) -> pd.DataFrame:
    """
    Run the full simulation loop over configs, scaling methods, and test types.
    
    Args:
        target_iterations: Number of iterations per config.
        config_matrix: List of configurations. Defaults to CONFIG_MATRIX.
        scaling_methods: List of scaling methods. Defaults to ['standardize', 'minmax', 'robust'].
        test_types: List of test types. Defaults to ['t_test', 'anova', 'chi_squared'].
        output_path: Path to write results. Defaults to 'results/simulation_results.csv'.
        
    Returns:
        DataFrame containing all results.
    """
    ensure_directories()
    
    if config_matrix is None:
        config_matrix = CONFIG_MATRIX
    if scaling_methods is None:
        scaling_methods = ["standardize", "minmax", "robust"]
    if test_types is None:
        test_types = ["t_test", "anova", "chi_squared"]
    if output_path is None:
        output_path = str(RESULTS_DIR / "simulation_results.csv")
    
    all_results = []
    iteration_counter = 0
    start_time = time.time()
    
    for config in config_matrix:
        for scaling_method in scaling_methods:
            for test_type in test_types:
                for i in range(target_iterations):
                    # Check time limit (6 hours = 21600 seconds)
                    elapsed = time.time() - start_time
                    if elapsed > 21600:
                        logger.warning("Time limit approaching. Saving checkpoint and stopping.")
                        save_checkpoint(len(all_results), pd.DataFrame(all_results))
                        return pd.DataFrame(all_results)
                    
                    seed = int(time.time() * 1000) % (2**32) # Simple seed generation
                    try:
                        result = run_single_iteration(
                            iteration_id=iteration_counter,
                            config=config,
                            scaling_method=scaling_method,
                            test_type=test_type,
                            seed=seed
                        )
                        all_results.append(result)
                        
                        # Save checkpoint every 100 iterations
                        if (iteration_counter + 1) % 100 == 0:
                            save_checkpoint(len(all_results), pd.DataFrame(all_results))
                        
                    except Exception as e:
                        logger.error(f"Error in iteration {iteration_counter}: {e}", exc_info=True)
                        # Continue to next iteration
                    
                    iteration_counter += 1
    
    # Write final results
    write_simulation_results(all_results, output_path)
    logger.info(f"Simulation loop completed. Total iterations: {iteration_counter}")
    return pd.DataFrame(all_results)

# Mode runners
def run_simulation_mode(args: argparse.Namespace) -> None:
    """Run the simulation mode."""
    config_matrix = CONFIG_MATRIX
    if hasattr(args, 'config_id') and args.config_id:
        # Filter config matrix if specific config requested
        config_matrix = [c for c in CONFIG_MATRIX if args.config_id in f"config_{c.distribution_type}"]
        if not config_matrix:
            raise ValueError(f"No configuration found for ID: {args.config_id}")
    
    iterations = args.iterations if hasattr(args, 'iterations') and args.iterations else 100
    
    run_simulation_loop(
        target_iterations=iterations,
        config_matrix=config_matrix,
        scaling_methods=args.scaling if hasattr(args, 'scaling') else None,
        test_types=args.tests if hasattr(args, 'tests') else None
    )

def run_real_world_mode(args: argparse.Namespace) -> None:
    """Run the real-world data analysis mode."""
    logger.info("Running real-world data analysis mode...")
    # Placeholder for real-world logic (T038)
    logger.info("Real-world mode not fully implemented yet.")

def run_analyze_mode(args: argparse.Namespace) -> None:
    """Run the analysis mode."""
    logger.info("Running analysis mode...")
    # Placeholder for aggregation logic (T029)
    logger.info("Analysis mode not fully implemented yet.")

def run_visualize_mode(args: argparse.Namespace) -> None:
    """Run the visualization mode."""
    logger.info("Running visualization mode...")
    # Placeholder for plotting logic (T030)
    logger.info("Visualization mode not fully implemented yet.")

def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Simulation and Analysis Pipeline")
    subparsers = parser.add_subparsers(dest="mode", help="Available modes")
    
    # Simulation subparser
    sim_parser = subparsers.add_parser("simulation", help="Run simulation loop")
    sim_parser.add_argument("--config-id", type=str, help="Specific config ID to run")
    sim_parser.add_argument("--iterations", type=int, default=100, help="Number of iterations")
    sim_parser.add_argument("--scaling", type=str, nargs="+", help="Scaling methods to use")
    sim_parser.add_argument("--tests", type=str, nargs="+", help="Test types to run")
    
    # Real-world subparser
    real_parser = subparsers.add_parser("real_world", help="Run real-world data analysis")
    
    # Analyze subparser
    analyze_parser = subparsers.add_parser("analyze", help="Run analysis on results")
    
    # Visualize subparser
    viz_parser = subparsers.add_parser("visualize", help="Generate visualizations")
    
    args = parser.parse_args()
    
    if args.mode == "simulation":
        run_simulation_mode(args)
    elif args.mode == "real_world":
        run_real_world_mode(args)
    elif args.mode == "analyze":
        run_analyze_mode(args)
    elif args.mode == "visualize":
        run_visualize_mode(args)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
