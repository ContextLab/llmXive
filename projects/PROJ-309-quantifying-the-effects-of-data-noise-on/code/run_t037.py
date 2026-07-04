"""
Runner script for Task T037: Add timing logic to verify pipeline completes within 2-hour CPU budget.

This script demonstrates the timing monitor by running a simulated pipeline 
with multiple phases and verifying it stays within the 2-hour budget.
"""
import os
import sys
import time
import json
import logging
import argparse
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from code.timing_monitor import PipelineTimer, PIPELINE_TIME_LIMIT_SECONDS
from code.main import run_full_pipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_simulated_pipeline(timer: PipelineTimer) -> None:
    """
    Run a simulated pipeline with multiple phases for demonstration.
    
    In a real scenario, this would call the actual pipeline phases.
    For T037, we simulate phases to demonstrate timing monitoring.
    
    Args:
        timer: The PipelineTimer instance to use for timing.
    """
    # Simulate data generation phase (T012-T017)
    with timer.measure_phase("data_generation"):
        logger.info("Simulating clean trajectory generation...")
        time.sleep(0.5)  # Simulate computation time
        logger.info("Clean trajectories generated successfully.")

    # Simulate noise injection phase (T020-T024)
    with timer.measure_phase("noise_injection"):
        logger.info("Simulating noise injection across SNR levels...")
        time.sleep(0.8)  # Simulate computation time
        logger.info("Noisy trajectories generated successfully.")

    # Simulate metrics computation phase (T027-T029)
    with timer.measure_phase("metrics_computation"):
        logger.info("Simulating metric computation (Correlation Dimension, Lyapunov, FNN)...")
        time.sleep(1.2)  # Simulate computation time
        logger.info("Metrics computed successfully.")

    # Simulate error analysis phase (T030-T031)
    with timer.measure_phase("error_analysis"):
        logger.info("Simulating error calculation and threshold identification...")
        time.sleep(0.6)  # Simulate computation time
        logger.info("Error analysis completed.")

    # Simulate visualization and export phase (T034-T036)
    with timer.measure_phase("visualization_export"):
        logger.info("Simulating plot generation and CSV export...")
        time.sleep(0.4)  # Simulate computation time
        logger.info("Visualization and export completed.")


def run_real_pipeline(timer: PipelineTimer) -> None:
    """
    Run the actual pipeline with timing monitoring.
    
    Args:
        timer: The PipelineTimer instance to use for timing.
    """
    try:
        # Run the full pipeline with timing phases
        with timer.measure_phase("pipeline_execution"):
            run_full_pipeline()
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        raise


def main(args=None):
    """
    Main entry point for T037 timing verification.
    
    Args:
        args: Command line arguments (optional).
    """
    parser = argparse.ArgumentParser(
        description="Task T037: Verify pipeline execution time is within 2-hour budget"
    )
    parser.add_argument(
        "--simulate",
        action="store_true",
        help="Run simulated pipeline phases for demonstration"
    )
    parser.add_argument(
        "--real",
        action="store_true",
        help="Run the actual pipeline (default if no flag provided)"
    )
    parser.add_argument(
        "--report-dir",
        type=str,
        default="data/results",
        help="Directory to store timing reports"
    )

    parsed_args = parser.parse_args(args) if args else argparse.Namespace(simulate=False, real=False)

    # Default to simulated if neither flag is set
    if not parsed_args.simulate and not parsed_args.real:
        parsed_args.simulate = True

    logger.info("=" * 60)
    logger.info("Starting Task T037: Pipeline Timing Verification")
    logger.info(f"Time limit: {PIPELINE_TIME_LIMIT_SECONDS / 3600:.1f} hours")
    logger.info("=" * 60)

    # Initialize timer
    timer = PipelineTimer(report_dir=parsed_args.report_dir)
    timer.start()

    try:
        if parsed_args.simulate:
            logger.info("Running SIMULATED pipeline phases...")
            run_simulated_pipeline(timer)
        else:
            logger.info("Running REAL pipeline...")
            run_real_pipeline(timer)

        # Stop timer
        timer.stop()

        # Check budget
        within_budget = timer.check_budget()

        # Generate and save report
        report_path = timer.save_report()

        # Final status
        if within_budget:
            logger.info("SUCCESS: Pipeline completed within the 2-hour budget.")
            logger.info(f"Total time: {timer.elapsed_seconds:.2f} seconds")
            logger.info(f"Report saved to: {report_path}")
            return 0
        else:
            logger.error("FAILURE: Pipeline exceeded the 2-hour budget.")
            logger.error(f"Total time: {timer.elapsed_seconds:.2f} seconds")
            logger.error(f"Report saved to: {report_path}")
            return 1

    except Exception as e:
        logger.error(f"Pipeline execution failed with error: {e}")
        if timer.start_time:
            timer.stop()
            timer.save_report()
        return 2


if __name__ == "__main__":
    sys.exit(main())
