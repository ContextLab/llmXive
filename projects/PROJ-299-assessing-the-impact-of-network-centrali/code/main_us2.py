"""
User Story 2 Orchestration Script

Chains: QC Validation -> Merge -> Regression -> Diagnostics.
Produces: data/analysis/regression_results.csv, data/analysis/diagnostics.json.
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

from code.analysis.qc_validator import validate_qc
from code.analysis.data_merger import merge_data
from code.analysis.regression import run_regression_analysis
from code.analysis.diagnostics import run_diagnostics
from code.utils.logging_config import setup_logging, get_logger

def run_us2_pipeline():
    """
    Executes the full User Story 2 pipeline.
    Returns 0 on success, non-zero on failure.
    """
    logger = get_logger("us2")
    logger.info("Starting User Story 2 Pipeline")

    # 1. Validate QC Counts
    logger.info("Step 1: Validating QC Counts...")
    ret = validate_qc()
    if ret != 0:
        logger.error("QC Validation failed.")
        return ret

    # 2. Merge Data
    logger.info("Step 2: Merging Data...")
    ret = merge_data()
    if ret != 0:
        logger.error("Data merging failed.")
        return ret

    # 3. Run Regression
    logger.info("Step 3: Running Regression Analysis...")
    ret = run_regression_analysis()
    if ret != 0:
        logger.error("Regression analysis failed.")
        return ret

    # 4. Run Diagnostics
    logger.info("Step 4: Running Diagnostics...")
    ret = run_diagnostics()
    if ret != 0:
        logger.error("Diagnostics failed.")
        return ret

    logger.info("User Story 2 Pipeline completed successfully.")
    return 0

def main():
    parser = argparse.ArgumentParser(description="Run User Story 2 Pipeline")
    parser.add_argument("--log-level", type=str, default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    args = parser.parse_args()

    log_path = project_root / "logs" / "pipeline.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    setup_logging(log_path=log_path, level=args.log_level)

    return run_us2_pipeline()

if __name__ == "__main__":
    sys.exit(main())
