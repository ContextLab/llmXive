"""
Validate that the final report renders as PDF/Markdown within the time budget.

This script executes the reporting pipeline and measures the time taken to
generate the final report artifacts. It ensures the process completes within
the 30-second CI budget.
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
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Time budget constants
REPORT_RENDER_BUDGET_SECONDS = 30
PROJECT_ROOT = Path(__file__).parent.parent.parent
REPORT_SCRIPT = PROJECT_ROOT / "code" / "analysis" / "reporting.py"
REPORT_OUTPUT_DIR = PROJECT_ROOT / "data" / "reports"
REPORT_MARKDOWN = REPORT_OUTPUT_DIR / "final_report.md"
REPORT_PDF = REPORT_OUTPUT_DIR / "final_report.pdf"

def ensure_output_directory():
    """Ensure the report output directory exists."""
    REPORT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured output directory exists: {REPORT_OUTPUT_DIR}")

def run_reporting_script():
    """
    Execute the reporting script to generate the final report.
    
    Returns:
        tuple: (success: bool, duration: float, output: str)
    """
    logger.info(f"Starting report generation script: {REPORT_SCRIPT}")
    start_time = time.time()
    
    try:
        # Run the reporting script
        result = subprocess.run(
            [sys.executable, str(REPORT_SCRIPT)],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=REPORT_RENDER_BUDGET_SECONDS + 10  # Add buffer
        )
        
        duration = time.time() - start_time
        output = result.stdout + result.stderr
        
        if result.returncode != 0:
            logger.error(f"Reporting script failed with return code {result.returncode}")
            logger.error(f"Error output: {result.stderr}")
            return False, duration, output
        
        logger.info(f"Reporting script completed successfully in {duration:.2f}s")
        return True, duration, output

    except subprocess.TimeoutExpired:
        duration = time.time() - start_time
        logger.error(f"Reporting script timed out after {REPORT_RENDER_BUDGET_SECONDS}s")
        return False, duration, "Timeout: Script exceeded time budget"
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Error running reporting script: {str(e)}")
        return False, duration, str(e)

def verify_report_artifacts():
    """
    Verify that the expected report artifacts were created.
    
    Returns:
        bool: True if artifacts exist, False otherwise
    """
    artifacts_exist = True
    
    # Check for Markdown report
    if REPORT_MARKDOWN.exists():
        file_size = REPORT_MARKDOWN.stat().st_size
        logger.info(f"Markdown report exists: {REPORT_MARKDOWN} ({file_size} bytes)")
    else:
        logger.warning(f"Markdown report not found: {REPORT_MARKDOWN}")
        artifacts_exist = False
    
    # Check for PDF report (if generated)
    if REPORT_PDF.exists():
        file_size = REPORT_PDF.stat().st_size
        logger.info(f"PDF report exists: {REPORT_PDF} ({file_size} bytes)")
    else:
        logger.info(f"PDF report not generated (optional): {REPORT_PDF}")
        # PDF generation might be optional depending on environment
        # We consider the task successful if Markdown is generated
    
    return artifacts_exist

def validate_report_rendering():
    """
    Main validation function for report rendering.
    
    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    logger.info("=" * 60)
    logger.info("Starting Report Rendering Validation")
    logger.info("=" * 60)
    logger.info(f"Time Budget: {REPORT_RENDER_BUDGET_SECONDS} seconds")
    logger.info(f"Output Directory: {REPORT_OUTPUT_DIR}")
    
    # Ensure output directory exists
    ensure_output_directory()
    
    # Run the reporting script
    success, duration, output = run_reporting_script()
    
    if not success:
        logger.error("Report generation failed!")
        logger.error(f"Duration: {duration:.2f}s")
        return 1
    
    # Verify artifacts were created
    if not verify_report_artifacts():
        logger.error("Report artifacts not found!")
        return 1
    
    # Check if within time budget
    if duration > REPORT_RENDER_BUDGET_SECONDS:
        logger.error(f"Report generation exceeded time budget!")
        logger.error(f"Duration: {duration:.2f}s > Budget: {REPORT_RENDER_BUDGET_SECONDS}s")
        return 1
    
    logger.info("=" * 60)
    logger.info("VALIDATION SUCCESSFUL")
    logger.info(f"Report generated in {duration:.2f}s (within {REPORT_RENDER_BUDGET_SECONDS}s budget)")
    logger.info(f"Markdown: {REPORT_MARKDOWN}")
    if REPORT_PDF.exists():
        logger.info(f"PDF: {REPORT_PDF}")
    logger.info("=" * 60)
    
    return 0

def main():
    """Entry point for the validation script."""
    exit_code = validate_report_rendering()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()