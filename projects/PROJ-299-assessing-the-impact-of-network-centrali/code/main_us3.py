"""
User Story 3 Orchestration Script

Chains: Visualization -> Report Generation.
Produces: outputs/final_report.pdf, outputs/viz/*.png.
"""
import argparse
import json
import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from code.viz.plotting import generate_plots
from code.viz.report_generator import generate_report
from code.utils.logging_config import setup_logging, get_logger

def run_us3_pipeline():
    """
    Executes the full User Story 3 pipeline.
    Returns 0 on success, non-zero on failure.
    """
    logger = get_logger("us3")
    logger.info("Starting User Story 3 Pipeline")

    # 1. Generate Plots
    logger.info("Step 1: Generating Visualizations...")
    ret = generate_plots()
    if ret != 0:
        logger.error("Plot generation failed.")
        return ret

    # 2. Generate Report
    logger.info("Step 2: Generating Final Report...")
    ret = generate_report()
    if ret != 0:
        logger.error("Report generation failed.")
        return ret

    logger.info("User Story 3 Pipeline completed successfully.")
    return 0

def main():
    parser = argparse.ArgumentParser(description="Run User Story 3 Pipeline")
    parser.add_argument("--log-level", type=str, default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    args = parser.parse_args()

    log_path = project_root / "logs" / "pipeline.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    setup_logging(log_path=log_path, level=args.log_level)

    return run_us3_pipeline()

if __name__ == "__main__":
    sys.exit(main())
