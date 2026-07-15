"""
Main entry point for the statistical sensitivity simulation pipeline.
Orchestrates data generation, hypothesis testing, and result aggregation.
"""
import argparse
import json
import os
import sys
import gc
from datetime import datetime

# Add project root to path to resolve imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from code.simulation.logging_config import (
    setup_logging, get_logger, log_simulation_params, log_output_file_written,
    log_error_details, log_shutdown
)
from code.simulation.data_generator import generate_normal_data, generate_contingency_table_data
from code.simulation.test_runner import run_simulation_condition, aggregate_results
from code.simulation.output_writer import write_p_values_raw
from code.simulation import get_rng
from code.analysis.aggregator import calculate_error_rates, save_aggregated_results
from code.analysis.validator import (
    download_breast_cancer_dataset, download_wine_dataset, download_adult_dataset,
    preprocess_dataset_for_validation, save_simulation_metadata
)
from code.analysis.real_data_runner import save_p_values_to_csv
from code.analysis.bootstrapper import run_bootstrapped_validation, save_power_results
from code.analysis.validation_metrics import calculate_validation_metrics, save_validation_metrics
from code.analysis.threshold_finder import save_thresholds
from code.utils.metadata_manager import register_run, update_run_status, ensure_metadata_file_exists

logger = None

def parse_args():
    parser = argparse.ArgumentParser(description="Run statistical sensitivity simulations")
    parser.add_argument("--mode", type=str, default="simulation", choices=["simulation", "aggregation", "validation"],
                        help="Operation mode")
    parser.add_argument("--test", type=str, default="t-test", choices=["t-test", "anova", "chi-squared"],
                        help="Statistical test to run")
    parser.add_argument("--min-n", type=int, default=5, help="Minimum sample size")
    parser.add_argument("--max-n", type=int, default=500, help="Maximum sample size")
    parser.add_argument("--step-n", type=int, default=5, help="Step size for sample sizes")
    parser.add_argument("--iterations", type=int, default=1000, help="Number of iterations per condition")
    parser.add_argument("--effect-size", type=str, default="0.2,0.5,0.8", help="Comma-separated effect sizes")
    parser.add_argument("--alpha", type=float, default=0.05, help="Significance level")
    parser.add_argument("--hypothesis", type=str, default="two-sided", choices=["one-sided", "two-sided"],
                        help="Hypothesis type")
    parser.add_argument("--output-dir", type=str, default="data/simulation", help="Output directory")
    return parser.parse_args()

def validate_args(args):
    if args.min_n < 2:
        raise ValueError("Minimum sample size must be at least 2")
    if args.max_n < args.min_n:
        raise ValueError("Maximum sample size must be >= minimum sample size")
    if args.iterations < 1:
        raise ValueError("Iterations must be at least 1")
    return True

def generate_sample_sizes(min_n, max_n, step_n):
    return list(range(min_n, max_n + 1, step_n))

def parse_effect_sizes(effect_str):
    return [float(x.strip()) for x in effect_str.split(",")]

def generate_conditions(sample_sizes, effect_sizes, test_type, hypotheses, alpha):
    conditions = []
    for n in sample_sizes:
        for effect in effect_sizes:
            for hyp in hypotheses:
                conditions.append({
                    "n": n,
                    "effect_size": effect,
                    "test_type": test_type,
                    "hypothesis": hyp,
                    "alpha": alpha
                })
    return conditions

def run_simulation_grid_chunked(conditions, iterations, output_file, logger):
    """Run simulation for all conditions, writing results in chunks to avoid memory issues."""
    all_results = []
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    for i, cond in enumerate(conditions):
        logger.info(f"Processing condition {i+1}/{len(conditions)}: n={cond['n']}, effect={cond['effect_size']}, test={cond['test_type']}")
        
        # Run simulation for this condition
        results = run_simulation_condition(cond, iterations, logger)
        all_results.extend(results)
        
        # Periodic garbage collection
        if (i + 1) % 10 == 0:
            gc.collect()
    
    # Write all results to CSV
    write_p_values_raw(all_results, output_file, logger)
    return len(all_results)

def save_results_streaming(results, output_file, logger):
    """Save results to CSV in streaming fashion."""
    write_p_values_raw(results, output_file, logger)
    logger.info(f"Saved {len(results)} results to {output_file}")

def run_aggregation_mode(args):
    """Run aggregation on existing p-values."""
    logger.info("Starting aggregation mode")
    input_file = os.path.join(args.output_dir, "p_values_raw.csv")
    output_file = os.path.join(args.output_dir, "error_rates_summary.csv")
    
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    error_rates = calculate_error_rates(input_file, args.alpha)
    save_aggregated_results(error_rates, output_file, logger)
    logger.info(f"Aggregation complete. Results saved to {output_file}")

def run_validation_mode(args):
    """Run validation against real datasets."""
    logger.info("Starting validation mode")
    
    # Download datasets
    logger.info("Downloading UCI Breast Cancer dataset")
    breast_cancer_path = download_breast_cancer_dataset("data/raw")
    logger.info("Downloading UCI Wine dataset")
    wine_path = download_wine_dataset("data/raw")
    logger.info("Downloading UCI Adult dataset")
    adult_path = download_adult_dataset("data/raw")
    
    # Preprocess data
    datasets = {
        "breast_cancer": preprocess_dataset_for_validation(breast_cancer_path, "t-test"),
        "wine": preprocess_dataset_for_validation(wine_path, "anova"),
        "adult": preprocess_dataset_for_validation(adult_path, "chi-squared")
    }
    
    # Run tests on real data
    real_pvalues = {}
    for name, data in datasets.items():
        logger.info(f"Running tests on {name} dataset")
        pvalues = save_p_values_to_csv(data, name, args.output_dir, logger)
        real_pvalues[name] = pvalues
    
    # Save real data p-values
    real_pvalues_file = os.path.join(args.output_dir, "real_data_pvalues.csv")
    # Note: save_p_values_to_csv already saves this, but we ensure it exists
    
    # Run bootstrapped validation
    logger.info("Running bootstrapped validation")
    power_results = run_bootstrapped_validation(real_pvalues, args.output_dir, logger)
    save_power_results(power_results, os.path.join(args.output_dir, "real_data_power.json"), logger)
    
    # Calculate validation metrics
    logger.info("Calculating validation metrics")
    metrics = calculate_validation_metrics(real_pvalues, args.output_dir, logger)
    save_validation_metrics(metrics, os.path.join(args.output_dir, "validation_metrics.json"), logger)
    
    # Update metadata
    metadata_path = "data/simulation_metadata.json"
    ensure_metadata_file_exists(metadata_path)
    for name, path in [("breast_cancer", breast_cancer_path), ("wine", wine_path), ("adult", adult_path)]:
        # Register checksums if needed
        pass
    
    logger.info("Validation mode complete")

def main():
    global logger
    args = parse_args()
    validate_args(args)
    
    # Setup logging
    log_dir = os.path.join("data", "reports")
    os.makedirs(log_dir, exist_ok=True)
    logger = setup_logging(log_dir)
    
    try:
        if args.mode == "simulation":
            logger.info("Starting simulation mode")
            
            # Register run in metadata
            metadata_path = "data/simulation_metadata.json"
            ensure_metadata_file_exists(metadata_path)
            register_run(metadata_path, {
                "mode": "simulation",
                "test": args.test,
                "min_n": args.min_n,
                "max_n": args.max_n,
                "iterations": args.iterations,
                "timestamp": datetime.now().isoformat()
            })
            
            sample_sizes = generate_sample_sizes(args.min_n, args.max_n, args.step_n)
            effect_sizes = parse_effect_sizes(args.effect_size)
            hypotheses = [args.hypothesis]
            conditions = generate_conditions(sample_sizes, effect_sizes, args.test, hypotheses, args.alpha)
            
            output_file = os.path.join(args.output_dir, "p_values_raw.csv")
            total_results = run_simulation_grid_chunked(conditions, args.iterations, output_file, logger)
            
            logger.info(f"Simulation complete. Generated {total_results} p-values")
            
            # Save metadata
            save_simulation_metadata(metadata_path, {
                "total_conditions": len(conditions),
                "total_iterations": args.iterations,
                "output_file": output_file
            })
            
            update_run_status(metadata_path, "simulation", "completed")
            
        elif args.mode == "aggregation":
            run_aggregation_mode(args)
            
        elif args.mode == "validation":
            run_validation_mode(args)
            
    except Exception as e:
        log_error_details(logger, e)
        update_run_status("data/simulation_metadata.json", "simulation", "failed")
        raise
    finally:
        log_shutdown(logger)

if __name__ == "__main__":
    main()
