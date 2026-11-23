import os
import sys
import subprocess
import logging
from pathlib import Path

from config import setup_logging

logger = logging.getLogger(__name__)

def run_command(cmd: str) -> int:
    """Runs a command and returns exit code."""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error(f"Command failed: {cmd}\n{result.stderr}")
    return result.returncode

def main():
    setup_logging()
    logger.info("Running pipeline validation...")
    
    # Run validation steps
    steps = [
        "python code/validate_baseline.py",
        "python code/verify_results.py"
    ]
    
    for step in steps:
        if run_command(step) != 0:
            sys.exit(1)
    
    logger.info("Pipeline validation completed.")

if __name__ == "__main__":
    main()
