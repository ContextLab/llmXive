import subprocess
import sys
from pathlib import Path
import logging
from config import setup_logging

def run_flake8_check():
    """
    Runs flake8 check on the code/ directory.
    Returns True if the check passes (exit code 0), False otherwise.
    """
    logger = logging.getLogger(__name__)
    logger.info("Running flake8 check...")
    
    code_dir = Path(__file__).parent
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "flake8", str(code_dir)],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            logger.info("flake8 check passed.")
            return True
        else:
            logger.warning(f"flake8 found issues:\n{result.stdout}{result.stderr}")
            return False
    except FileNotFoundError:
        logger.error("flake8 not found. Please install it via pip install flake8.")
        return False
    except Exception as e:
        logger.error(f"Unexpected error running flake8: {e}")
        return False

def run_black_check():
    """
    Runs black check on the code/ directory.
    Returns True if the code is formatted correctly, False otherwise.
    """
    logger = logging.getLogger(__name__)
    logger.info("Running black check...")
    
    code_dir = Path(__file__).parent
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "black", "--check", str(code_dir)],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            logger.info("black check passed. Code is formatted correctly.")
            return True
        else:
            logger.warning("black check failed. Code needs formatting.")
            return False
    except FileNotFoundError:
        logger.error("black not found. Please install it via pip install black.")
        return False
    except Exception as e:
        logger.error(f"Unexpected error running black check: {e}")
        return False

def run_black_format():
    """
    Runs black formatter on the code/ directory.
    Returns True if formatting succeeds, False otherwise.
    """
    logger = logging.getLogger(__name__)
    logger.info("Running black formatter...")
    
    code_dir = Path(__file__).parent
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "black", str(code_dir)],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            logger.info("black formatting completed successfully.")
            return True
        else:
            logger.error(f"black formatting failed: {result.stderr}")
            return False
    except FileNotFoundError:
        logger.error("black not found. Please install it via pip install black.")
        return False
    except Exception as e:
        logger.error(f"Unexpected error running black format: {e}")
        return False

def format_code():
    """
    Runs autoflake, then black to clean up and format code.
    Returns True if all steps succeed, False otherwise.
    """
    logger = logging.getLogger(__name__)
    logger.info("Starting code formatting process...")
    
    # Step 1: Remove unused imports
    if not run_autoflake():
        logger.error("Failed to remove unused imports. Stopping formatting process.")
        return False
    
    # Step 2: Format with black
    if not run_black_format():
        logger.error("Failed to format code with black. Stopping formatting process.")
        return False
    
    logger.info("Code formatting process completed successfully.")
    return True

def run_all_checks():
    """
    Runs flake8 and black checks.
    Returns True if all checks pass, False otherwise.
    """
    logger = logging.getLogger(__name__)
    logger.info("Running all linting checks...")
    
    flake8_ok = run_flake8_check()
    black_ok = run_black_check()
    
    if flake8_ok and black_ok:
        logger.info("All linting checks passed.")
        return True
    else:
        logger.warning("Some linting checks failed.")
        return False

def run_autoflake():
    """
    Runs autoflake on all Python files in the code/ directory to remove unused imports.
    Returns True if the command exits with code 0, False otherwise.
    """
    logger = logging.getLogger(__name__)
    logger.info("Running autoflake to remove unused imports...")
    
    code_dir = Path(__file__).parent
    
    try:
        # Run autoflake with in-place modification and remove-all-unused-imports
        result = subprocess.run(
            [
                sys.executable, "-m", "autoflake",
                "--in-place",
                "--remove-all-unused-imports",
                "--recursive",
                str(code_dir)
            ],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            logger.info("autoflake completed successfully. All unused imports removed.")
            return True
        else:
            logger.error(f"autoflake encountered an issue: {result.stderr}")
            return False
    except FileNotFoundError:
        logger.error("autoflake not found. Please install it via pip install autoflake.")
        return False
    except Exception as e:
        logger.error(f"Unexpected error running autoflake: {e}")
        return False

if __name__ == "__main__":
    setup_logging()
    run_all_checks()
