"""
Linting and formatting verification utilities for the Consciousness Bootstrapping project.

This module provides functions to run `ruff check` and `black --check`
on the project's codebase, ensuring adherence to style and linting standards.
"""

import subprocess
import sys
import os
from pathlib import Path
from utils.logging import get_logger

logger = get_logger(__name__)


def run_command(command: list[str], cwd: Path | None = None) -> tuple[int, str, str]:
    """
    Execute a shell command and return its exit code, stdout, and stderr.

    Args:
        command: List of command arguments.
        cwd: Working directory for the command.

    Returns:
        Tuple of (exit_code, stdout, stderr).
    """
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False
        )
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        logger.error(f"Command not found: {command[0]}")
        return 127, "", f"Command not found: {command[0]}"
    except Exception as e:
        logger.error(f"Error executing command: {e}")
        return 1, "", str(e)


def check_ruff(code_dir: Path) -> bool:
    """
    Run `ruff check` on the specified directory.

    Args:
        code_dir: Path to the directory to check.

    Returns:
        True if the check passes (no errors), False otherwise.
    """
    logger.info(f"Running ruff check on {code_dir}...")
    command = ["ruff", "check", str(code_dir)]
    exit_code, stdout, stderr = run_command(command)

    if exit_code == 0:
        logger.info("ruff check passed successfully.")
        return True
    else:
        logger.error("ruff check failed.")
        if stdout:
            logger.error(f"stdout:\n{stdout}")
        if stderr:
            logger.error(f"stderr:\n{stderr}")
        return False


def check_black(code_dir: Path) -> bool:
    """
    Run `black --check` on the specified directory.

    Args:
        code_dir: Path to the directory to check.

    Returns:
        True if the check passes (no formatting issues), False otherwise.
    """
    logger.info(f"Running black --check on {code_dir}...")
    command = ["black", "--check", str(code_dir)]
    exit_code, stdout, stderr = run_command(command)

    if exit_code == 0:
        logger.info("black --check passed successfully.")
        return True
    else:
        logger.error("black --check failed.")
        if stdout:
            logger.error(f"stdout:\n{stdout}")
        if stderr:
            logger.error(f"stderr:\n{stderr}")
        return False


def main() -> int:
    """
    Main entry point for the lint check script.

    Runs both ruff and black checks on the 'code' directory relative to the
    project root. Exits with code 1 if any check fails, 0 otherwise.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    # Determine project root (assumed to be the directory containing this script's parent)
    # The script is at code/utils/lint_check.py, so project root is 3 levels up?
    # Actually, tasks.md says "code/" is at repository root.
    # Let's assume the script is run from the project root or we find the 'code' dir.
    # A robust way: look for 'code' directory relative to this file's location.
    script_path = Path(__file__).resolve()
    # Assuming structure: project_root/code/utils/lint_check.py
    project_root = script_path.parent.parent.parent
    code_dir = project_root / "code"

    if not code_dir.exists():
        logger.error(f"Code directory not found: {code_dir}")
        return 1

    logger.info(f"Project root: {project_root}")
    logger.info(f"Checking code directory: {code_dir}")

    ruff_ok = check_ruff(code_dir)
    black_ok = check_black(code_dir)

    if ruff_ok and black_ok:
        logger.info("All linting and formatting checks passed.")
        return 0
    else:
        logger.error("One or more linting/formatting checks failed.")
        if not ruff_ok:
            logger.error("  - ruff check failed")
        if not black_ok:
            logger.error("  - black check failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())