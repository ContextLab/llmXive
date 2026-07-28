"""
Linting and formatting check utilities for the project.
Runs ruff and black checks on the codebase.
"""
import subprocess
import sys
import os
from pathlib import Path
from utils.logging import get_logger

logger = get_logger(__name__)


def run_command(cmd: list, check: bool = True) -> subprocess.CompletedProcess:
    """
    Run a shell command and return the result.

    Args:
        cmd: Command and arguments as a list.
        check: If True, raise CalledProcessError on non-zero exit.

    Returns:
        CompletedProcess instance.
    """
    logger.info(f"Running command: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            check=check,
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        )
        return result
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed with return code {e.returncode}")
        logger.error(f"stdout: {e.stdout}")
        logger.error(f"stderr: {e.stderr}")
        raise


def check_ruff() -> bool:
    """
    Run ruff check on the code/ directory.

    Returns:
        True if check passes, False otherwise.
    """
    cmd = ["ruff", "check", "code/"]
    try:
        result = run_command(cmd)
        if result.returncode == 0:
            logger.info("ruff check passed.")
            return True
        else:
            logger.error("ruff check failed.")
            if result.stdout:
                logger.error(result.stdout)
            if result.stderr:
                logger.error(result.stderr)
            return False
    except FileNotFoundError:
        logger.error("ruff not found. Please install it: pip install ruff")
        return False
    except Exception as e:
        logger.error(f"Error running ruff: {e}")
        return False


def check_black() -> bool:
    """
    Run black --check on the code/ directory.

    Returns:
        True if check passes, False otherwise.
    """
    cmd = ["black", "--check", "code/"]
    try:
        result = run_command(cmd)
        if result.returncode == 0:
            logger.info("black check passed.")
            return True
        else:
            logger.error("black check failed.")
            if result.stdout:
                logger.error(result.stdout)
            if result.stderr:
                logger.error(result.stderr)
            return False
    except FileNotFoundError:
        logger.error("black not found. Please install it: pip install black")
        return False
    except Exception as e:
        logger.error(f"Error running black: {e}")
        return False


def main():
    """
    Main entry point for lint and format checks.
    Exits with non-zero code if any check fails.
    """
    logger.info("Starting lint and format checks...")

    ruff_ok = check_ruff()
    black_ok = check_black()

    if ruff_ok and black_ok:
        logger.info("All checks passed.")
        sys.exit(0)
    else:
        logger.error("Some checks failed. Please fix the issues.")
        sys.exit(1)


if __name__ == "__main__":
    main()