import subprocess
import sys
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def _log_step(message: str) -> None:
    """Helper to log steps with consistent formatting."""
    logger.info(f"LINT: {message}")

def run_flake8() -> bool:
    """Run flake8 linter."""
    _log_step("Running flake8")
    try:
        result = subprocess.run(
            ["flake8", "code/"],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0:
            logger.info("Flake8 passed")
            return True
        else:
            logger.warning(f"Flake8 found issues:\n{result.stdout}")
            return False
    except FileNotFoundError:
        logger.error("Flake8 not found. Install with: pip install flake8")
        return False

def run_black() -> bool:
    """Run Black formatter."""
    _log_step("Running black")
    try:
        result = subprocess.run(
            ["black", "--check", "code/"],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0:
            logger.info("Black check passed")
            return True
        else:
            logger.warning(f"Black formatting issues found:\n{result.stdout}")
            return False
    except FileNotFoundError:
        logger.error("Black not found. Install with: pip install black")
        return False

def run_isort() -> bool:
    """Run isort import sorter."""
    _log_step("Running isort")
    try:
        result = subprocess.run(
            ["isort", "--check-only", "code/"],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0:
            logger.info("Isort check passed")
            return True
        else:
            logger.warning(f"Isort issues found:\n{result.stdout}")
            return False
    except FileNotFoundError:
        logger.error("Isort not found. Install with: pip install isort")
        return False

def run_all_checks() -> bool:
    """Run all linting checks."""
    _log_step("Running all linting checks")
    flake8_ok = run_flake8()
    black_ok = run_black()
    isort_ok = run_isort()
    
    if flake8_ok and black_ok and isort_ok:
        logger.info("All linting checks passed")
        return True
    else:
        logger.warning("Some linting checks failed")
        return False

def run_all_formatters() -> None:
    """Run all formatters to fix issues."""
    _log_step("Running all formatters")
    try:
        subprocess.run(["black", "code/"], check=True)
        subprocess.run(["isort", "code/"], check=True)
        logger.info("Formatters applied successfully")
    except subprocess.CalledProcessError as e:
        logger.error(f"Formatter failed: {e}")

def main() -> None:
    """Main entry point for linting config script."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    success = run_all_checks()
    if not success:
        logger.warning("Please fix linting issues before committing.")
        sys.exit(1)
    else:
        logger.info("Linting completed successfully")

if __name__ == "__main__":
    import sys
    main()
