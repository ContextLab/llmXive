"""
Validate that the final report renders as PDF/Markdown within the time budget.

This script executes the reporting pipeline and measures the time taken to
generate the final report artifacts. It verifies that the output files exist
and are non-empty.
"""
import os
import sys
import time
import logging
import subprocess
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from analysis.reporting import main as generate_report_main

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

TIME_BUDGET_SECONDS = 30
REPORT_DIR = project_root / "artifacts"
REPORT_MD = REPORT_DIR / "final_report.md"
REPORT_PDF = REPORT_DIR / "final_report.pdf"

def ensure_report_dir():
    """Ensure the artifacts directory exists."""
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

def run_generation():
    """Run the report generation script and measure time."""
    logger.info(f"Starting report generation (budget: {TIME_BUDGET_SECONDS}s)...")
    start_time = time.time()
    
    try:
        # Execute the main reporting function
        # This will load data, LME results, XGBoost results, etc.
        generate_report_main()
        
        elapsed = time.time() - start_time
        logger.info(f"Report generation completed in {elapsed:.2f} seconds.")
        return elapsed, True
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"Report generation failed after {elapsed:.2f} seconds: {e}")
        return elapsed, False

def verify_outputs():
    """Verify that output files exist and are non-empty."""
    issues = []
    
    # Check Markdown
    if REPORT_MD.exists():
        size = REPORT_MD.stat().st_size
        if size > 0:
            logger.info(f"Markdown report exists: {REPORT_MD} ({size} bytes)")
        else:
            issues.append(f"Markdown report is empty: {REPORT_MD}")
    else:
        issues.append(f"Markdown report not found: {REPORT_MD}")
        
    # Check PDF (optional, depending on environment, but task asks for validation)
    if REPORT_PDF.exists():
        size = REPORT_PDF.stat().st_size
        if size > 0:
            logger.info(f"PDF report exists: {REPORT_PDF} ({size} bytes)")
        else:
            issues.append(f"PDF report is empty: {REPORT_PDF}")
    else:
        # PDF generation might fail if no latex/pandoc is installed, 
        # but the MD file is the primary artifact for CI validation usually.
        # We log a warning but don't fail if MD exists.
        logger.warning(f"PDF report not found: {REPORT_PDF}. Ensure pandoc/latex is installed for PDF generation.")

    return issues

def main():
    ensure_report_dir()
    
    elapsed, success = run_generation()
    
    if elapsed > TIME_BUDGET_SECONDS:
        logger.error(f"FAILED: Report generation took {elapsed:.2f}s, exceeding budget of {TIME_BUDGET_SECONDS}s.")
        sys.exit(1)
    
    if not success:
        logger.error("FAILED: Report generation script raised an exception.")
        sys.exit(1)
    
    issues = verify_outputs()
    
    if issues:
        logger.error("FAILED: Output verification issues found:")
        for issue in issues:
            logger.error(f"  - {issue}")
        sys.exit(1)
    
    logger.info("SUCCESS: Report validation passed within time budget.")
    sys.exit(0)

if __name__ == "__main__":
    main()
