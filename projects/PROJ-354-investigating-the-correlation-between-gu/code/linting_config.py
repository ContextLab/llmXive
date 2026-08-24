"""
Linting and Formatting Configuration and Execution Utilities.

This module provides functions to configure, run, and validate
ruff, black, and flake8 within the project environment.
"""
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import json
import logging

from utils.logging import get_logger, LlmXiveError

logger = get_logger(__name__)


def get_black_config() -> Dict[str, Any]:
    """Return the effective Black configuration based on pyproject.toml."""
    return {
        "line-length": 88,
        "target-version": ["py310"],
        "include": r"\.pyi?$",
    }


def get_ruff_config() -> Dict[str, Any]:
    """Return the effective Ruff configuration based on pyproject.toml."""
    return {
        "line-length": 88,
        "target-version": "py310",
        "select": ["E", "W", "F", "I", "B", "C4", "UP"],
        "ignore": ["E501", "B008", "C901"],
    }


def run_formatter(tool: str = "black", paths: Optional[List[str]] = None) -> bool:
    """
    Run the specified formatter on the project code.

    Args:
        tool: Either 'black' or 'ruff' (format mode).
        paths: List of paths to format. Defaults to current directory.

    Returns:
        True if successful, False otherwise.
    """
    if paths is None:
        paths = [str(Path.cwd())]

    cmd = []
    if tool == "black":
        cmd = [sys.executable, "-m", "black"]
    elif tool == "ruff":
        # Ruff format is available in newer versions, fallback to check if needed
        # Using ruff format command if available, otherwise ruff check --fix
        cmd = [sys.executable, "-m", "ruff", "format"]
    else:
        logger.error(f"Unknown formatter tool: {tool}")
        return False

    cmd.extend(paths)

    logger.info(f"Running {tool} formatter: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode == 0:
            logger.info(f"{tool} formatting completed successfully.")
            return True
        else:
            logger.warning(f"{tool} found issues or failed:\n{result.stdout}\n{result.stderr}")
            return False
    except FileNotFoundError:
        logger.error(f"Tool '{tool}' not found. Please install it via requirements.txt.")
        return False
    except Exception as e:
        logger.error(f"Error running {tool}: {e}")
        return False


def run_linter(tool: str = "ruff", paths: Optional[List[str]] = None) -> bool:
    """
    Run the specified linter on the project code.

    Args:
        tool: Either 'ruff' or 'flake8'.
        paths: List of paths to lint. Defaults to current directory.

    Returns:
        True if successful (no errors found), False otherwise.
    """
    if paths is None:
        paths = [str(Path.cwd())]

    cmd = []
    if tool == "ruff":
        cmd = [sys.executable, "-m", "ruff", "check"]
    elif tool == "flake8":
        cmd = [sys.executable, "-m", "flake8"]
    else:
        logger.error(f"Unknown linter tool: {tool}")
        return False

    cmd.extend(paths)

    logger.info(f"Running {tool} linter: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode == 0:
            logger.info(f"{tool} linting passed (no issues found).")
            return True
        else:
            logger.warning(f"{tool} found issues:\n{result.stdout}\n{result.stderr}")
            return False
    except FileNotFoundError:
        logger.error(f"Tool '{tool}' not found. Please install it via requirements.txt.")
        return False
    except Exception as e:
        logger.error(f"Error running {tool}: {e}")
        return False


def validate_environment() -> bool:
    """
    Validate that all required linting and formatting tools are installed.

    Returns:
        True if all tools are available, False otherwise.
    """
    tools = ["black", "ruff", "flake8"]
    missing = []

    for tool in tools:
        try:
            subprocess.run(
                [sys.executable, "-m", tool, "--version"],
                capture_output=True,
                check=True,
            )
            logger.info(f"Tool '{tool}' is installed.")
        except subprocess.CalledProcessError:
            missing.append(tool)
            logger.warning(f"Tool '{tool}' is NOT installed.")
        except FileNotFoundError:
            missing.append(tool)
            logger.warning(f"Tool '{tool}' is NOT installed.")

    if missing:
        logger.error(f"Missing required tools: {', '.join(missing)}. Run: pip install {' '.join(missing)}")
        return False

    return True


def main() -> int:
    """
    Main entry point for linting configuration validation and execution.

    Usage:
        python -m code.linting_config --check
        python -m code.linting_config --format
        python -m code.linting_config --lint

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    import argparse

    parser = argparse.ArgumentParser(description="Linting and Formatting Utilities")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Validate that tools are installed.",
    )
    parser.add_argument(
        "--format",
        action="store_true",
        help="Run formatters (black, ruff format).",
    )
    parser.add_argument(
        "--lint",
        action="store_true",
        help="Run linters (ruff, flake8).",
    )
    parser.add_argument(
        "--paths",
        nargs="+",
        default=None,
        help="Paths to run tools on (default: current directory).",
    )

    args = parser.parse_args()

    if not any([args.check, args.format, args.lint]):
        parser.print_help()
        return 1

    # Initialize logging
    init_logging()

    if args.check:
        if validate_environment():
            logger.info("Environment validation passed.")
            return 0
        else:
            logger.error("Environment validation failed.")
            return 1

    success = True

    if args.format:
        logger.info("Running formatters...")
        if not run_formatter("black", args.paths):
            success = False
        if not run_formatter("ruff", args.paths):
            success = False

    if args.lint:
        logger.info("Running linters...")
        if not run_linter("ruff", args.paths):
            success = False
        if not run_linter("flake8", args.paths):
            success = False

    return 0 if success else 1


def init_logging():
    """Initialize basic logging for the module."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

if __name__ == "__main__":
    sys.exit(main())