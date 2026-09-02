"""
Linting Runner Module

Provides functionality to run Black formatting on the codebase.
"""
import subprocess
import sys
import logging
from pathlib import Path
from config import setup_logging

# Initialize logger
logger = setup_logging(__name__)


def run_black_check(project_root: Path) -> bool:
    """
    Run black --check on the code directory to verify formatting.

    Args:
        project_root: Path to the project root directory.

    Returns:
        True if all files are formatted correctly, False otherwise.
    """
    code_dir = project_root / "code"
    if not code_dir.exists():
        logger.error(f"Code directory not found: {code_dir}")
        return False

    logger.info(f"Running black check on {code_dir}...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "black", "--check", str(code_dir)],
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode == 0:
            logger.info("Black check passed: All files are formatted correctly.")
            return True
        else:
            logger.warning("Black check failed: Some files need formatting.")
            if result.stdout:
                logger.warning(result.stdout)
            if result.stderr:
                logger.warning(result.stderr)
            return False
    except FileNotFoundError:
        logger.error("Black is not installed. Please install it via requirements.txt.")
        return False
    except Exception as e:
        logger.error(f"Error running black check: {e}")
        return False


def run_black_format(project_root: Path) -> bool:
    """
    Run black on the code directory to format files.

    Args:
        project_root: Path to the project root directory.

    Returns:
        True if formatting succeeded, False otherwise.
    """
    code_dir = project_root / "code"
    if not code_dir.exists():
        logger.error(f"Code directory not found: {code_dir}")
        return False

    logger.info(f"Running black format on {code_dir}...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "black", str(code_dir)],
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode == 0:
            logger.info("Black formatting completed successfully.")
            return True
        else:
            logger.error("Black formatting failed.")
            if result.stdout:
                logger.error(result.stdout)
            if result.stderr:
                logger.error(result.stderr)
            return False
    except FileNotFoundError:
        logger.error("Black is not installed. Please install it via requirements.txt.")
        return False
    except Exception as e:
        logger.error(f"Error running black format: {e}")
        return False


def run_all_checks(project_root: Path) -> bool:
    """
    Run all linting checks (black check) and format if necessary.

    Args:
        project_root: Path to the project root directory.

    Returns:
        True if formatting was successful (or already correct), False otherwise.
    """
    logger.info("Starting linting process...")

    # First, check if formatting is needed
    if run_black_check(project_root):
        logger.info("No formatting needed.")
        return True

    # If check failed, attempt to format
    logger.info("Formatting code with black...")
    success = run_black_format(project_root)

    if success:
        logger.info("Formatting completed. Re-checking...")
        # Re-check to ensure formatting was applied correctly
        if run_black_check(project_root):
            return True
        else:
            logger.error("Formatting applied, but re-check failed.")
            return False
    else:
        logger.error("Formatting failed.")
        return False


def main():
    """
    Main entry point for the linting runner script.
    """
    # Determine project root (assuming script is in code/)
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent

    logging.basicConfig(level=logging.INFO)
    logger = setup_logging(__name__)

    success = run_all_checks(project_root)

    if success:
        logger.info("All linting checks passed.")
        sys.exit(0)
    else:
        logger.error("Linting checks failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()