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

def run_command(command: list, description: str) -> bool:
    """
    Execute a shell command and log the result.
    
    Args:
        command: List of command arguments
        description: Description of what the command does
        
    Returns:
        True if command succeeded, False otherwise
    """
    logger.info(f"Running: {description}")
    logger.debug(f"Command: {' '.join(command)}")
    
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True
        )
        if result.stdout:
            logger.debug(f"Output: {result.stdout}")
        logger.info(f"Success: {description}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed: {description}")
        logger.error(f"Error: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error running {description}: {str(e)}")
        return False

def check_linting() -> bool:
    """
    Check code for linting issues using ruff.
    
    Returns:
        True if no linting issues found, False otherwise
    """
    logger.info("Checking linting with ruff...")
    
    # Check if ruff is installed
    if not run_command([sys.executable, "-m", "ruff", "--version"], "Checking ruff availability"):
        logger.error("Ruff is not installed. Please install it with: pip install ruff")
        return False
    
    # Run ruff check on the code directory
    code_dir = Path("code")
    if not code_dir.exists():
        logger.warning("Code directory does not exist. Skipping linting check.")
        return True
    
    return run_command(
        [sys.executable, "-m", "ruff", "check", str(code_dir)],
        "Linting check with ruff"
    )

def check_formatting() -> bool:
    """
    Check code formatting using black.
    
    Returns:
        True if formatting is correct, False otherwise
    """
    logger.info("Checking formatting with black...")
    
    # Check if black is installed
    if not run_command([sys.executable, "-m", "black", "--version"], "Checking black availability"):
        logger.error("Black is not installed. Please install it with: pip install black")
        return False
    
    # Run black check on the code directory
    code_dir = Path("code")
    if not code_dir.exists():
        logger.warning("Code directory does not exist. Skipping formatting check.")
        return True
    
    return run_command(
        [sys.executable, "-m", "black", "--check", str(code_dir)],
        "Formatting check with black"
    )

def fix_linting() -> bool:
    """
    Fix linting issues using ruff.
    
    Returns:
        True if issues were fixed or no issues found, False otherwise
    """
    logger.info("Fixing linting issues with ruff...")
    
    # Check if ruff is installed
    if not run_command([sys.executable, "-m", "ruff", "--version"], "Checking ruff availability"):
        logger.error("Ruff is not installed. Please install it with: pip install ruff")
        return False
    
    # Run ruff check --fix on the code directory
    code_dir = Path("code")
    if not code_dir.exists():
        logger.warning("Code directory does not exist. Skipping linting fix.")
        return True
    
    return run_command(
        [sys.executable, "-m", "ruff", "check", "--fix", str(code_dir)],
        "Fixing linting issues with ruff"
    )

def fix_formatting() -> bool:
    """
    Fix formatting issues using black.
    
    Returns:
        True if issues were fixed or no issues found, False otherwise
    """
    logger.info("Fixing formatting issues with black...")
    
    # Check if black is installed
    if not run_command([sys.executable, "-m", "black", "--version"], "Checking black availability"):
        logger.error("Black is not installed. Please install it with: pip install black")
        return False
    
    # Run black on the code directory
    code_dir = Path("code")
    if not code_dir.exists():
        logger.warning("Code directory does not exist. Skipping formatting fix.")
        return True
    
    return run_command(
        [sys.executable, "-m", "black", str(code_dir)],
        "Fixing formatting issues with black"
    )

def main():
    """
    Main function to run linting and formatting checks and fixes.
    """
    logger.info("=" * 60)
    logger.info("Starting Linting and Formatting Configuration")
    logger.info("=" * 60)
    
    # Check current state
    lint_ok = check_linting()
    format_ok = check_formatting()
    
    if lint_ok and format_ok:
        logger.info("All checks passed! Code is properly linted and formatted.")
        return 0
    
    logger.warning("Some checks failed. Attempting to fix...")
    
    # Try to fix issues
    fix_linting()
    fix_formatting()
    
    # Re-check after fixes
    lint_ok = check_linting()
    format_ok = check_formatting()
    
    if lint_ok and format_ok:
        logger.info("All issues have been fixed successfully!")
        return 0
    else:
        logger.error("Some issues could not be fixed automatically. Please review the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
