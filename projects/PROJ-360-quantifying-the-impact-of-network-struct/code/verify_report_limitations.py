"""
Task T026: Verify final report contains mandatory 'Limitations' text.

This script checks that `results/final_report.md` exists and contains
the exact mandatory text specified in FR-008.
"""
import os
import sys
import logging
from pathlib import Path
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("verify_report_limitations")

REPORT_PATH = Path("results/final_report.md")
MANDATORY_TEXT = (
    "This study is observational. Correlations do not imply causality. "
    "The thermal conductivity tensor was reduced to a scalar by averaging "
    "principal components, which may obscure anisotropic effects."
)

def verify_report() -> bool:
    """
    Verify that the final report exists and contains the mandatory limitations text.
    
    Returns:
        bool: True if verification passes, False otherwise.
    """
    if not REPORT_PATH.exists():
        logger.error(f"Report file not found: {REPORT_PATH}")
        return False

    try:
        content = REPORT_PATH.read_text(encoding='utf-8')
    except Exception as e:
        logger.error(f"Failed to read report file: {e}")
        return False

    if MANDATORY_TEXT in content:
        logger.info("SUCCESS: Mandatory 'Limitations' text found in final report.")
        return True
    else:
        logger.error("FAILURE: Mandatory 'Limitations' text NOT found in final report.")
        logger.error(f"Expected text: {MANDATORY_TEXT}")
        # Log a snippet of the actual content for debugging
        lines = content.split('\n')
        logger.error(f"Report content (first 10 lines):\n" + "\n".join(lines[:10]))
        return False

def main() -> None:
    """Main entry point."""
    logger.info(f"Verifying report at: {REPORT_PATH}")
    success = verify_report()
    if not success:
        sys.exit(1)
    else:
        print("Verification passed.")
        sys.exit(0)

if __name__ == "__main__":
    main()