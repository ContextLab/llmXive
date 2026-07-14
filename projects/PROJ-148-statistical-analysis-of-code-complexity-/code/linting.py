"""
Linting utilities for the llmXive project.
Provides functions to run flake8 and check for PEP8 compliance.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Tuple, Optional

from utils.logging import get_logger

logger = get_logger(__name__)


def run_flake8(target_path: str = "code") -> Tuple[bool, str]:
    """
    Run flake8 on the specified directory and return the result.

    Args:
        target_path: Path to the directory to lint (default: "code").

    Returns:
        A tuple (success, output) where:
            - success is True if no violations were found, False otherwise.
            - output contains the full flake8 output or a summary message.
    """
    path = Path(target_path)
    if not path.exists():
        msg = f"Target path does not exist: {path}"
        logger.error(msg)
        return False, msg

    logger.info(f"Running flake8 on {path}...")

    # Construct the flake8 command
    # We exclude .venv, __pycache__, and build artifacts if they exist in code/
    exclude = ".venv,__pycache__,build,dist,*.egg-info"
    cmd = [
        sys.executable,
        "-m",
        "flake8",
        "--max-line-length=120",
        f"--exclude={exclude}",
        str(path),
        "--show-source",
        "--statistics",
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )
        output = result.stdout + result.stderr

        if result.returncode == 0:
            logger.info("flake8 passed: No PEP8 violations found.")
            return True, "No violations found."
        else:
            logger.warning(f"flake8 found {result.returncode} issues (or errors).")
            logger.warning("Output:\n" + output)
            return False, output

    except FileNotFoundError:
        msg = "flake8 not found. Please install it via: pip install flake8"
        logger.error(msg)
        return False, msg
    except Exception as e:
        msg = f"Error running flake8: {e}"
        logger.error(msg)
        return False, msg


def verify_pep8_compliance(target_path: str = "code") -> bool:
    """
    Verify that the codebase is PEP8 compliant using flake8.

    Args:
        target_path: Path to the directory to check.

    Returns:
        True if compliant, False otherwise.
    """
    success, _ = run_flake8(target_path)
    return success


def main() -> int:
    """
    Entry point for running flake8 verification.

    Returns:
        Exit code: 0 if compliant, 1 if violations found or error occurred.
    """
    target = "code"
    success, output = run_flake8(target)

    if success:
        print(f"✓ PEP8 compliance verified for '{target}'.")
        return 0
    else:
        print(f"✗ PEP8 violations found in '{target}':")
        print(output)
        return 1


if __name__ == "__main__":
    sys.exit(main())
