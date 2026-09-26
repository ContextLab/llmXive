"""
T008b: Validate presence of multabench_baselines.csv.

This script validates the presence of the required baseline file
`data/raw/multabench_baselines.csv`. If the file is missing or empty,
it logs an ERROR to stderr and exits with code 1. It does NOT generate
synthetic data or attempt to parse external links.
"""

import os
import sys
import logging
from pathlib import Path

# Configure logging to stderr with ERROR level as the minimum for this script
logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s",
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

def main() -> int:
    """
    Validate the presence of the baseline file.

    Returns:
        int: 0 if file exists and is non-empty, 1 otherwise.
    """
    # Define the path relative to the project root
    # Assuming this script runs from the project root or code/pipelines/
    project_root = Path(__file__).resolve().parent.parent
    baseline_path = project_root / "data" / "raw" / "multabench_baselines.csv"

    if not baseline_path.exists():
        logger.error(
            "Missing required baseline file: data/raw/multabench_baselines.csv. "
            "Please refer to data/README.md for acquisition steps."
        )
        return 1

    # Check if file is empty
    if baseline_path.stat().st_size == 0:
        logger.error(
            "Missing required baseline file: data/raw/multabench_baselines.csv. "
            "Please refer to data/README.md for acquisition steps."
        )
        return 1

    logger.info(
        f"Baseline file validated successfully: {baseline_path} "
        f"(size: {baseline_path.stat().st_size} bytes)"
    )
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)