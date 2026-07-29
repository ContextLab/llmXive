"""
Lint and format checking utilities for the Consciousness Bootstrapping project.

This module provides functions to run ruff and black checks on the codebase.
It is designed to be used in CI pipelines to ensure code quality.
"""

import subprocess
import sys
import os
from pathlib import Path
from utils.logging import get_logger

logger = get_logger(__name__)


def run_command(command: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """
    Run a shell command and return the result.

    Args:
        command: List of command arguments.
        check: If True, raise CalledProcessError on non-zero exit.

    Returns:
        CompletedProcess instance.
    """
    logger.info(f"Running command: {' '.join(command)}")
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=check
        )
        return result
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed with return code {e.returncode}")
        if e.stdout:
            logger.error(f"STDOUT:\n{e.stdout}")
        if e.stderr:
            logger.error(f"STDERR:\n{e.stderr}")
        raise


def check_ruff(code_dir: Path) -> bool:
    """
    Run ruff check on the specified directory.

    Args:
        code_dir: Path to the code directory to check.

    Returns:
        True if check passes, False otherwise.
    """
    logger.info(f"Running ruff check on {code_dir}")
    try:
        # Run ruff check with exit code 1 on errors
        run_command(["ruff", "check", str(code_dir)], check=True)
        logger.info("ruff check passed")
        return True
    except subprocess.CalledProcessError:
        logger.error("ruff check failed")
        return False


def check_black(code_dir: Path) -> bool:
    """
    Run black --check on the specified directory.

    Args:
        code_dir: Path to the code directory to check.

    Returns:
        True if check passes, False otherwise.
    """
    logger.info(f"Running black --check on {code_dir}")
    try:
        # Run black --check (does not modify files, exits 1 if formatting needed)
        run_command(["black", "--check", str(code_dir)], check=True)
        logger.info("black --check passed")
        return True
    except subprocess.CalledProcessError:
        logger.error("black --check failed")
        return False


def main() -> int:
    """
    Main entry point for lint checking.

    Runs ruff and black checks on the code/ directory.
    Returns 0 if all checks pass, 1 otherwise.
    """
    project_root = Path(__file__).parent.parent
    code_dir = project_root / "code"

    if not code_dir.exists():
        logger.error(f"Code directory not found: {code_dir}")
        return 1

    logger.info(f"Starting lint checks on {code_dir}")

    ruff_passed = check_ruff(code_dir)
    black_passed = check_black(code_dir)

    if ruff_passed and black_passed:
        logger.info("All lint checks passed")
        return 0
    else:
        logger.error("One or more lint checks failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
