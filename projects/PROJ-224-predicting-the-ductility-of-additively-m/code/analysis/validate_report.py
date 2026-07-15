"""
Task T036: Validate final report renders as PDF/Markdown within 30s on CI.

This script performs a local simulation of the CI report generation process.
It measures the time taken to generate the final report using the existing
reporting pipeline and verifies it completes within the 30-second budget.
"""
import os
import sys
import time
import logging
import subprocess
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from analysis.reporting import generate_final_report, main as reporting_main

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

REPORT_TIMEOUT_SECONDS = 30
REPORT_OUTPUT_PATH = "data/final_report.md"

def run_report_generation():
    """
    Executes the report generation and measures the time taken.
    Returns (success, duration_seconds, error_message).
    """
    logger.info(f"Starting report generation validation (timeout: {REPORT_TIMEOUT_SECONDS}s)...")
    
    start_time = time.time()
    try:
        # We call the main logic of the reporting module directly
        # to simulate the CI execution without spawning a new process.
        # This ensures we are testing the actual code path.
        generate_final_report()
        
        # Verify the output file exists
        output_path = project_root / REPORT_OUTPUT_PATH
        if not output_path.exists():
            return False, 0, f"Report file not created at {output_path}"
        
        duration = time.time() - start_time
        
        if duration > REPORT_TIMEOUT_SECONDS:
            return False, duration, f"Report generation took {duration:.2f}s (exceeds {REPORT_TIMEOUT_SECONDS}s limit)"
        
        logger.info(f"Report generated successfully in {duration:.2f}s.")
        return True, duration, None

    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Report generation failed after {duration:.2f}s: {e}")
        return False, duration, str(e)

def main():
    """
    Main entry point for the validation script.
    Exits with code 0 on success, 1 on failure.
    """
    success, duration, error = run_report_generation()
    
    if success:
        logger.info("VALIDATION PASSED: Report renders within time budget.")
        sys.exit(0)
    else:
        logger.error(f"VALIDATION FAILED: {error}")
        sys.exit(1)

if __name__ == "__main__":
    main()
