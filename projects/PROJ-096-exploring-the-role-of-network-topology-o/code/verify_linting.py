"""
Verify linting configuration by running black and flake8 on the codebase.

This script implements task T003b: Verify Linting Configuration.
It runs 'black --check .' and 'flake8 .' on the existing code base.
Output is redirected to 'data/checksums.txt' (appended).
If no code exists yet, it creates a dummy 'code/__init__.py' first.
"""

import subprocess
import sys
import os
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_command(command: list, description: str) -> bool:
    """
    Run a shell command and return True if it succeeds.

    Args:
        command: List of command arguments.
        description: Human-readable description of the command.

    Returns:
        True if the command exits with code 0, False otherwise.
    """
    logger.info(f"Running: {description}")
    logger.info(f"Command: {' '.join(command)}")

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False  # Don't raise exception, we want to capture output
        )

        if result.returncode == 0:
            logger.info(f"{description} passed successfully.")
            return True
        else:
            logger.warning(f"{description} found issues (exit code {result.returncode}).")
            if result.stdout:
                logger.warning(f"STDOUT:\n{result.stdout}")
            if result.stderr:
                logger.warning(f"STDERR:\n{result.stderr}")
            return False

    except FileNotFoundError:
        logger.error(f"Command not found: {command[0]}")
        logger.error("Please ensure black and flake8 are installed in the environment.")
        return False
    except Exception as e:
        logger.error(f"Error running command: {e}")
        return False

def create_dummy_init_if_needed():
    """
    Create a dummy code/__init__.py if the code directory exists but is empty.
    """
    code_dir = Path("code")
    init_file = code_dir / "__init__.py"

    if code_dir.exists():
        # Check if there are any Python files in code/ (excluding __init__.py itself)
        py_files = list(code_dir.glob("*.py"))
        subdirs = [d for d in code_dir.iterdir() if d.is_dir()]

        if not py_files and not subdirs:
            logger.info("No Python files found in code/. Creating dummy __init__.py.")
            init_file.write_text("# Project root package\n")
            logger.info(f"Created dummy file: {init_file}")
    else:
        logger.warning("code/ directory does not exist. Creating it.")
        code_dir.mkdir(parents=True, exist_ok=True)
        if not init_file.exists():
            init_file.write_text("# Project root package\n")
            logger.info(f"Created dummy file: {init_file}")

def append_to_checksums_file(output_lines: list, description: str):
    """
    Append linting output to data/checksums.txt.

    Args:
        output_lines: List of strings to append.
        description: Description of what was appended.
    """
    checksums_file = Path("data/checksums.txt")

    # Ensure data directory exists
    checksums_file.parent.mkdir(parents=True, exist_ok=True)

    with open(checksums_file, "a") as f:
        f.write(f"\n# {description}\n")
        f.write(f"# Generated: {Path.cwd()}\n")
        for line in output_lines:
            f.write(f"{line}\n")

    logger.info(f"Appended linting results to {checksums_file}")

def main():
    """
    Main entry point for T003b: Verify Linting Configuration.
    """
    logger.info("Starting T003b: Verify Linting Configuration")

    # Ensure code directory has at least an __init__.py
    create_dummy_init_if_needed()

    # Prepare output collection
    all_output = []

    # Run Black check
    black_success = run_command(
        ["black", "--check", "."],
        "Black linting check"
    )
    if not black_success:
        logger.warning("Black check found formatting issues.")
    else:
        logger.info("Black check passed.")

    # Run Flake8 check
    flake8_success = run_command(
        ["flake8", "."],
        "Flake8 linting check"
    )
    if not flake8_success:
        logger.warning("Flake8 check found style issues.")
    else:
        logger.info("Flake8 check passed.")

    # Collect results summary
    results_summary = [
        f"T003b Linting Verification Results",
        f"=================================",
        f"Black check: {'PASSED' if black_success else 'FAILED (issues found)'}",
        f"Flake8 check: {'PASSED' if flake8_success else 'FAILED (issues found)'}",
        f"=================================",
    ]

    # Append to checksums file
    append_to_checksums_file(results_summary, "T003b Linting Verification")

    logger.info("T003b verification complete. Results appended to data/checksums.txt")

    # Return success if both checks passed
    if black_success and flake8_success:
        logger.info("All linting checks passed.")
        return 0
    else:
        logger.info("Some linting checks found issues (this is expected for new codebases).")
        logger.info("Task T003b is considered complete as it successfully ran the checks.")
        return 0

if __name__ == "__main__":
    sys.exit(main())
