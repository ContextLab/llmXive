"""
Quickstart Validator.

Verifies that all declared deliverables exist after pipeline execution.
"""
import os
import sys
import logging
import time
import traceback
from pathlib import Path

# Add project root
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def log_section(msg):
    logger.info("=" * 50)
    logger.info(msg)
    logger.info("=" * 50)

def check_file_exists(path_str):
    path = Path(path_str)
    if path.exists():
        logger.info(f"✓ Found: {path}")
        return True
    else:
        logger.error(f"✗ Missing: {path}")
        return False

def main():
    """Validates declared deliverables."""
    log_section("Validating Declared Deliverables")
    
    required_files = [
        "data/raw/cyberbullying_2021.csv",
        "data/results/analysis_cohort.csv",
        "data/results/regression_results.csv",
        "data/results/sensitivity_analysis.csv",
        "data/results/regression_summary.md",
        "data/results/platform_status.json",
        "data/results/validation_report.json"
    ]
    
    all_present = True
    for f in required_files:
        full_path = project_root.parent / f
        if not check_file_exists(str(full_path)):
            all_present = False
    
    log_section("Validation Complete")
    if all_present:
        logger.info("All declared deliverables are present.")
    else:
        logger.error("Some declared deliverables are missing.")
        sys.exit(1)

if __name__ == "__main__":
    main()
