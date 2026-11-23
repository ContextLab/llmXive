"""
Code cleanup and formatting utilities for the llmXive pipeline.

This module provides functions to run black and flake8 checks
and automatically format code to meet project standards.
"""
import subprocess
import sys
import os
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_command(command: list, description: str = "") -> bool:
    """
    Run a shell command and return success status.
    
    Args:
        command: List of command arguments
        description: Optional description for logging
        
    Returns:
        True if command succeeded, False otherwise
    """
    cmd_str = ' '.join(command)
    if description:
        logger.info(f"Running: {description}")
    else:
        logger.info(f"Running: {cmd_str}")
        
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            logger.info("Success")
            return True
        else:
            logger.error(f"Command failed with return code {result.returncode}")
            if result.stdout:
                logger.error(f"STDOUT:\n{result.stdout}")
            if result.stderr:
                logger.error(f"STDERR:\n{result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Exception running command: {e}")
        return False


def format_code_with_black() -> bool:
    """
    Format all Python files in the code/ directory using black.
    
    Returns:
        True if formatting succeeded, False otherwise
    """
    logger.info("Starting code formatting with black...")
    
    # Check if black is installed
    try:
        subprocess.run(
            [sys.executable, "-m", "black", "--version"],
            capture_output=True,
            check=True
        )
    except subprocess.CalledProcessError:
        logger.error("black is not installed. Installing...")
        install_result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "black"],
            capture_output=True,
            text=True
        )
        if install_result.returncode != 0:
            logger.error(f"Failed to install black: {install_result.stderr}")
            return False
    
    # Run black on the code directory
    success = run_command(
        [sys.executable, "-m", "black", "code/"],
        "Formatting code/ directory with black"
    )
    
    return success


def check_with_flake8() -> bool:
    """
    Check code quality with flake8.
    
    Returns:
        True if no errors found, False otherwise
    """
    logger.info("Running flake8 code quality check...")
    
    # Check if flake8 is installed
    try:
        subprocess.run(
            [sys.executable, "-m", "flake8", "--version"],
            capture_output=True,
            check=True
        )
    except subprocess.CalledProcessError:
        logger.error("flake8 is not installed. Installing...")
        install_result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "flake8"],
            capture_output=True,
            text=True
        )
        if install_result.returncode != 0:
            logger.error(f"Failed to install flake8: {install_result.stderr}")
            return False
    
    # Run flake8 on the code directory
    success = run_command(
        [sys.executable, "-m", "flake8", "code/"],
        "Checking code quality with flake8"
    )
    
    return success


def main():
    """
    Main entry point for code cleanup and formatting.
    
    This function:
    1. Formats all Python files with black
    2. Runs flake8 to verify code quality
    3. Returns appropriate exit code
    """
    logger.info("=" * 60)
    logger.info("Starting code cleanup and formatting (T038)")
    logger.info("=" * 60)
    
    # Step 1: Format with black
    black_success = format_code_with_black()
    if not black_success:
        logger.error("Black formatting failed")
        sys.exit(1)
    
    # Step 2: Check with flake8
    flake8_success = check_with_flake8()
    if not flake8_success:
        logger.error("flake8 check failed")
        sys.exit(1)
    
    logger.info("=" * 60)
    logger.info("Code cleanup and formatting completed successfully!")
    logger.info("All files pass black formatting and flake8 checks.")
    logger.info("=" * 60)
    
    sys.exit(0)


if __name__ == "__main__":
    main()
