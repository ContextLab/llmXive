"""
Main entry point for the simulation and validation pipeline.
Orchestrates the execution of all phases.
"""
import argparse
import gc
import json
import os
import sys
import time
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from code.simulation.logging_config import setup_logging, get_logger
from code.simulation.test_runner import run_simulation_condition
from code.simulation.output_writer import write_p_values_raw
from code.analysis.aggregator import calculate_error_rates, save_aggregated_results
from code.analysis.threshold_finder import save_thresholds
from code.visualization.plotter import generate_all_plots
from code.analysis.validator import run_validation_on_datasets
from code.analysis.bootstrapper import main as bootstrap_main
from code.analysis.validation_metrics import main as metrics_main
from code.analysis.report_generator import main as report_main
from code.utils.checksum_utils import main as checksum_main

logger = get_logger(__name__)


def get_memory_usage_mb():
    try:
        import resource
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
    except:
        return 0.0


def check_memory_limit(limit_mb=7000):
    usage = get_memory_usage_mb()
    if usage > limit_mb:
        logger.warning(f"Memory usage {usage:.1f}MB exceeds limit {limit_mb}MB")
        return False
    return True


def force_gc():
    gc.collect()


def parse_args():
    parser = argparse.ArgumentParser(description="Statistical Test Sensitivity Analysis")
    parser.add_argument("--mode", type=str, default="full", 
                      choices=["simulation", "validation", "full", "aggregation", "thresholds", "plots", "bootstrap", "metrics", "report"],
                      help="Execution mode")
    parser.add_argument("--test", type=str, default="all",
                      help="Specific test to run (t-test, anova, chi-squared, or 'all')")
    parser.add_argument("--min-n", type=int, default=5,
                      help="Minimum sample size")
    parser.add_argument("--max-n", type=int, default=500,
                      help="Maximum sample size")
    parser.add_argument("--step-n", type=int, default=5,
                      help="Step size for sample size")
    parser.add_argument("--iterations", type=int, default=10000,
                      help="Number of iterations per condition")
    parser.add_argument("--alpha", type=float, default=0.05,
                      help="Significance level")
    parser.add_argument("--effect-size", type=float, default=0.5,
                      help="Effect size for simulation")
    
    return parser.parse_args()


def run_simulation(args):
    logger.info(f"Starting simulation: n={args.min_n} to {args.max_n}, steps={args.step_n}, iterations={args.iterations}")
    
    sample_sizes = list(range(args.min_n, args.max_n + 1, args.step_n))
    test_types = ["t-test", "anova", "chi-squared"] if args.test == "all" else [args.test]
    
    all_results = []
    
    for n in sample_sizes:
        if not check_memory_limit():
            logger.error("Memory limit exceeded. Stopping simulation.")
            break
        
        for test_type in test_types:
            logger.info(f"Running {test_type} with n={n}")
            
            # Run simulation condition
            results = run_simulation_condition(
                test_type=test_type,
                sample_size=n,
                iterations=args.iterations,
                alpha=args.alpha,
                effect_size=args.effect_size
            )
            
            all_results.append(results)
            force_gc()
    
    # Write raw p-values
    write_p_values_raw(all_results)
    logger.info("Simulation complete. Raw p-values written.")


def run_aggregation(args):
    logger.info("Running aggregation...")
    # Aggregator reads p_values_raw.csv and writes error_rates_summary.csv
    save_aggregated_results()
    logger.info("Aggregation complete.")


def run_thresholds(args):
    logger.info("Calculating thresholds...")
    save_thresholds()
    logger.info("Thresholds saved.")


def run_plots(args):
    logger.info("Generating plots...")
    generate_all_plots()
    logger.info("Plots generated.")


def run_validation(args):
    logger.info("Running validation on real datasets...")
    run_validation_on_datasets()
    logger.info("Validation complete. Real data p-values saved.")


def run_bootstrap(args):
    logger.info("Running bootstrapped power estimation...")
    bootstrap_main()
    logger.info("Bootstrap complete.")


def run_metrics(args):
    logger.info("Calculating validation metrics...")
    metrics_main()
    logger.info("Metrics complete.")


def run_report(args):
    logger.info("Generating final report...")
    report_main()
    logger.info("Report generated.")


def run_full_pipeline(args):
    logger.info("Starting full pipeline...")
    run_simulation(args)
    run_aggregation(args)
    run_thresholds(args)
    run_validation(args)
    run_bootstrap(args)
    run_metrics(args)
    run_report(args)
    logger.info("Full pipeline complete.")


def main():
    args = parse_args()
    setup_logging()
    
    start_time = time.time()
    
    try:
        validate_args(args)
        
        if args.mode == "simulation":
            run_simulation(args)
        elif args.mode == "aggregation":
            run_aggregation(args)
        elif args.mode == "thresholds":
            run_thresholds(args)
        elif args.mode == "plots":
            run_plots(args)
        elif args.mode == "validation":
            run_validation(args)
        elif args.mode == "bootstrap":
            run_bootstrap(args)
        elif args.mode == "metrics":
            run_metrics(args)
        elif args.mode == "report":
            run_report(args)
        elif args.mode == "full":
            run_full_pipeline(args)
        else:
            logger.error(f"Unknown mode: {args.mode}")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise
    finally:
        elapsed = time.time() - start_time
        logger.info(f"Total execution time: {elapsed:.2f} seconds")


if __name__ == "__main__":
    main()
