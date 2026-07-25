"""
Verification script for T040.
Ensures that the sampling and power analysis was run and the report exists.
"""
import os
import sys
import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    report_path = Path("state/power_analysis_report.json")
    summary_path = Path("docs/analysis_summary.md")

    if not report_path.exists():
        logger.error(f"Verification failed: {report_path} does not exist.")
        return 1

    if not summary_path.exists():
        logger.error(f"Verification failed: {summary_path} does not exist.")
        return 1

    with open(report_path, 'r') as f:
        report = json.load(f)

    if "issues" not in report:
        logger.error("Verification failed: Report missing 'issues' key.")
        return 1

    if "recommendations" not in report:
        logger.error("Verification failed: Report missing 'recommendations' key.")
        return 1

    with open(summary_path, 'r') as f:
        summary_content = f.read()

    if "Statistical Power and Sampling Analysis" not in summary_content:
        logger.error("Verification failed: Summary missing power analysis section.")
        return 1

    logger.info("Verification passed: T040 artifacts are present and valid.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
