import os
import sys
import subprocess
import json
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import load_paths
from utils.logging import setup_logging, get_logger

logger = get_logger(__name__)

def run_step(step_name):
    """Run a specific pipeline step."""
    result = subprocess.run(
        [sys.executable, f"code/{step_name}.py"],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        logger.error(f"Step {step_name} failed: {result.stderr}")
        return False
    return True

def main():
    setup_logging()
    steps = ["ingest", "descriptors", "train", "evaluate", "importance", "plots"]
    for step in steps:
        logger.info(f"Running validation for {step}")
        if not run_step(step):
            sys.exit(1)
    logger.info("All steps passed validation.")

if __name__ == "__main__":
    main()
