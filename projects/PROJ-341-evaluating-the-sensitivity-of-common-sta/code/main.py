import argparse
import gc
import json
import os
import sys
import time
import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

# Import simulation components
from code.simulation.data_generator import (
    generate_normal_data,
    generate_multinomial_data,
    generate_contingency_table_data,
    generate_two_sample_data,
    generate_anova_data
)
from code.simulation.test_runner import (
    run_t_test,
    run_anova,
    run_chi_squared,
    run_simulation_condition,
    aggregate_results
)
from code.simulation.output_writer import (
    ensure_output_directory,
    write_p_values_raw,
    load_p_values_raw_safe
)
from code.simulation.logging_config import setup_logging, get_logger, log_simulation_params
from code.simulation import get_rng

# Import analysis components
from code.analysis.aggregator import calculate_error_rates, save_aggregated_results
from code.analysis.threshold_finder import calculate_confidence_intervals, save_thresholds
from code.analysis.validator import (
    download_breast_cancer_dataset,
    download_wine_dataset,
    download_adult_dataset,
    preprocess_dataset_for_validation
)
from code.analysis.real_data_runner import run_validation_on_datasets, save_p_values_to_csv
from code.analysis.bootstrapper import run_bootstrapped_validation, save_power_results
from code.utils.checksum_utils import (
    ensure_metadata_file_exists,
    save_simulation_metadata,
    register_dataset_checksum
)

# Constants
MEMORY_LIMIT_GB = 7.0
MEMORY_LIMIT_MB = MEMORY_LIMIT_GB * 1024
BATCH_SIZE = 1000  # Number of iterations to process before checking memory and writing to disk

def get_memory_usage_mb() -> float:
    """Get current memory usage in MB using resource module (Unix) or fallback."""
    try:
        import resource
        usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        # On Linux, ru_maxrss is in KB. On macOS, it's in KB too but sometimes reported differently.
        # Standardizing to KB -> MB
        if sys.platform == 'darwin':
            # macOS ru_maxrss is in bytes
            return usage / (1024 * 1024)
        else:
            # Linux ru_maxrss is in KB
            return usage / 1024.0
    except ImportError:
        # Fallback: estimate based on numpy arrays or just return 0
        # In a real scenario, we might use psutil if installed
        return 0.0

def check_memory_limit(current_mb: float) -> bool:
    """Check if current memory usage exceeds the limit."""
    return current_mb > MEMORY_LIMIT_MB

def force_gc():
    """Force garbage collection to reclaim memory."""
    gc.collect()
    # Clear numpy caches if necessary
    np.lib.stride_tricks._array_function_dispatch = None

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Simulation of statistical tests sensitivity")
    parser.add_argument("--mode", choices=["simulation", "validation", "full"], default="simulation",
                        help="Execution mode: simulation, validation, or full pipeline")
    parser.add_argument("--test", type=str, default="t-test",
                        help="Test type: t-test, anova, chi-squared")
    parser.add_argument("--min-n", type=int, default=5, help="Minimum sample size")
    parser.add_argument("--max-n", type=int, default=500, help="Maximum sample size")
    parser.add_argument("--step-n", type=int, default=5, help="Step size for sample sizes")
    parser.add_argument("--iterations", type=int, default=10000, help="Number of iterations per condition")
    parser.add_argument("--alpha", type=float, default=0.05, help="Significance level")
    parser.add_argument("--effect-size", type=str, default="0.5", help="Effect size (comma-separated)")
    parser.add_argument("--hypotheses", type=str, default="two-sided", help="Hypothesis type (comma-separated)")
    parser.add_argument("--chunk-size", type=int, default=BATCH_SIZE, help="Iterations per batch for memory management")
    return parser.parse_args()

def validate_args(args: argparse.Namespace) -> None:
    if args.min_n < 2:
        raise ValueError("Minimum sample size must be at least 2")
    if args.max_n < args.min_n:
        raise ValueError("Maximum sample size must be greater than or equal to minimum")
    if args.iterations < 100:
        raise ValueError("Iterations must be at least 100 for meaningful results")

def generate_sample_sizes(args: argparse.Namespace) -> List[int]:
    return list(range(args.min_n, args.max_n + 1, args.step_n))

def parse_effect_sizes(effect_str: str) -> List[float]:
    return [float(x) for x in effect_str.split(",")]

def parse_hypotheses(hyp_str: str) -> List[str]:
    return [x.strip() for x in hyp_str.split(",")]

def generate_conditions(args: argparse.Namespace) -> List[Dict[str, Any]]:
    sample_sizes = generate_sample_sizes(args)
    effect_sizes = parse_effect_sizes(args.effect_size)
    hypotheses = parse_hypotheses(args.hypotheses)
    
    conditions = []
    for n in sample_sizes:
        for effect in effect_sizes:
            for hyp in hypotheses:
                conditions.append({
                    "sample_size": n,
                    "effect_size": effect,
                    "hypothesis": hyp,
                    "test_type": args.test,
                    "alpha": args.alpha,
                    "iterations": args.iterations
                })
    return conditions

def run_simulation_grid_chunked(args: argparse.Namespace, conditions: List[Dict[str, Any]]) -> None:
    logger = get_logger()
    logger.info(f"Starting simulation grid with {len(conditions)} conditions")
    
    all_results = []
    current_batch = []
    
    # Ensure output directory exists
    ensure_output_directory("data/simulation")
    
    for i, condition in enumerate(conditions):
        logger.info(f"Processing condition {i+1}/{len(conditions)}: n={condition['sample_size']}, effect={condition['effect_size']}")
        
        # Run simulation condition
        results = run_simulation_condition(condition)
        current_batch.append(results)
        
        # Memory management
        if len(current_batch) >= args.chunk_size:
            # Write batch to disk
            write_p_values_raw(current_batch, "data/simulation/p_values_raw.csv", append=True)
            current_batch = []
            
            # Check memory and force GC
            mem_usage = get_memory_usage_mb()
            if check_memory_limit(mem_usage):
                logger.warning(f"Memory usage high ({mem_usage:.2f} MB). Forcing GC.")
                force_gc()
            
            # Small sleep to let OS reclaim memory
            time.sleep(0.1)
        
        # Progress logging
        if (i + 1) % 10 == 0:
            mem_usage = get_memory_usage_mb()
            logger.info(f"Progress: {i+1}/{len(conditions)}, Memory: {mem_usage:.2f} MB")
    
    # Write remaining batch
    if current_batch:
        write_p_values_raw(current_batch, "data/simulation/p_values_raw.csv", append=True)
    
    logger.info("Simulation grid completed. Aggregating results...")
    
    # Aggregate results
    aggregated = calculate_error_rates("data/simulation/p_values_raw.csv")
    save_aggregated_results(aggregated, "data/simulation/error_rates_summary.csv")
    
    logger.info("Aggregation completed. Results saved to data/simulation/error_rates_summary.csv")

def run_validation_mode(args: argparse.Namespace) -> None:
    logger = get_logger()
    logger.info("Starting validation mode...")
    
    # Download datasets
    logger.info("Downloading UCI datasets...")
    datasets = {
        "breast_cancer": download_breast_cancer_dataset(),
        "wine": download_wine_dataset(),
        "adult": download_adult_dataset()
    }
    
    # Compute and register checksums
    for name, data in datasets.items():
        if data is not None:
            checksum = register_dataset_checksum(data, f"data/raw/{name}.csv")
            logger.info(f"Registered checksum for {name}: {checksum}")
    
    # Run validation
    logger.info("Running validation on real datasets...")
    p_values = run_validation_on_datasets(datasets, args.test, args.alpha)
    save_p_values_to_csv(p_values, "data/simulation/real_data_pvalues.csv")
    
    # Bootstrapped power estimation
    logger.info("Running bootstrapped power estimation...")
    power_results = run_bootstrapped_validation(p_values, "data/simulation/p_values_raw.csv")
    save_power_results(power_results, "data/simulation/real_data_power.json")
    
    # Generate validation report
    from code.analysis.report_generator import generate_report
    generate_report()
    
    logger.info("Validation mode completed.")

def run_full_pipeline(args: argparse.Namespace) -> None:
    logger = get_logger()
    logger.info("Starting full pipeline...")
    
    # Run simulation
    conditions = generate_conditions(args)
    run_simulation_grid_chunked(args, conditions)
    
    # Run validation
    run_validation_mode(args)
    
    # Generate thresholds and plots
    logger.info("Generating thresholds and visualizations...")
    from code.analysis.threshold_finder import main as threshold_main
    threshold_main()
    
    from code.visualization.plotter import main as plotter_main
    plotter_main()
    
    logger.info("Full pipeline completed.")

def main():
    args = parse_args()
    validate_args(args)
    
    # Setup logging
    log_file = setup_logging()
    logger = get_logger()
    
    logger.info(f"Starting simulation with args: {args}")
    log_simulation_params(args)
    
    try:
        if args.mode == "simulation":
            conditions = generate_conditions(args)
            run_simulation_grid_chunked(args, conditions)
        elif args.mode == "validation":
            run_validation_mode(args)
        elif args.mode == "full":
            run_full_pipeline(args)
        else:
            logger.error(f"Unknown mode: {args.mode}")
            sys.exit(1)
        
        logger.info("Simulation completed successfully.")
    except Exception as e:
        logger.error(f"Simulation failed: {str(e)}")
        raise
    finally:
        # Force GC at the end
        force_gc()
        logger.info("Garbage collection completed.")

if __name__ == "__main__":
    main()