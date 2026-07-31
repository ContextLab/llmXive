"""
Type Checking Utility for llmXive Project.

This module provides functionality to run mypy type checking on the codebase
and enforce strict type checking as a hard block for the 'Polish' phase.
"""
import subprocess
import sys
import os
from pathlib import Path
import logging
from typing import List, Optional, Dict, Any

from utils.config import get_project_root, get_path, ensure_dir

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_mypy_check() -> int:
    """
    Run mypy type checking on the code/ directory.

    This function executes mypy with strict settings on the project's code directory.
    If mypy returns a non-zero exit code (including type warnings), the function
    writes the output to data/processed/type_log.txt and returns the exit code.

    Returns:
        int: The exit code from mypy (0 for success, non-zero for failure)
    """
    project_root = get_project_root()
    code_dir = project_root / "code"
    output_path = project_root / "data" / "processed" / "type_log.txt"

    # Ensure output directory exists
    ensure_dir(output_path.parent)

    logger.info(f"Running mypy type check on {code_dir}...")
    logger.info(f"Output will be written to {output_path}")

    # Construct mypy command with strict settings
    # --strict enables all strict flags
    # --ignore-missing-imports to handle external libraries not having stubs
    # --explicit-package-bases to handle package structure
    cmd = [
        sys.executable, "-m", "mypy",
        str(code_dir),
        "--strict",
        "--ignore-missing-imports",
        "--explicit-package-bases",
        "--show-error-codes",
        "--pretty"
    ]

    logger.info(f"Executing: {' '.join(cmd)}")

    try:
        # Run mypy and capture output
        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )

        # Write output to log file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("=== MYPI TYPE CHECK LOG ===\n")
            f.write(f"Command: {' '.join(cmd)}\n")
            f.write(f"Return Code: {result.returncode}\n")
            f.write("=" * 50 + "\n\n")

            if result.stdout:
                f.write("STDOUT:\n")
                f.write(result.stdout)
                f.write("\n")

            if result.stderr:
                f.write("STDERR:\n")
                f.write(result.stderr)
                f.write("\n")

            if result.returncode == 0:
                f.write("\n=== TYPE CHECK PASSED ===\n")
                logger.info("Type check passed successfully!")
            else:
                f.write("\n=== TYPE CHECK FAILED ===\n")
                logger.error(f"Type check failed with return code {result.returncode}")

        return result.returncode

    except subprocess.TimeoutExpired:
        logger.error("mypy check timed out after 300 seconds")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("=== MYPI TYPE CHECK LOG ===\n")
            f.write("ERROR: Type check timed out after 300 seconds\n")
        return 1
    except FileNotFoundError:
        logger.error("mypy not found. Please install it with: pip install mypy")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("=== MYPI TYPE CHECK LOG ===\n")
            f.write("ERROR: mypy not found. Please install it with: pip install mypy\n")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during type check: {e}")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("=== MYPI TYPE CHECK LOG ===\n")
            f.write(f"ERROR: Unexpected error - {e}\n")
        return 1


def main() -> int:
    """
    Main entry point for the type checking utility.

    This function runs the mypy type check and exits with the appropriate code.
    If mypy returns a non-zero exit code, the pipeline MUST fail immediately.

    Returns:
        int: The exit code from mypy (0 for success, non-zero for failure)
    """
    logger.info("Starting type check (T031b)...")

    exit_code = run_mypy_check()

    if exit_code != 0:
        logger.error("Type check failed. Pipeline must fail immediately.")
        logger.error("Please fix all type errors and warnings before proceeding.")
    else:
        logger.info("Type check passed. Pipeline can proceed.")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
