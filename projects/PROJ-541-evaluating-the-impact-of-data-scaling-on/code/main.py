"""
Main entry point for the simulation pipeline.
Orchestrates simulation, real-world data processing, analysis, and visualization.
"""
import os
import sys
import time
import logging
import argparse
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from simulation.config import SimulationConfig, get_default_config
from simulation.generator import generate_synthetic_data_from_config
from simulation.persistence import save_synthetic_data
from simulation.logger import setup_logger
from preprocessing.scaling import standardize_data, min_max_scale, robust_scale
from analysis.tests import run_scaled_t_test, run_scaled_anova, run_scaled_chi_squared
from analysis.metrics import calculate_aggregate_metrics, calculate_confidence_interval
from visualization.plots import generate_error_rate_plot
from preprocessing.ingestion import process_real_world_dataset, load_dataset_config

# Constants
RESULTS_FILE = Path("results/simulation_results.csv")
CHECKPOINT_FILE = Path("results/partial_checkpoint.csv")
REAL_WORLD_RESULTS_FILE = Path("results/real_world_results.csv")
AGGREGATE_METRICS_FILE = Path("results/aggregate_metrics.csv")
MIN_ITERATIONS = 10000

logger = setup_logger(batch_id="main_pipeline")


def ensure_directories():
    """Ensure all required directories exist."""
    dirs = [
        "code", "data", "results", "logs",
        "data/raw", "data/scaled", "data/scaled/standardized",
        "data/scaled/minmax", "data/scaled/robust", "data/synthetic",
        "results/figures"
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
    logger.log("ensure_directories", status="completed", directories=dirs)


def enforce_iteration_threshold(iterations: int) -> int:
    """Enforce minimum iteration threshold for statistical validity."""
    if iterations < MIN_ITERATIONS:
        logger.log("enforce_iteration_threshold", 
                 warning=f"Iterations {iterations} below minimum {MIN_ITERATIONS}, adjusting.")
        return MIN_ITERATIONS
    return iterations


def run_single_iteration(config: SimulationConfig, scaling_method: str, 
                       test_type: str, iteration_id: int) -> Dict[str, Any]:
    """
    Run a single simulation iteration.
    This function is designed to be picklable for multiprocessing.
    """
    import numpy as np
    from simulation.generator import generate_synthetic_data_from_config
    from preprocessing.scaling import standardize_data, min_max_scale, robust_scale
    from analysis.tests import run_scaled_t_test, run_scaled_anova, run_scaled_chi_squared
    import json

    # Set seed for reproducibility
    seed = config.seed + iteration_id
    np.random.seed(seed)

    # Generate synthetic data
    data_group1, data_group2 = generate_synthetic_data_from_config(config, seed=seed)
    
    # Apply scaling
    scaling_functions = {
        "standardize": standardize_data,
        "minmax": min_max_scale,
        "robust": robust_scale
    }
    
    scale_func = scaling_functions.get(scaling_method)
    if not scale_func:
        raise ValueError(f"Unknown scaling method: {scaling_method}")

    scaled_group1 = scale_func(data_group1)
    scaled_group2 = scale_func(data_group2)

    # Run statistical test
    test_functions = {
        "t_test": run_scaled_t_test,
        "anova": run_scaled_anova,
        "chi_squared": run_scaled_chi_squared
    }
    
    test_func = test_functions.get(test_type)
    if not test_func:
        raise ValueError(f"Unknown test type: {test_type}")

    result = test_func(scaled_group1, scaled_group2)

    # Determine ground truth
    ground_truth = "null" if config.mean_diff == 0 else "alternative"

    return {
        "iteration_id": iteration_id,
        "config_id": config.config_id,
        "scaling_method": scaling_method,
        "test_type": test_type,
        "p_value": result.p_value,
        "statistic": result.statistic,
        "ground_truth": ground_truth,
        "scaling_params": json.dumps({"method": scaling_method}),
        "seed": seed
    }


def run_simulation_loop(config: SimulationConfig, scaling_methods: List[str], 
                       test_types: List[str], iterations: int) -> pd.DataFrame:
    """
    Run the full simulation loop with multiprocessing parallelization.
    """
    iterations = enforce_iteration_threshold(iterations)
    logger.log("run_simulation_loop", 
             config_id=config.config_id, 
             iterations=iterations,
             scaling_methods=scaling_methods,
             test_types=test_types)

    all_results = []
    total_combinations = len(scaling_methods) * len(test_types)
    
    # Prepare tasks for parallel execution
    tasks = []
    task_id = 0
    for scaling_method in scaling_methods:
        for test_type in test_types:
            for i in range(iterations):
                tasks.append((config, scaling_method, test_type, task_id))
                task_id += 1

    logger.log("simulation_tasks_prepared", total_tasks=len(tasks))

    # Use multiprocessing for parallel execution
    num_workers = max(1, multiprocessing.cpu_count() - 1)
    logger.log("multiprocessing_start", workers=num_workers)

    try:
        with ProcessPoolExecutor(max_workers=num_workers) as executor:
            futures = {
                executor.submit(run_single_iteration, *task): task 
                for task in tasks
            }
            
            completed = 0
            for future in as_completed(futures):
                try:
                    result = future.result()
                    all_results.append(result)
                    completed += 1
                    
                    # Checkpoint every 10% of iterations
                    if completed % (iterations // 10) == 0 and completed > 0:
                        partial_df = pd.DataFrame(all_results)
                        partial_df.to_csv(CHECKPOINT_FILE, index=False)
                        logger.log("checkpoint_saved", completed_iterations=completed)
                        
                except Exception as e:
                    logger.log("simulation_error", error=str(e))
                    continue
                    
    except Exception as e:
        logger.log("multiprocessing_failed", error=str(e), fallback="sequential")
        # Fallback to sequential if multiprocessing fails
        for scaling_method in scaling_methods:
            for test_type in test_types:
                for i in range(iterations):
                    result = run_single_iteration(config, scaling_method, test_type, i)
                    all_results.append(result)

    results_df = pd.DataFrame(all_results)
    results_df.to_csv(RESULTS_FILE, index=False)
    logger.log("simulation_loop_completed", total_results=len(results_df))
    
    return results_df


def run_simulation_mode(config_id: Optional[str] = None, 
                      iterations: Optional[int] = None):
    """Run simulation mode with optional config override."""
    ensure_directories()
    
    if config_id:
        config = SimulationConfig(config_id=config_id)
    else:
        config = get_default_config()
        
    if iterations:
        config.iterations = iterations
        
    scaling_methods = ["standardize", "minmax", "robust"]
    test_types = ["t_test", "anova", "chi_squared"]
    
    results = run_simulation_loop(config, scaling_methods, test_types, config.iterations)
    return results


def run_real_world_mode():
    """Run real-world data processing and testing."""
    ensure_directories()
    
    # Load dataset configurations
    config_path = Path("data/config/datasets.yaml")
    if not config_path.exists():
        logger.log("real_world_error", error="No dataset config found")
        return pd.DataFrame()
        
    dataset_configs = load_dataset_config(config_path)
    
    all_results = []
    for dataset_info in dataset_configs:
        try:
            logger.log("processing_dataset", dataset_id=dataset_info.get("id"))
            result_df = process_real_world_dataset(dataset_info)
            if result_df is not None:
                all_results.append(result_df)
        except Exception as e:
            logger.log("dataset_processing_error", 
                     dataset_id=dataset_info.get("id"), 
                     error=str(e))
            continue
    
    if all_results:
        combined_df = pd.concat(all_results, ignore_index=True)
        combined_df.to_csv(REAL_WORLD_RESULTS_FILE, index=False)
        logger.log("real_world_completed", total_datasets=len(all_results))
        return combined_df
    
    return pd.DataFrame()


def run_analyze_mode():
    """Run analysis mode to aggregate metrics."""
    if not RESULTS_FILE.exists():
        logger.log("analyze_error", error="No simulation results found")
        return None
        
    results_df = pd.read_csv(RESULTS_FILE)
    metrics = calculate_aggregate_metrics(results_df)
    
    if metrics is not None:
        metrics.to_csv(AGGREGATE_METRICS_FILE, index=False)
        logger.log("analysis_completed", metrics_file=str(AGGREGATE_METRICS_FILE))
        return metrics
    
    return None


def run_visualize_mode():
    """Run visualization mode to generate plots."""
    if not AGGREGATE_METRICS_FILE.exists():
        logger.log("visualize_error", error="No aggregate metrics found")
        return None
        
    metrics_df = pd.read_csv(AGGREGATE_METRICS_FILE)
    fig_path = generate_error_rate_plot(metrics_df)
    
    if fig_path:
        logger.log("visualization_completed", figure_path=str(fig_path))
        return fig_path
    
    return None


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(description="Simulation Pipeline")
    parser.add_argument("--mode", choices=["simulation", "real_world", "analyze", "visualize"],
                      required=True, help="Mode to run")
    parser.add_argument("--config-id", type=str, help="Configuration ID")
    parser.add_argument("--iterations", type=int, help="Number of iterations")
    
    args = parser.parse_args()
    
    if args.mode == "simulation":
        run_simulation_mode(args.config_id, args.iterations)
    elif args.mode == "real_world":
        run_real_world_mode()
    elif args.mode == "analyze":
        run_analyze_mode()
    elif args.mode == "visualize":
        run_visualize_mode()


if __name__ == "__main__":
    main()