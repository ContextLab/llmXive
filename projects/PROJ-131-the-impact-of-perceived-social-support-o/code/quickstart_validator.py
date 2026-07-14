"""
T035: Quickstart Validation Script
Runs the end-to-end pipeline as described in quickstart.md to ensure
all components function correctly and produce the required artifacts.
"""
import os
import sys
import logging
import time
import traceback
from pathlib import Path

# Add project root to path if not already present
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from logger import get_logger
from main_pipeline import run_pipeline

def log_section(title: str):
    logger = get_logger()
    logger.info("=" * 60)
    logger.info(f" {title} ")
    logger.info("=" * 60)

def check_file_exists(path: str, description: str):
    p = Path(path)
    if not p.exists():
        logger = get_logger()
        logger.error(f"MISSING: {description} not found at {p.resolve()}")
        return False
    logger.info(f"FOUND: {description} at {p.resolve()}")
    return True

def main():
    logger = get_logger()
    logger.setLevel(logging.INFO)
    
    log_section("T035: Quickstart Validation Starting")
    logger.info("Executing end-to-end pipeline validation...")
    
    start_time = time.time()
    success = True
    
    try:
        # Run the main pipeline
        log_section("Step 1: Executing Main Pipeline")
        run_pipeline()
        log_section("Step 1: Pipeline Execution Completed")
        
    except Exception as e:
        logger.error(f"Pipeline execution failed: {str(e)}")
        traceback.print_exc()
        success = False
    
    elapsed = time.time() - start_time
    logger.info(f"Total execution time: {elapsed:.2f} seconds")
    
    # Verify expected output artifacts
    log_section("Step 2: Verifying Output Artifacts")
    
    required_files = [
        ("data/results/synthetic_cohort.csv", "Synthetic Cohort"),
        ("data/results/regression_results.csv", "Regression Results"),
        ("data/results/sensitivity_analysis.csv", "Sensitivity Analysis"),
        ("data/results/regression_summary.md", "Regression Summary Report"),
        ("data/results/sensitivity_comparison.csv", "Sensitivity Comparison Table"),
    ]
    
    missing_files = []
    for path, desc in required_files:
        if not check_file_exists(path, desc):
            missing_files.append(path)
    
    if missing_files:
        logger.error(f"Validation FAILED: Missing {len(missing_files)} required files.")
        for f in missing_files:
            logger.error(f"  - {f}")
        success = False
    else:
        logger.info("Validation PASSED: All required output files generated.")
    
    log_section("T035: Validation Summary")
    if success:
        logger.info("SUCCESS: End-to-end pipeline validation completed successfully.")
        logger.info("All required artifacts were generated and verified.")
        return 0
    else:
        logger.error("FAILURE: Validation failed due to missing artifacts or pipeline errors.")
        return 1

if __name__ == "__main__":
    sys.exit(main())