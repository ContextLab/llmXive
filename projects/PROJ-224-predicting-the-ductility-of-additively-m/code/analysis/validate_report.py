"""
Validation script for the final report generation (Task T036).

This script validates that the final report (Markdown/PDF) can be rendered
within the 30-second time budget on a CI system. It runs the reporting
script, measures execution time, and verifies the output artifacts exist.
"""
import os
import sys
import time
import logging
import subprocess
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def ensure_output_directory(output_dir: str) -> bool:
    """Ensure the output directory exists."""
    path = Path(output_dir)
    try:
        path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Output directory ensured: {output_dir}")
        return True
    except Exception as e:
        logger.error(f"Failed to create output directory {output_dir}: {e}")
        return False

def run_reporting_script(script_path: str, output_dir: str, timeout_seconds: int = 30) -> bool:
    """
    Run the reporting script and measure execution time.
    
    Args:
        script_path: Path to the reporting script (code/analysis/reporting.py)
        output_dir: Directory where the report should be generated
        timeout_seconds: Maximum allowed execution time in seconds
    
    Returns:
        True if the script completes within the time budget, False otherwise.
    """
    cmd = [sys.executable, script_path, "--output-dir", output_dir]
    logger.info(f"Running reporting script: {' '.join(cmd)}")
    
    start_time = time.time()
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_seconds
        )
        elapsed = time.time() - start_time
        
        logger.info(f"Reporting script completed in {elapsed:.2f} seconds")
        
        if result.returncode == 0:
            if elapsed <= timeout_seconds:
                logger.info(f"SUCCESS: Report generated within {timeout_seconds}s budget ({elapsed:.2f}s)")
                return True
            else:
                logger.error(f"FAILURE: Report generation exceeded {timeout_seconds}s budget ({elapsed:.2f}s)")
                return False
        else:
            logger.error(f"FAILURE: Reporting script failed with return code {result.returncode}")
            if result.stderr:
                logger.error(f"stderr: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        elapsed = time.time() - start_time
        logger.error(f"FAILURE: Reporting script timed out after {timeout_seconds}s")
        return False
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"FAILURE: Exception while running reporting script: {e}")
        return False

def verify_report_artifacts(output_dir: str, expected_files: list) -> bool:
    """
    Verify that the expected report artifacts were created.
    
    Args:
        output_dir: Directory to check for artifacts
        expected_files: List of expected filenames (relative to output_dir)
    
    Returns:
        True if all expected files exist, False otherwise.
    """
    all_exist = True
    for filename in expected_files:
        file_path = Path(output_dir) / filename
        if file_path.exists():
            logger.info(f"Verified: {file_path} exists")
        else:
            logger.error(f"MISSING: Expected file {file_path} does not exist")
            all_exist = False
    
    return all_exist

def validate_report_rendering(output_dir: str = "data/reports", timeout_seconds: int = 30) -> bool:
    """
    Main validation function for Task T036.
    
    Validates that the final report renders as PDF/Markdown within the time budget.
    
    Args:
        output_dir: Directory for report output
        timeout_seconds: Maximum allowed rendering time
    
    Returns:
        True if validation passes, False otherwise.
    """
    logger.info("Starting Report Rendering Validation (Task T036)")
    
    # Ensure output directory exists
    if not ensure_output_directory(output_dir):
        return False
    
    # Define paths
    script_path = "code/analysis/reporting.py"
    if not os.path.exists(script_path):
        logger.error(f"Reporting script not found: {script_path}")
        return False
    
    # Define expected output files
    expected_files = [
        "final_report.md",
        "final_report.pdf"  # Optional, depends on configuration
    ]
    
    # Run the reporting script
    success = run_reporting_script(script_path, output_dir, timeout_seconds)
    
    if not success:
        logger.error("Report generation failed or timed out.")
        return False
    
    # Verify artifacts
    # Note: PDF generation might be optional depending on environment
    # We primarily validate Markdown existence
    if not verify_report_artifacts(output_dir, ["final_report.md"]):
        logger.error("Required report artifacts are missing.")
        return False
    
    logger.info("Report Rendering Validation PASSED")
    return True

def main():
    """Entry point for the validation script."""
    output_dir = os.environ.get("REPORT_OUTPUT_DIR", "data/reports")
    timeout = int(os.environ.get("REPORT_TIMEOUT_SECONDS", "30"))
    
    success = validate_report_rendering(output_dir=output_dir, timeout_seconds=timeout)
    
    if success:
        print("VALIDATION_RESULT: PASS")
        sys.exit(0)
    else:
        print("VALIDATION_RESULT: FAIL")
        sys.exit(1)

if __name__ == "__main__":
    main()