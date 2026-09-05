"""
Setup script for linting (ruff) and formatting (black) tools.
This script verifies installation and runs basic validation checks.
"""
import os
import sys
import subprocess
from pathlib import Path
from typing import Tuple, Optional

# Ensure code directory is in path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.logging import get_logger

logger = get_logger(__name__)

def run_command(command: list[str], description: str) -> Tuple[bool, str]:
    """Run a shell command and return success status and output."""
    logger.info(f"Running: {description}")
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
            cwd=project_root
        )
        logger.info(f"Success: {description}")
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed: {description}\nError: {e.stderr}")
        return False, str(e)

def ensure_tool_installed(tool_name: str) -> bool:
    """Check if a tool is installed and accessible."""
    try:
        subprocess.run(
            [tool_name, "--version"],
            check=True,
            capture_output=True,
            text=True
        )
        logger.info(f"Tool '{tool_name}' is installed.")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.error(f"Tool '{tool_name}' is not installed or not in PATH.")
        logger.info(f"Please install it via: pip install {tool_name}")
        return False

def validate_config() -> bool:
    """Validate that configuration files exist and are readable."""
    pyproject_path = project_root / "pyproject.toml"
    if not pyproject_path.exists():
        logger.error("pyproject.toml not found. Please ensure configuration exists.")
        return False

    logger.info("Configuration file 'pyproject.toml' found and readable.")
    return True

def main() -> int:
    """Main entry point for linting setup."""
    logger.info("Starting linting and formatting configuration validation...")

    # Check configurations
    if not validate_config():
        return 1

    # Check tools
    tools = ["ruff", "black"]
    all_installed = True
    for tool in tools:
        if not ensure_tool_installed(tool):
            all_installed = False

    if not all_installed:
        logger.warning("Some tools are missing. Run 'pip install ruff black' to fix.")
        return 1

    # Run basic validation: check that ruff can parse the code directory
    logger.info("Running 'ruff check code/' to verify configuration...")
    success, output = run_command(
        ["ruff", "check", "code/"],
        "Ruff lint check on code directory"
    )
    # Ruff returns 0 if clean, 1 if issues found. We treat issues as warnings for setup,
    # but we want to ensure the command runs successfully.
    if success or "Found" in output: # Ruff often exits 1 if issues found, which is okay for setup
         logger.info("Ruff check executed successfully.")
    else:
         logger.error("Ruff check failed to execute.")
         return 1

    logger.info("Running 'black --check code/' to verify formatting configuration...")
    success, output = run_command(
        ["black", "--check", "code/"],
        "Black format check on code directory"
    )
    if success or "would reformat" in output:
        logger.info("Black check executed successfully.")
    else:
        logger.error("Black check failed to execute.")
        return 1

    logger.info("Linting and formatting configuration validated successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
