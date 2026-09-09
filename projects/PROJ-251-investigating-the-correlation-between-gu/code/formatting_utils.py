"""
Formatting utilities for linting and code style enforcement.

This module provides helper functions for running ruff and black formatting
tools on the codebase.
"""
import subprocess
import sys
import os
from pathlib import Path
from typing import Tuple, Optional
import logging

from utils.logging_config import get_logger

logger = get_logger(__name__)

def run_command(cmd: list, capture_output: bool = True, timeout: int = 300) -> Tuple[int, str, str]:
    """
    Run a shell command and return (return_code, stdout, stderr).
    
    Args:
        cmd: Command as a list of strings
        capture_output: Whether to capture stdout/stderr
        timeout: Command timeout in seconds
        
    Returns:
        Tuple of (return_code, stdout, stderr)
    """
    logger.debug(f"Running command: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            capture_output=capture_output,
            text=True,
            timeout=timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        logger.error(f"Command timed out: {' '.join(cmd)}")
        return -1, "", "Command timed out"
    except Exception as e:
        logger.error(f"Error running command: {e}")
        return -1, "", str(e)

def run_ruff_check_and_fix(code_dir: Path) -> bool:
    """
    Run ruff check on code directory and attempt to fix issues.
    
    Args:
        code_dir: Path to the code directory
        
    Returns:
        True if all issues were fixed or no issues found, False otherwise
    """
    logger.info("Running ruff check with auto-fix...")
    
    # Try to fix issues
    fix_cmd = [sys.executable, "-m", "ruff", "check", str(code_dir), "--fix"]
    returncode, stdout, stderr = run_command(fix_cmd)
    
    if returncode != 0:
        logger.warning(f"Ruff found issues that could not be auto-fixed:\n{stdout}")
    
    # Verify with a check-only run
    check_cmd = [sys.executable, "-m", "ruff", "check", str(code_dir)]
    returncode_check, stdout_check, _ = run_command(check_cmd)
    
    if returncode_check == 0:
        logger.info("Ruff check passed after fixes")
        return True
    else:
        logger.error(f"Ruff check failed:\n{stdout_check}")
        return False

def run_black_format(code_dir: Path) -> bool:
    """
    Run black format on code directory.
    
    Args:
        code_dir: Path to the code directory
        
    Returns:
        True if formatting succeeded, False otherwise
    """
    logger.info("Running black format...")
    
    format_cmd = [sys.executable, "-m", "black", str(code_dir)]
    returncode, stdout, stderr = run_command(format_cmd)
    
    if returncode == 0:
        logger.info("Black formatting completed successfully")
        return True
    else:
        logger.error(f"Black formatting failed:\n{stdout}\n{stderr}")
        return False

def main():
    """
    Main entry point for formatting utilities.
    """
    logger.info("Formatting utilities module loaded")
    return 0

if __name__ == "__main__":
    sys.exit(main())