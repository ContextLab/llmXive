"""
Quickstart script to run the full pipeline end-to-end.
Orchestrates download, network construction, metrics computation,
analysis, and runtime monitoring.
"""

import os
import sys
import time
import logging
from pathlib import Path

# Import pipeline stages
from download import main as download_main
from construct_network import main as construct_network_main
from compute_metrics import main as compute_metrics_main
from analyze import main as analyze_main
from report import main as report_main
from runtime_monitor import record_start_time, measure_and_log_runtime


def setup_quickstart_logger() -> logging.Logger:
    """Set up and return the quickstart logger."""
    logger = logging.getLogger("quickstart")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def run_pipeline() -> None:
    """
    Execute the full research pipeline in the correct order:
    1. Record start time
    2. Download CIF files
    3. Construct networks
    4. Compute metrics
    5. Analyze (VIF, model training, cross-validation)
    6. Generate report
    7. Measure and log runtime
    """
    logger = setup_quickstart_logger()
    logger.info("Starting full pipeline execution...")

    # Record start time for runtime monitoring
    record_start_time()
    logger.info("Pipeline start time recorded.")

    try:
        # Step 1: Download CIF files
        logger.info("Step 1: Downloading CIF files...")
        download_main()
        logger.info("Step 1 complete: CIF files downloaded.")

        # Step 2: Construct networks
        logger.info("Step 2: Constructing networks...")
        construct_network_main()
        logger.info("Step 2 complete: Networks constructed.")

        # Step 3: Compute metrics
        logger.info("Step 3: Computing metrics...")
        compute_metrics_main()
        logger.info("Step 3 complete: Metrics computed.")

        # Step 4: Analyze (VIF, model training, cross-validation)
        logger.info("Step 4: Running analysis...")
        analyze_main()
        logger.info("Step 4 complete: Analysis finished.")

        # Step 5: Generate report
        logger.info("Step 5: Generating report...")
        report_main()
        logger.info("Step 5 complete: Report generated.")

        # Step 6: Measure and log runtime
        logger.info("Step 6: Measuring pipeline runtime...")
        measure_and_log_runtime()
        logger.info("Step 6 complete: Runtime measured and logged.")

        logger.info("Full pipeline execution completed successfully.")

    except Exception as e:
        logger.error(f"Pipeline execution failed: {str(e)}")
        raise


def main() -> None:
    """Entry point for quickstart."""
    run_pipeline()


if __name__ == "__main__":
    main()
