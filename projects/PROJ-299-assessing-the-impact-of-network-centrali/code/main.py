"""
Main Orchestrator Script

Executes the full pipeline: US1 -> US2 -> US3.
Reconciled with quickstart.md to ensure all required steps are invoked.
"""
import argparse
import sys
import os
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

# Import US1 pipeline
from code.main_us1 import run_us1_pipeline
from code.main_us2 import run_us2_pipeline
from code.main_us3 import run_us3_pipeline
from code.utils.logging_config import setup_logging, get_logger

# Ensure necessary directories exist before running
def ensure_required_dirs():
    dirs = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "analysis",
        project_root / "outputs" / "viz",
        project_root / "logs",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def main():
    parser = argparse.ArgumentParser(description="Run Full Analysis Pipeline")
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level",
    )
    args = parser.parse_args()

    # Ensure directories exist
    ensure_required_dirs()

    # Setup logging
    log_path = project_root / "logs" / "pipeline.log"
    setup_logging(log_path=log_path, level=args.log_level)
    logger = get_logger("main")

    logger.info("Starting Full Pipeline")

    try:
        # Run US1: Download, Preprocess, Connectivity, Centrality
        logger.info("Executing User Story 1 (Download -> Preprocess -> Centrality)...")
        ret1 = run_us1_pipeline()
        if ret1 != 0:
            logger.error("US1 failed. Aborting pipeline.")
            return ret1

        # Run US2: Merge, Regression, Diagnostics
        logger.info("Executing User Story 2 (Merge -> Regression -> Diagnostics)...")
        ret2 = run_us2_pipeline()
        if ret2 != 0:
            logger.error("US2 failed. Aborting pipeline.")
            return ret2

        # Run US3: Visualization, Report
        logger.info("Executing User Story 3 (Viz -> Report)...")
        ret3 = run_us3_pipeline()
        if ret3 != 0:
            logger.error("US3 failed. Aborting pipeline.")
            return ret3

        logger.info("Full Pipeline completed successfully.")
        return 0

    except Exception as e:
        logger.exception(f"Unexpected error in main pipeline: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
