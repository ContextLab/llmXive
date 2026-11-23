import os
import sys
import time
import logging
from pathlib import Path

from utils import setup_logging
from download import main as download_main
from construct_network import main as construct_network_main
from compute_metrics import main as compute_metrics_main
from analyze import main as analyze_main
from report import main as report_main
from runtime_monitor import record_start_time, measure_and_log_runtime

# Configure logging
LOG_DIR = Path("results")
LOG_DIR.mkdir(exist_ok=True)
logger = setup_logging("quickstart", str(LOG_DIR / "quickstart.log"))

def run_pipeline():
    """Run the full pipeline from download to report generation."""
    logger.info("Starting full pipeline execution.")
    
    # Record start time for runtime monitoring
    record_start_time()
    
    steps = [
        ("Downloading CIF files", download_main, ["--limit", "50", "--output", "data/raw/cif/"]),
        ("Constructing networks", construct_network_main, ["--input", "data/raw/cif/", "--output", "data/processed/networks/"]),
        ("Computing metrics", compute_metrics_main, ["--input", "data/processed/networks/", "--output", "data/processed/metrics.csv"]),
        ("Analyzing data", analyze_main, ["--input", "data/processed/metrics.csv", "--output", "results/"]),
        ("Generating report", report_main, []),
    ]

    for step_name, func, args in steps:
        logger.info(f"Executing step: {step_name}")
        try:
            # We need to simulate sys.argv for the functions that expect it
            old_argv = sys.argv
            sys.argv = [sys.argv[0]] + args
            func()
            sys.argv = old_argv
            logger.info(f"Step completed: {step_name}")
        except Exception as e:
            logger.error(f"Step failed: {step_name}. Error: {e}")
            raise

    # Measure and log total runtime
    logger.info("Pipeline execution complete. Measuring runtime.")
    runtime_success = measure_and_log_runtime()
    
    if not runtime_success:
        logger.error("Runtime measurement failed or exceeded limits.")
        return False
    
    logger.info("Full pipeline completed successfully.")
    return True

def main():
    """Main entry point for quickstart."""
    try:
        success = run_pipeline()
        return 0 if success else 1
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())