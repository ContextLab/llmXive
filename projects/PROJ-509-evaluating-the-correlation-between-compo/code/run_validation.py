import os
import sys
import subprocess
import json
import logging
from pathlib import Path

from config import load_paths

logger = logging.getLogger(__name__)


def run_step(step_name: str) -> bool:
    """Run a pipeline step and return success."""
    cmd = [sys.executable, f"code/{step_name}.py"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logger.info(f"Step {step_name} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Step {step_name} failed: {e.stderr}")
        return False


def main() -> None:
    """Main entry point for validation."""
    logging.basicConfig(level=logging.INFO)
    paths = load_paths()

    steps = ["ingest", "descriptors", "evaluate", "importance"]
    for step in steps:
        if not run_step(step):
            logger.error(f"Validation failed at step: {step}")
            sys.exit(1)

    logger.info("All validation steps passed")


if __name__ == "__main__":
    main()
