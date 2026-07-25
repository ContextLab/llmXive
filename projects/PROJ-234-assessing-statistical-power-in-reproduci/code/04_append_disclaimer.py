"""
Task T035: Append mandatory disclaimer to the audit report.

This script reads the generated audit report (audit_report.md),
appends the mandatory disclaimer text required by the specification,
and writes the updated content back to the same file.
"""

import os
import sys
from pathlib import Path
import logging

# Ensure logging is configured if not already done by the parent pipeline
try:
    from utils.logging_config import setup_logging
    logger = setup_logging("append_disclaimer")
except ImportError:
    # Fallback if running directly without full path setup
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(name)s %(message)s'
    )
    logger = logging.getLogger(__name__)

# Define the paths relative to the project root
# The script expects to be run from the project root or code/ directory
# We resolve the base path to ensure we find data/processed/audit_report.md
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
report_path = project_root / "data" / "processed" / "audit_report.md"

DISCLAIMER_TEXT = """
**Disclaimer:** Observed power is a monotone function of the p‑value and should not be used for post‑hoc validation (Hoenig & Heisey).

The research question is to determine whether observed power is appropriate for post‑hoc validation. The method involves a theoretical analysis of the monotonic relationship between observed power and p‑values.
"""

def append_disclaimer(report_path: Path) -> bool:
    """
    Appends the mandatory disclaimer to the end of the audit report.

    Args:
        report_path: Path to the audit_report.md file.

    Returns:
        True if successful, False otherwise.
    """
    if not report_path.exists():
        logger.error(f"Report file not found: {report_path}")
        return False

    try:
        # Read existing content
        with open(report_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Ensure content ends with a newline before appending
        if not content.endswith('\n'):
            content += '\n'

        # Append the disclaimer
        new_content = content + DISCLAIMER_TEXT

        # Write back
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        logger.info(f"Disclaimer successfully appended to {report_path}")
        return True

    except IOError as e:
        logger.error(f"IOError while processing report: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False

def main():
    """Main entry point for the script."""
    logger.info(f"Starting disclaimer append process for {report_path}")
    
    if not report_path.exists():
        logger.error("Cannot proceed: audit_report.md does not exist. "
                     "Please ensure code/04_generate_report.py has run successfully first.")
        sys.exit(1)

    success = append_disclaimer(report_path)
    
    if success:
        logger.info("Task T035 completed successfully.")
        sys.exit(0)
    else:
        logger.error("Task T035 failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()