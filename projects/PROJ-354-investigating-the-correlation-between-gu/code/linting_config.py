"""
Linting and formatting configuration and execution utilities.
Provides functions to validate environment, run formatters, and run linters.
"""
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import json
import logging

# Import project logger utility
from utils.logging import get_logger

logger = get_logger(__name__)

def get_black_config() -> Dict[str, Any]:
    """
    Return the Black configuration parameters used in this project.
    """
    return {
        "line_length": 88,
        "target_version": "py310",
        "quote_style": "double",
        "exclude_patterns": [".git", ".venv", "data", "results"],
    }

def get_ruff_config() -> Dict[str, Any]:
    """
    Return the Ruff configuration parameters used in this project.
    """
    return {
        "select": ["E", "W", "F", "I", "C", "B", "UP", "N"],
        "ignore": ["E501", "B008", "C901"],
        "exclude": [".git", "__pycache__", ".venv", "data/", "results/"],
    }

def validate_environment() -> bool:
    """
    Validate that required tools (ruff, black) are installed and accessible.
    Returns True if valid, False otherwise.
    """
    tools = ["ruff", "black"]
    for tool in tools:
        try:
            result = subprocess.run(
                [tool, "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                text=True,
            )
            logger.info(f"Found {tool}: {result.stdout.strip()}")
        except subprocess.CalledProcessError:
            logger.error(f"Tool {tool} not found or not executable.")
            return False
        except FileNotFoundError:
            logger.error(f"Tool {tool} not found in PATH.")
            return False
    return True

def run_formatter(file_paths: Optional[List[str]] = None, check_only: bool = False) -> bool:
    """
    Run Black formatter on the specified files or the whole project.

    Args:
        file_paths: List of file paths to format. If None, formats the whole project.
        check_only: If True, only check formatting without modifying files.

    Returns:
        True if formatting succeeded (or check passed), False otherwise.
    """
    cmd = ["black"]
    if check_only:
        cmd.append("--check")
        cmd.append("--diff")
    else:
        cmd.append("--quiet")

    if file_paths:
        cmd.extend(file_paths)
    else:
        # Default to formatting code and tests directories
        cmd.extend(["code", "tests"])

    logger.info(f"Running formatter: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            text=True,
        )
        if result.stdout:
            logger.info(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        if check_only:
            logger.warning("Formatting check failed. Run 'black .' to fix.")
            if e.stdout:
                logger.warning(e.stdout)
            return False
        logger.error(f"Formatter failed: {e.stderr}")
        return False

def run_linter(file_paths: Optional[List[str]] = None, fix: bool = False) -> bool:
    """
    Run Ruff linter on the specified files or the whole project.

    Args:
        file_paths: List of file paths to lint. If None, lints the whole project.
        fix: If True, attempt to automatically fix issues.

    Returns:
        True if linting passed (no errors), False otherwise.
    """
    cmd = ["ruff"]
    if fix:
        cmd.append("--fix")
    else:
        cmd.append("--output-format=concise")

    if file_paths:
        cmd.extend(file_paths)
    else:
        # Default to linting code and tests directories
        cmd.extend(["code", "tests"])

    logger.info(f"Running linter: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            text=True,
        )
        if result.stdout:
            logger.info(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        # Ruff returns non-zero exit code if issues are found
        logger.warning("Linting issues found:")
        if e.stdout:
            logger.warning(e.stdout)
        if e.stderr:
            logger.error(e.stderr)
        return False

def init_logging() -> None:
    """
    Initialize logging for the linting module.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

def main() -> None:
    """
    Main entry point for running linting and formatting checks.
    Usage: python -m code.linting_config [--fix] [--check-only]
    """
    import argparse

    parser = argparse.ArgumentParser(description="Run linters and formatters.")
    parser.add_argument(
        "--fix", action="store_true", help="Attempt to automatically fix linting issues."
    )
    parser.add_argument(
        "--check-only", action="store_true", help="Only check formatting, do not modify files."
    )
    parser.add_argument(
        "--files", nargs="+", help="Specific files to process."
    )

    args = parser.parse_args()

    init_logging()

    # Validate environment first
    if not validate_environment():
        logger.error("Environment validation failed. Please install required tools (ruff, black).")
        sys.exit(1)

    # Run formatter
    logger.info("Running Black formatter...")
    format_ok = run_formatter(
        file_paths=args.files, check_only=args.check_only
    )

    # Run linter
    logger.info("Running Ruff linter...")
    lint_ok = run_linter(file_paths=args.files, fix=args.fix)

    if format_ok and lint_ok:
        logger.info("All checks passed successfully.")
        sys.exit(0)
    else:
        logger.error("Some checks failed. Please review the output above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
