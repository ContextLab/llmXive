"""
Quickstart validation script.

This script programmatically executes the commands listed in ``quickstart.md``
to ensure that the full pipeline runs end‑to‑end within the CI time budget
(60 minutes). It records the total wall‑clock time and writes a small
validation report to ``data/processed/quickstart_validation.txt``.
"""

import subprocess
import time
from pathlib import Path
import sys
import logging

# Import the shared utilities for consistent logging configuration.
from utils import setup_logging, get_logger

# Configure logging for this script.
logger = setup_logging()
logger = get_logger(__name__)

# Define the commands that constitute the pipeline (mirroring quickstart.md).
PIPELINE_COMMANDS = [
    ["python", "code/download.py"],
    ["python", "code/filter.py"],
    ["python", "code/fingerprints.py"],
    ["python", "code/split.py"],
    ["python", "code/train.py"],
    ["python", "code/evaluate.py"],
]

# Path to the validation report.
REPORT_PATH = Path("data/processed/quickstart_validation.txt")

def run_command(cmd):
    """Run a command via subprocess, streaming output to the logger."""
    cmd_str = " ".join(cmd)
    logger.info(f"Executing: {cmd_str}")
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    # Log command output (useful for debugging CI failures).
    for line in result.stdout.splitlines():
        logger.debug(line)

    if result.returncode != 0:
        logger.error(f"Command failed with exit code {result.returncode}: {cmd_str}")
        raise subprocess.CalledProcessError(
            result.returncode, cmd, output=result.stdout
        )
    logger.info(f"Command succeeded: {cmd_str}")

def main():
    start_time = time.time()
    try:
        for cmd in PIPELINE_COMMANDS:
            run_command(cmd)
    except subprocess.CalledProcessError as e:
        # Write a failure report and exit with a non‑zero status.
        total_seconds = time.time() - start_time
        report = (
            f"Pipeline validation FAILED after {total_seconds:.1f}s.\n"
            f"Failed command: {' '.join(e.cmd)}\n"
            f"Exit code: {e.returncode}\n"
        )
        REPORT_PATH.write_text(report)
        logger.error(report)
        sys.exit(1)

    total_seconds = time.time() - start_time
    # CI time budget: 60 minutes = 3600 seconds.
    within_budget = total_seconds <= 3600
    status = "SUCCESS" if within_budget else "TIMEOUT"

    report = (
        f"Pipeline validation {status}.\n"
        f"Total wall‑clock time: {total_seconds:.1f} seconds.\n"
        f"Time budget (60 min): 3600 seconds.\n"
    )
    REPORT_PATH.write_text(report)
    logger.info(report)

    # Exit with non‑zero status if the time budget was exceeded.
    if not within_budget:
        sys.exit(1)

if __name__ == "__main__":
    main()
