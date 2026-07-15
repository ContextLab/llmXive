"""
Main entry point for the simulation and validation pipeline.
"""
from __future__ import annotations

import argparse
import gc
import json
import os
import sys
import traceback
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from code.simulation.logging_config import get_logger, log_operation, log_error_details
from code.simulation.test_runner import run_simulation_condition
from code.simulation.output_writer import write_p_values_raw, ensure_output_directory
from code.analysis.aggregator import calculate_error_rates, save_aggregated_results
from code.analysis.validator import download_breast_cancer_dataset, download_wine_dataset, download_adult_dataset, prepare_data_for_ttest, prepare_data_for_anova, prepare_data_for_chi_squared
from code.analysis.real_data_runner import run_validation_on_datasets
from code.utils.checksum_utils import register_run, update_run_status
from code.simulation.data_generator import generate_two_sample_data, generate_anova_data, generate_contingency_table_data

logger = get_logger("main")

def get_memory_usage_mb():
    """Get current memory usage in MB."""
    try:
        import resource
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    except Exception:
        return 0.0

def check_memory_limit(limit_mb: float = 7000.0) -> bool:
    """Check if memory usage is within limit."""
    current = get_memory_usage_mb()
    if current > limit_mb:
        logger.log("memory_limit_exceeded", current=current, limit=limit_mb)
        return False
    return True

def force_gc():
    """Force garbage collection."""
    gc.collect()

def parse_args():
    parser = argparse.ArgumentParser(description="Statistical Test Sensitivity Analysis")
    parser.add_argument("--mode", type=str, default="simulation", choices=["simulation", "validation", "full"],
                        help="Mode of operation: simulation, validation, or full pipeline")
    parser.add_argument("--test", type=str, default="t-test", choices=["t-test", "anova", "chi-squared"],
                        help="Statistical test to run")
    parser.add_argument("--min-n", type=int, default=5, help="Minimum sample size")
    parser.add_argument("--max-n", type=int, default=500, help="Maximum sample size")
    parser.add_argument("--step-n", type=int, default=5, help="Step size for sample sizes")
    parser.add_argument("--iterations", type=int, default=1000, help="Number of iterations per condition")
    parser.add_argument("--alpha", type=float, default=0.05, help="Significance level")
    parser.add_argument("--effect-size", type=float, default=0.5, help="Effect size for simulation")
    parser.add_argument("--chunk-size", type=int, default=50, help="Chunk size for processing")
    parser.add_argument("--hypotheses", type=str, default="null,alternative", help="Comma-separated list of hypotheses")
    return parser.parse_args()

def validate_args(args):
    if args.min_n < 2:
        raise ValueError("Minimum sample size must be at least 2")
    if args.max_n < args.min_n:
        raise ValueError("Maximum sample size must be greater than or equal to minimum")
    if args.iterations < 1:
        raise ValueError("Iterations must be at least 1")
    return True

def generate_sample_sizes(min_n: int, max_n: int, step: int):
    return list(range(min_n, max_n + 1, step))

def parse_effect_sizes(effect_str: str):
    return [float(x) for x in effect_str.split(",")]

def parse_hypotheses(hypotheses_str: str):
    return [h.strip() for h in hypotheses_str.split(",")]

def generate_conditions(args):
    sample_sizes = generate_sample_sizes(args.min_n, args.max_n, args.step_n)
    hypotheses = parse_hypotheses(args.hypotheses)
    # For simplicity, we use a single effect size for the grid
    effect_sizes = [args.effect_size]
    
    conditions = []
    for n in sample_sizes:
        for h in hypotheses:
            for es in effect_sizes:
                conditions.append({
                    "sample_size": n,
                    "hypothesis": h,
                    "effect_size": es,
                    "test_type": args.test,
                    "iterations": args.iterations,
                    "alpha": args.alpha
                })
    return conditions

def run_simulation_grid_chunked(args):
    """Run the simulation grid in chunks to manage memory."""
    logger.log("simulation_start", mode="chunked", **vars(args))
    
    # Register run
    try:
        register_run("simulation", vars(args))
    except TypeError:
        # Fallback for older signature
        register_run("simulation")

    conditions = generate_conditions(args)
    
    # Ensure output directory
    ensure_output_directory()
    
    all_p_values = []
    
    for i, condition in enumerate(conditions):
        if i % args.chunk_size == 0 and i > 0:
            force_gc()
            if not check_memory_limit():
                logger.log("memory_limit_warning", iteration=i)
        
        logger.log("simulation_condition", index=i, **condition)
        
        # Run simulation for this condition
        results = run_simulation_condition(condition)
        
        # Collect results
        for res in results:
            all_p_values.append(res)
        
        # Write partial results to avoid losing everything on crash
        if (i + 1) % 10 == 0:
            write_p_values_raw(all_p_values, overwrite=False)

    # Write final results
    write_p_values_raw(all_p_values, overwrite=True)
    
    # Aggregate results
    save_aggregated_results(all_p_values, args.alpha)
    
    logger.log("simulation_complete", total_conditions=len(conditions))

def run_validation_mode(args):
    """Run the validation mode on real datasets."""
    logger.log("validation_start", **vars(args))
    
    try:
        register_run("validation", vars(args))
    except TypeError:
        register_run("validation")

    # Run validation on datasets
    run_validation_on_datasets()
    
    logger.log("validation_complete")

def run_full_pipeline(args):
    """Run the full pipeline: simulation, aggregation, validation, bootstrapping, reporting."""
    logger.log("full_pipeline_start")
    
    # Run simulation
    run_simulation_grid_chunked(args)
    
    # Run validation
    run_validation_mode(args)
    
    # Run bootstrapper (T032)
    from code.analysis.bootstrapper import main as bootstrapper_main
    bootstrapper_main()
    
    # Run report generator
    from code.analysis.report_generator import main as report_main
    report_main()
    
    logger.log("full_pipeline_complete")

def main():
    args = parse_args()
    
    try:
        validate_args(args)
        
        if args.mode == "simulation":
            run_simulation_grid_chunked(args)
        elif args.mode == "validation":
            run_validation_mode(args)
        elif args.mode == "full":
            run_full_pipeline(args)
        else:
            raise ValueError(f"Unknown mode: {args.mode}")
            
    except Exception as e:
        # Log error details
        try:
            log_error_details(e, context=vars(args))
        except TypeError:
            # Fallback for older signature
            log_error_details(e)
        
        logger.log("critical_error", error=str(e))
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
