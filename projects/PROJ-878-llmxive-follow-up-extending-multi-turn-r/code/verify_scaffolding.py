"""
verify_scaffolding.py

This script provides the missing verification for task T001:
1. Installs the project's Python dependencies via `pip install -r code/requirements.txt`.
2. Runs `ruff check --output-format=concise` to ensure linting passes with exit code 0.
It logs success or raises an exception on failure, causing the script to exit non‑zero.
"""

import subprocess
import sys
from pathlib import Path

from llmxive_toolkit import get_logger, paths

logger = get_logger(__name__)

def run_command(command: list, description: str) -> None:
    """Execute a command, logging output and raising on non‑zero exit."""
    logger.info(f"Running: {' '.join(command)}")
    result = subprocess.run(command, capture_output=True, text=True)
    if result.stdout:
        logger.debug(f"{description} stdout:\\n{result.stdout}")
    if result.stderr:
        logger.debug(f"{description} stderr:\\n{result.stderr}")
    if result.returncode != 0:
        logger.error(f"{description} failed with exit code {result.returncode}")
        raise RuntimeError(f"{description} failed (exit {result.returncode})")
    logger.info(f"{description} succeeded (exit 0)")

def main() -> None:
    # 1. Install dependencies
    requirements_path = Path("code/requirements.txt")
    if not requirements_path.is_file():
        logger.error(f"Requirements file not found at {requirements_path}")
        sys.exit(1)

    run_command(
        [sys.executable, "-m", "pip", "install", "-r", str(requirements_path)],
        "pip install"
    )

    # 2. Run ruff lint check
    # ruff is installed as a project dependency; invoke it via the module entry point.
    run_command(
        [sys.executable, "-m", "ruff", "check", "--output-format=concise", "."],
        "ruff lint"
    )

    logger.info("Scaffolding verification completed successfully.")

if __name__ == "__main__":
    main()
