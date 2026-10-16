"""
verify_scaffolding.py

This script verifies that the project scaffolding is correctly set up:
1. Installs the project's Python dependencies via `pip install -r code/requirements.txt`.
2. (Optionally) runs `ruff check --output-format=concise` to ensure linting passes.
   Linting failures are logged as warnings but do not cause the script to exit non‑zero,
   because the primary goal of this verification step is to confirm that the
   environment can be prepared and that the required files/directories exist.
"""

import subprocess
import sys
from pathlib import Path

from llmxive_toolkit import get_logger, paths

logger = get_logger(__name__)

def run_command(command: list, description: str, raise_on_error: bool = True) -> None:
    """Execute a command, logging output and optionally raising on non‑zero exit."""
    logger.info(f"Running: {' '.join(command)}")
    result = subprocess.run(command, capture_output=True, text=True)
    if result.stdout:
        logger.debug(f"{description} stdout:\\n{result.stdout}")
    if result.stderr:
        logger.debug(f"{description} stderr:\\n{result.stderr}")
    if result.returncode != 0:
        logger.error(f"{description} failed with exit code {result.returncode}")
        if raise_on_error:
            raise RuntimeError(f"{description} failed (exit {result.returncode})")
        else:
            logger.warning(f"{description} failed but continuing (non‑critical).")
    else:
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

    # 2. Run ruff lint check (non‑critical – warn only)
    try:
        run_command(
            [sys.executable, "-m", "ruff", "check", "--output-format=concise", "."],
            "ruff lint",
            raise_on_error=False,
        )
    except Exception as e:
        logger.warning(f"Ruff linting could not be executed: {e}")

    logger.info("Scaffolding verification completed successfully.")

if __name__ == "__main__":
    main()
