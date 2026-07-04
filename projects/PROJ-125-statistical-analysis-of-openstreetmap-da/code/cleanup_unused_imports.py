"""
Script to remove unused imports and dead code from the project's Python files.
This script uses `ruff` to identify unused imports and `black` to format code.
"""

import os
import subprocess
import sys
from pathlib import Path

from utils.logging import get_main_logger

logger = get_main_logger()

def run_command(cmd: list[str], cwd: Path | None = None) -> None:
    """Run a shell command and log output."""
    logger.info(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
        )
        if result.stdout:
            logger.info(result.stdout)
        if result.stderr:
            logger.warning(result.stderr)
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {e}")
        logger.error(f"stderr: {e.stderr}")
        raise

def main() -> int:
    """Main entry point for cleanup."""
    project_root = Path(__file__).resolve().parent.parent
    code_dir = project_root / "code"

    if not code_dir.exists():
        logger.error(f"Code directory not found: {code_dir}")
        return 1

    logger.info(f"Starting cleanup in {code_dir}")

    # 1. Run ruff check to fix unused imports and other fixable issues
    # --fix: Automatically fix issues
    # --exit-zero: Don't fail if issues remain (some might be unfixable)
    try:
        run_command(
            ["ruff", "check", "--fix", "--exit-zero", str(code_dir)],
            cwd=project_root,
        )
    except subprocess.CalledProcessError:
        logger.warning("Ruff check had issues that couldn't be fixed automatically.")

    # 2. Run ruff format (or black) to format code
    # Using ruff format if available, otherwise fall back to black
    try:
        run_command(
            ["ruff", "format", str(code_dir)],
            cwd=project_root,
        )
    except FileNotFoundError:
        logger.info("ruff format not available, trying black...")
        try:
            run_command(
                ["black", str(code_dir)],
                cwd=project_root,
            )
        except FileNotFoundError:
            logger.warning("Neither ruff format nor black found. Skipping formatting.")
        except subprocess.CalledProcessError:
            logger.warning("Black formatting failed.")
    except subprocess.CalledProcessError:
        logger.warning("Ruff formatting failed.")

    logger.info("Cleanup complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
