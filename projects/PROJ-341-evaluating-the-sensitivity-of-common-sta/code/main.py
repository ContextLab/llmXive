import argparse
import gc
import json
import os
import sys
import time
import traceback
from datetime import datetime

# Add project root to path to ensure imports work
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from code.simulation.test_runner import main as simulation_main
from code.analysis.aggregator import main as aggregator_main
from code.analysis.threshold_finder import main as threshold_main
from code.visualization.plotter import main as plotter_main
from code.analysis.validator import main as validator_main
from code.analysis.bootstrapper import main as bootstrapper_main
from code.analysis.validation_metrics import main as metrics_main
from code.analysis.report_generator import main as report_main
from code.utils.checksum_utils import main as checksum_main
from code.simulation.logging_config import get_logger, log_operation

logger = get_logger(__name__)

def get_memory_usage_mb():
    """Get current memory usage in MB."""
    try:
        import resource
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    except ImportError:
        return 0

def check_memory_limit(limit_mb=7000):
    """Check if memory usage is within limit."""
    current = get_memory_usage_mb()
    return current < limit_mb

def force_gc():
    """Force garbage collection."""
    gc.collect()

def parse_args():
    parser = argparse.ArgumentParser(description="Statistical Test Sensitivity Pipeline")
    parser.add_argument('--mode', type=str, default='full',
                        choices=['full', 'simulation', 'aggregation', 'thresholds', 'plots', 'validation', 'bootstrap', 'metrics', 'report', 'checksum'],
                        help='Pipeline mode to run')
    parser.add_argument('--test', type=str, default='all',
                        help='Specific test to run (t-test, anova, chi-squared, all)')
    parser.add_argument('--min-n', type=int, default=5, help='Minimum sample size')
    parser.add_argument('--max-n', type=int, default=500, help='Maximum sample size')
    parser.add_argument('--iterations', type=int, default=1000, help='Number of iterations per condition')
    parser.add_argument('--alpha', type=float, default=0.05, help='Significance level')
    return parser.parse_args()

def run_simulation(args):
    logger.info("Running simulation...")
    # Note: The actual simulation logic is in code/simulation/test_runner.py
    # We invoke the main function there which handles the full grid or specific args
    # For this pipeline, we assume the simulation writes to data/simulation/p_values_raw.csv
    # If the test_runner needs specific args, we might need to pass them or rely on default
    simulation_main()

def run_aggregation(args):
    logger.info("Running aggregation...")
    aggregator_main()

def run_thresholds(args):
    logger.info("Running threshold analysis...")
    threshold_main()

def run_plots(args):
    logger.info("Generating plots...")
    plotter_main()

def run_validation(args):
    logger.info("Running validation on real datasets...")
    validator_main()

def run_bootstrap(args):
    logger.info("Running bootstrapped power estimation...")
    bootstrapper_main()

def run_metrics(args):
    logger.info("Calculating validation metrics...")
    metrics_main()

def run_report(args):
    logger.info("Generating validation report...")
    report_main()

def run_checksum(args):
    logger.info("Running checksum verification...")
    checksum_main()

def run_full_pipeline(args):
    """Run the full pipeline in order."""
    logger.info("Starting full pipeline...")
    start_time = time.time()

    steps = [
        ("Setup/Checksum", run_checksum),
        ("Simulation", run_simulation),
        ("Aggregation", run_aggregation),
        ("Thresholds", run_thresholds),
        ("Validation", run_validation),
        ("Bootstrap", run_bootstrap),
        ("Metrics", run_metrics),
        ("Plots", run_plots),
        ("Report", run_report)
    ]

    for step_name, step_func in steps:
        logger.info(f"Executing step: {step_name}")
        try:
            step_func(args)
            force_gc()
        except Exception as e:
            logger.error(f"Step {step_name} failed: {e}")
            traceback.print_exc()
            raise

    end_time = time.time()
    logger.info(f"Full pipeline completed in {end_time - start_time:.2f} seconds")

def main():
    args = parse_args()
    
    # Ensure directories exist
    os.makedirs("data/simulation", exist_ok=True)
    os.makedirs("data/visualization", exist_ok=True)
    os.makedirs("data/reports", exist_ok=True)
    os.makedirs("data/raw", exist_ok=True)

    try:
        if args.mode == 'full':
            run_full_pipeline(args)
        elif args.mode == 'simulation':
            run_simulation(args)
        elif args.mode == 'aggregation':
            run_aggregation(args)
        elif args.mode == 'thresholds':
            run_thresholds(args)
        elif args.mode == 'plots':
            run_plots(args)
        elif args.mode == 'validation':
            run_validation(args)
        elif args.mode == 'bootstrap':
            run_bootstrap(args)
        elif args.mode == 'metrics':
            run_metrics(args)
        elif args.mode == 'report':
            run_report(args)
        elif args.mode == 'checksum':
            run_checksum(args)
        else:
            logger.error(f"Unknown mode: {args.mode}")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
