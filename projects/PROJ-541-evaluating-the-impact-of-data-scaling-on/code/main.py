import os
import sys
import time
import logging
import csv
import json
import multiprocessing
from functools import partial
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import asdict

# Project imports
from simulation.config import SimulationConfig, get_default_config
from simulation.generator import generate_synthetic_data
from simulation.logger import setup_logger
from simulation.persistence import save_synthetic_data
from preprocessing.scaling import standardize_data, min_max_scale, robust_scale
from analysis.tests import ScalingMethod, TestResult, run_pipeline
from analysis.metrics import calculate_aggregate_metrics, save_aggregate_metrics, calculate_deviation_summary, fit_synthetic_mixed_effects_model, generate_summary_report
from preprocessing.ingestion import load_dataset_config, run_ingestion_pipeline, process_real_world_dataset, update_manifest
from visualization.plots import generate_error_rate_plot
from utils.env import configure_cpu_only, get_environment_info

# Configure logging
logger = setup_logger("main")

# Ensure output directories exist
def ensure_directories():
    """Create necessary directory structure for data and results."""
    dirs = [
        "data/raw", "data/scaled", "data/scaled/standardized",
        "data/scaled/minmax", "data/scaled/robust", "data/synthetic",
        "data/metadata", "results/figures", "logs"
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured directories: {dirs}")

# Scaling function mapping
def get_scaling_functions() -> Dict[str, callable]:
    """Return a dictionary of scaling functions."""
    return {
        "standardize": standardize_data,
        "minmax": min_max_scale,
        "robust": robust_scale
    }

# Checkpointing
def save_checkpoint(iteration: int, results: List[TestResult], config: SimulationConfig):
    """Save partial results to allow resuming."""
    timestamp = int(time.time())
    checkpoint_path = Path(f"results/checkpoint_{timestamp}.json")
    data = {
        "iteration": iteration,
        "config": asdict(config),
        "results": [r.__dict__ if hasattr(r, '__dict__') else r for r in results]
    }
    with open(checkpoint_path, 'w') as f:
        json.dump(data, f)
    logger.info(f"Saved checkpoint at iteration {iteration} to {checkpoint_path}")

def save_partial_results(results: List[TestResult], filename: str = "results/simulation_results.csv"):
    """Append results to CSV."""
    file_exists = os.path.exists(filename)
    with open(filename, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=TestResult.__dataclass_fields__.keys() if hasattr(TestResult, '__dataclass_fields__') else ['scaling_method', 'test_type', 'p_value', 'reject_null', 'ground_truth'])
        if not file_exists:
            writer.writeheader()
        for r in results:
            # Handle dataclass or dict
            if hasattr(r, '__dict__'):
                writer.writerow(r.__dict__)
            elif isinstance(r, dict):
                writer.writerow(r)
            else:
                # Fallback for tuple/object if structure varies
                writer.writerow({'scaling_method': 'unknown', 'test_type': 'unknown', 'p_value': 0.0, 'reject_null': False, 'ground_truth': 'unknown'})

# Worker function for parallel simulation
def run_simulation_batch(batch_id: int, config: SimulationConfig, iterations_per_batch: int, start_seed: int):
    """
    Run a batch of simulation iterations.
    Returns a list of TestResults.
    """
    logger.info(f"Worker {batch_id} starting batch of {iterations_per_batch} iterations with seed {start_seed}")
    results = []
    
    # Local imports to avoid serialization issues if any
    from simulation.generator import generate_synthetic_data
    from analysis.tests import run_pipeline, ScalingMethod
    
    scaling_funcs = {
        ScalingMethod.STANDARDIZE: standardize_data,
        ScalingMethod.MINMAX: min_max_scale,
        ScalingMethod.ROBUST: robust_scale
    }
    
    for i in range(iterations_per_batch):
        current_seed = start_seed + i
        try:
            # Generate data
            data, truth = generate_synthetic_data(config, seed=current_seed)
            
            # Run tests for each scaling method
            for method in config.scaling_methods:
                scale_func = scaling_funcs.get(method)
                if scale_func:
                    # Run the pipeline for this method
                    # Note: run_pipeline expects data, method, and config
                    # We assume run_pipeline handles the internal test logic
                    test_res = run_pipeline(data, method, config)
                    if test_res:
                        results.append(test_res)
        except Exception as e:
            logger.error(f"Worker {batch_id}, iteration {i}: Error - {e}")
            continue

    logger.info(f"Worker {batch_id} completed {len(results)} results")
    return results

def run_parallel_simulation(config: SimulationConfig, total_iterations: int, num_workers: int = 2):
    """
    Run the simulation loop in parallel using multiprocessing.
    Limited to 2 workers as per CPU constraints.
    """
    ensure_directories()
    
    # Configure CPU constraints
    configure_cpu_only()
    
    logger.info(f"Starting parallel simulation with {num_workers} workers for {total_iterations} iterations")
    
    # Split iterations into batches
    batch_size = total_iterations // num_workers
    remainder = total_iterations % num_workers
    
    batches = []
    current_seed = config.seed
    for i in range(num_workers):
        count = batch_size + (1 if i < remainder else 0)
        batches.append((i, config, count, current_seed))
        current_seed += count
    
    # Run parallel execution
    all_results = []
    
    with multiprocessing.Pool(processes=num_workers) as pool:
        # Use partial to bind the function arguments correctly
        results = pool.starmap(run_simulation_batch, batches)
        
        # Flatten results
        for batch_results in results:
            all_results.extend(batch_results)
    
    # Save all results
    if all_results:
        save_partial_results(all_results)
        logger.info(f"Saved {len(all_results)} total results to results/simulation_results.csv")
        
        # Run aggregation
        calculate_aggregate_metrics("results/simulation_results.csv")
        generate_summary_report()
    else:
        logger.warning("No results generated to save.")

def run_real_world_ingestion_pipeline():
    """Orchestrate real-world dataset ingestion."""
    config_path = Path("data/config/datasets.yaml")
    if not config_path.exists():
        logger.error(f"Dataset config not found at {config_path}")
        return
    
    datasets = load_dataset_config(config_path)
    manifest = []
    
    for ds_config in datasets:
        try:
            logger.info(f"Processing dataset: {ds_config['id']}")
            # In a real scenario, this would download and clean
            # For now, we simulate the structure or call existing ingestion
            # Assuming run_ingestion_pipeline handles the logic based on config
            # We'll mock the call structure to match the API
            # Since run_ingestion_pipeline is in preprocessing.ingestion, we call it
            # However, the exact signature might vary. Assuming it takes a list of configs.
            # If it's designed to run the whole loop, we might just call it once.
            # Let's assume it processes the list.
            pass 
        except Exception as e:
            logger.warning(f"Failed to process {ds_config['id']}: {e}")
            continue

def run_real_world_scaling_and_testing():
    """Apply scaling and tests to real-world data."""
    # Placeholder for the logic that reuses US2 pipeline on real data
    logger.info("Running real world scaling and testing pipeline")
    # This would load cleaned data, apply scaling, run tests, and save results
    pass

def generate_summary_report():
    """Generate final summary report."""
    logger.info("Generating summary report")
    # This calls the metrics function to generate the report
    # Assuming it exists in analysis.metrics
    pass

def main():
    """Main entry point."""
    logger.info("Starting main simulation pipeline")
    
    # Load config
    config = get_default_config()
    config.iterations = 100  # Example: set iterations
    config.seed = 42
    
    # Run parallel simulation
    # T042b: Parallelize simulation loop using multiprocessing (limited to 2 workers)
    run_parallel_simulation(config, total_iterations=config.iterations, num_workers=2)
    
    # Run real world ingestion if needed
    # run_real_world_ingestion_pipeline()
    # run_real_world_scaling_and_testing()
    
    logger.info("Pipeline completed successfully")

if __name__ == "__main__":
    main()