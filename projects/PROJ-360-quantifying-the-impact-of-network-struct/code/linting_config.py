"""
Linting and formatting configuration runner.
Provides functions to execute Black, isort, Flake8, and Pylint checks.
"""
import subprocess
import sys
import os
from typing import List, Tuple, Optional
import logging
from pathlib import Path

# Configure logger
logger = logging.getLogger(__name__)

def run_command(cmd: List[str], description: str) -> Tuple[bool, str]:
    """
    Run a shell command and capture output.

    Args:
        cmd: List of command arguments.
        description: Human-readable description of the action.

    Returns:
        Tuple of (success: bool, message: str).
    """
    logger.info(f"Running {description}...")
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
            cwd=Path(__file__).parent.parent
        )

        if result.returncode == 0:
            logger.info(f"{description} completed successfully.")
            return True, "Success"
        else:
            error_msg = result.stderr.strip() if result.stderr else result.stdout.strip()
            logger.error(f"{description} failed with code {result.returncode}: {error_msg}")
            return False, error_msg

    except FileNotFoundError:
        logger.error(f"Command not found: {cmd[0]}. Is it installed?")
        return False, f"Command not found: {cmd[0]}"
    except Exception as e:
        logger.error(f"Error running {description}: {str(e)}")
        return False, str(e)

def setup_tools() -> bool:
    """
    Verify that required linting tools are installed.

    Returns:
        True if all tools are found, False otherwise.
    """
    tools = ["black", "isort", "flake8", "pylint"]
    missing = []

    for tool in tools:
        try:
            subprocess.run(
                [tool, "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
            logger.debug(f"Found {tool}")
        except subprocess.CalledProcessError:
            missing.append(tool)
        except FileNotFoundError:
            missing.append(tool)

    if missing:
        logger.error(f"Missing required tools: {', '.join(missing)}. Install via: pip install {' '.join(missing)}")
        return False

    logger.info("All linting tools are available.")
    return True

def run_black() -> bool:
    """Run Black formatter in check mode."""
    # Run black to format code first (optional, but good practice)
    success, _ = run_command(
        ["black", "--line-length", "100", "code/"],
        "Black formatter (format)"
    )
    if not success:
        return False

    # Run black in check mode to verify
    success, msg = run_command(
        ["black", "--check", "--line-length", "100", "code/"],
        "Black formatter (check)"
    )
    return success

def run_isort() -> bool:
    """Run isort to sort imports."""
    success, _ = run_command(
        ["isort", "code/"],
        "isort (format)"
    )
    if not success:
        return False

    success, msg = run_command(
        ["isort", "--check-only", "code/"],
        "isort (check)"
    )
    return success

def run_flake8() -> bool:
    """Run Flake8 linter."""
    success, msg = run_command(
        ["flake8", "code/"],
        "Flake8 linter"
    )
    return success

def run_pylint() -> bool:
    """Run Pylint linter."""
    success, msg = run_command(
        ["pylint", "code/"],
        "Pylint linter"
    )
    return success

def main() -> int:
    """
    Main entry point for running linting and formatting checks.

    Returns:
        Exit code: 0 if all checks pass, 1 otherwise.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

    logger.info("Starting linting and formatting checks...")

    if not setup_tools():
        logger.error("Tool setup failed. Aborting.")
        return 1

    checks = [
        ("isort", run_isort),
        ("black", run_black),
        ("flake8", run_flake8),
        ("pylint", run_pylint),
    ]

    all_passed = True
    for name, check_func in checks:
        if not check_func():
            logger.error(f"{name} check failed.")
            all_passed = False
        else:
            logger.info(f"{name} check passed.")

    if all_passed:
        logger.info("All linting and formatting checks passed.")
        return 0
    else:
        logger.error("Some checks failed. Please fix the issues.")
        return 1

if __name__ == "__main__":
    sys.exit(main())