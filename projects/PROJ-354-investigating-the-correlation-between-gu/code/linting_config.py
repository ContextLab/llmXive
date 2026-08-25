"""
Linting and Formatting Configuration and Execution Utilities.

This module provides functions to validate environment, retrieve configurations
for Black and Ruff, and execute the formatters/linters on the project codebase.
"""
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import json
import logging

from code.utils.logging import get_logger

logger = get_logger(__name__)


def get_black_config() -> Dict[str, Any]:
    """
    Returns the Black configuration as a dictionary based on pyproject.toml.
    In a real execution, this would parse the file, but here we return the
    expected defaults defined in the project's pyproject.toml.
    """
    return {
        "line_length": 88,
        "target_version": "py310",
        "exclude": [
            ".eggs", ".git", ".hg", ".mypy_cache", ".tox", ".venv",
            "_build", "buck-out", "build", "dist"
        ]
    }


def get_ruff_config() -> Dict[str, Any]:
    """
    Returns the Ruff configuration as a dictionary based on pyproject.toml.
    """
    return {
        "line_length": 88,
        "target_version": "py310",
        "select": ["E", "W", "F", "I", "B", "C4", "UP"],
        "ignore": ["E501", "B008", "C901"],
        "exclude": [
            ".bzr", ".direnv", ".eggs", ".git", ".hg", ".mypy_cache",
            ".nox", ".pants.d", ".ruff_cache", ".svn", ".tox", ".venv",
            "__pypackages__", "_build", "buck-out", "build", "dist",
            "node_modules", "venv"
        ]
    }


def validate_environment() -> bool:
    """
    Checks if required tools (black, ruff) are installed and accessible.
    Returns True if environment is valid, False otherwise.
    """
    tools = ["black", "ruff"]
    for tool in tools:
        try:
            result = subprocess.run(
                [sys.executable, "-m", tool, "--version"],
                capture_output=True,
                text=True,
                check=True
            )
            logger.info(f"{tool} is available: {result.stdout.strip()}")
        except subprocess.CalledProcessError:
            logger.error(f"{tool} is not installed or not in PATH.")
            return False
        except FileNotFoundError:
            logger.error(f"{tool} executable not found.")
            return False
    return True


def run_formatter(target: Optional[str] = None) -> bool:
    """
    Runs the Black formatter on the codebase.
    If target is None, formats the entire 'code/' directory.
    """
    if target is None:
        target = "code/"

    logger.info(f"Running Black formatter on: {target}")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "black", target],
            capture_output=True,
            text=True,
            check=True
        )
        if result.stdout:
            logger.info(result.stdout)
        if result.stderr:
            logger.warning(result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Black formatting failed: {e.stderr}")
        return False


def run_linter(target: Optional[str] = None) -> bool:
    """
    Runs the Ruff linter on the codebase.
    If target is None, lints the entire 'code/' directory.
    """
    if target is None:
        target = "code/"

    logger.info(f"Running Ruff linter on: {target}")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "check", target],
            capture_output=True,
            text=True,
            check=False  # Ruff returns 1 if issues found, which is expected
        )
        if result.stdout:
            logger.warning("Ruff found issues:\n%s", result.stdout)
        if result.stderr:
            logger.error("Ruff error:\n%s", result.stderr)
        
        # Return True if no issues found (exit code 0), False otherwise
        return result.returncode == 0
    except FileNotFoundError:
        logger.error("Ruff executable not found. Please install it.")
        return False


def init_logging():
    """Initializes the logging configuration for this module."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def main():
    """
    Main entry point for running linting and formatting checks.
    """
    init_logging()
    
    logger.info("Starting Linting/Formatting Validation...")
    
    if not validate_environment():
        logger.error("Environment validation failed. Please install required tools.")
        sys.exit(1)
    
    logger.info("Environment valid.")
    
    # Run formatter
    if run_formatter():
        logger.info("Formatting completed successfully.")
    else:
        logger.error("Formatting failed.")
    
    # Run linter
    if run_linter():
        logger.info("Linting passed: No issues found.")
    else:
        logger.warning("Linting found issues. Please review the output above.")
    
    logger.info("Linting/Formatting process finished.")


if __name__ == "__main__":
    main()