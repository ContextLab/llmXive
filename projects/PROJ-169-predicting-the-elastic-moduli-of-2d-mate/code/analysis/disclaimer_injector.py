"""
Disclaimer Injector for Feature Importance Report.

This module ensures that the final feature importance report explicitly states
that the identified descriptors are statistical correlations learned by the surrogate
model, not fundamental quantum mechanical variables.
"""
import os
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

from analysis.report_generator import generate_markdown_report, load_json_file

logger = logging.getLogger(__name__)

# The exact required disclaimer text
REQUIRED_DISCLAIMER = (
    "The identified descriptors are statistical correlations learned by the "
    "surrogate model from DFT data, not fundamental quantum mechanical variables "
    "derived from the Hamiltonian."
)

def inject_disclaimer_into_report(report_path: Path) -> bool:
    """
    Ensure the report at `report_path` contains the required disclaimer.

    If the file exists and is a Markdown file, we check if the disclaimer
    is present. If not, we prepend it to the file content.

    Returns True if the file was modified or already compliant, False on error.
    """
    if not report_path.exists():
        logger.error(f"Report file not found: {report_path}")
        return False

    content = report_path.read_text(encoding="utf-8")

    if REQUIRED_DISCLAIMER in content:
        logger.info("Disclaimer already present in report.")
        return True

    logger.info(f"Injecting disclaimer into {report_path}")

    # Prepend the disclaimer as a clear section
    disclaimer_section = f"## Important Note on Descriptor Interpretation\n\n{REQUIRED_DISCLAIMER}\n\n"
    new_content = disclaimer_section + content

    report_path.write_text(new_content, encoding="utf-8")
    logger.info("Disclaimer successfully injected.")
    return True

def main():
    parser = argparse.ArgumentParser(
        description="Ensure feature importance report contains required disclaimer."
    )
    parser.add_argument(
        "--report-path",
        type=str,
        default="data/results/feature_importance_report.md",
        help="Path to the feature importance report markdown file.",
    )
    args = parser.parse_args()

    report_path = Path(args.report_path)

    if not inject_disclaimer_into_report(report_path):
        logger.error("Failed to ensure disclaimer is present.")
        return 1

    logger.info("Task completed successfully.")
    return 0

if __name__ == "__main__":
    exit(main())