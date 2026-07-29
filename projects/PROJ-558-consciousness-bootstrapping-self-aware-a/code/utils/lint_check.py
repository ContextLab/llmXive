"""
Lint and formatting check utilities for the Consciousness Bootstrapping project.

This module provides functions to run ruff and black checks on the codebase
and report any violations. It is designed to be used in CI pipelines to ensure
code quality.
"""

import subprocess
import sys
import os
from pathlib import Path
from utils.logging import get_logger

logger = get_logger(__name__)

def run_command(command: list, check: bool = True) -> tuple:
    """
    Run a shell command and return the result.
    
    Args:
        command: List of command arguments
        check: If True, raise CalledProcessError on non-zero exit
        
    Returns:
        Tuple of (return_code, stdout, stderr)
    """
    try:
        logger.info(f"Running command: {' '.join(command)}")
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=check
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed with return code {e.returncode}")
        logger.error(f"stdout: {e.stdout}")
        logger.error(f"stderr: {e.stderr}")
        return e.returncode, e.stdout, e.stderr

def check_ruff(code_dir: Path) -> bool:
    """
    Run ruff check on the specified directory.
    
    Args:
        code_dir: Path to the code directory to check
        
    Returns:
        True if no lint errors found, False otherwise
    """
    command = ["ruff", "check", str(code_dir)]
    returncode, stdout, stderr = run_command(command, check=False)
    
    if returncode == 0:
        logger.info("Ruff check passed: No lint errors found")
        return True
    else:
        logger.error("Ruff check failed:")
        logger.error(stdout)
        if stderr:
            logger.error(stderr)
        return False

def check_black(code_dir: Path) -> bool:
    """
    Run black --check on the specified directory.
    
    Args:
        code_dir: Path to the code directory to check
        
    Returns:
        True if formatting is correct, False otherwise
    """
    command = ["black", "--check", str(code_dir)]
    returncode, stdout, stderr = run_command(command, check=False)
    
    if returncode == 0:
        logger.info("Black check passed: Code is properly formatted")
        return True
    else:
        logger.error("Black check failed:")
        logger.error(stdout)
        if stderr:
            logger.error(stderr)
        return False

def main() -> int:
    """
    Main entry point for lint and format checking.
    
    Runs both ruff and black checks on the code/ directory.
    Exits with non-zero code if any check fails.
    """
    # Determine the project root (parent of the code directory)
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent
    code_dir = project_root / "code"
    
    if not code_dir.exists():
        logger.error(f"Code directory not found: {code_dir}")
        sys.exit(1)
    
    logger.info(f"Checking code in directory: {code_dir}")
    
    ruff_passed = check_ruff(code_dir)
    black_passed = check_black(code_dir)
    
    if ruff_passed and black_passed:
        logger.info("All lint and format checks passed!")
        sys.exit(0)
    else:
        logger.error("One or more checks failed. Please fix the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
