"""
Script to run linting (ruff) and formatting checks (black) on the project.
It writes a concise log file under the results directory indicating success.
The script exits with a non‑zero status if any check fails, causing the task
verification to fail.
"""

import subprocess
import sys
from pathlib import Path

# Import toolkit helpers for consistent path handling and logging
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def run_command(command: list[str], description: str) -> None:
    """Run a shell command, log its output, and raise on failure."""
    log.info(f"Running {description}: {' '.join(command)}")
    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        log.error(f"{description} failed with exit code {result.returncode}")
        log.error(f"Output:\n{result.stdout}")
        raise RuntimeError(f"{description} failed")
    else:
        log.info(f"{description} succeeded.")
        log.debug(f"Output:\n{result.stdout}")

def main() -> int:
    """
    Execute ruff and black checks.
    The log is written to <project>/results/lint_check.log.
    """
    try:
        # Run ruff linting
        run_command(["ruff", "check", "."], "ruff linting")

        # Run black formatting check
        run_command(["black", "--check", "."], "black formatting check")

        # Write a simple success marker file
        success_path: Path = paths.results("lint_check.log")
        success_path.parent.mkdir(parents=True, exist_ok=True)
        with success_path.open("w") as f:
            f.write("ruff and black checks passed successfully.\n")
        log.info(f"Lint check log written to {success_path}")

        return 0
    except Exception as e:
        log.exception("Linting/formatting verification failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())