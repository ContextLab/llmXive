"""
Configuration and execution helpers for linting (ruff) and formatting (black/isort).
"""
import os
import subprocess
import sys
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def ensure_ruff_config() -> bool:
    """Verify that ruff configuration exists in pyproject.toml."""
    root = Path.cwd()
    pyproject = root / "pyproject.toml"
    if not pyproject.exists():
        logger.error("pyproject.toml not found in current directory.")
        return False
    
    content = pyproject.read_text()
    if "[tool.ruff]" not in content:
        logger.error("Ruff configuration section [tool.ruff] missing in pyproject.toml.")
        return False
    
    logger.info("Ruff configuration found.")
    return True

def ensure_black_config() -> bool:
    """Verify that black configuration exists in pyproject.toml."""
    root = Path.cwd()
    pyproject = root / "pyproject.toml"
    if not pyproject.exists():
        logger.error("pyproject.toml not found in current directory.")
        return False
    
    content = pyproject.read_text()
    if "[tool.black]" not in content:
        logger.error("Black configuration section [tool.black] missing in pyproject.toml.")
        return False
    
    logger.info("Black configuration found.")
    return True

def run_isort() -> bool:
    """Run isort to sort imports."""
    logger.info("Running isort...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "isort", "."],
            check=True,
            capture_output=True,
            text=True
        )
        if result.stdout:
            logger.info(result.stdout)
        if result.stderr:
            logger.warning(result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"isort failed: {e}")
        logger.error(f"stderr: {e.stderr}")
        return False
    except FileNotFoundError:
        logger.error("isort not found. Please install it: pip install isort")
        return False

def run_lint() -> bool:
    """Run ruff to check for linting errors."""
    logger.info("Running ruff lint...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "check", "."],
            check=True,
            capture_output=True,
            text=True
        )
        if result.stdout:
            logger.info(result.stdout)
        if result.stderr:
            logger.warning(result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Ruff found linting errors:")
        logger.error(f"stdout: {e.stdout}")
        # Returning False here to indicate lint failure, but not crashing the script
        return False
    except FileNotFoundError:
        logger.error("ruff not found. Please install it: pip install ruff")
        return False

def run_format() -> bool:
    """Run black to format code."""
    logger.info("Running black format...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "black", "."],
            check=True,
            capture_output=True,
            text=True
        )
        if result.stdout:
            logger.info(result.stdout)
        if result.stderr:
            logger.warning(result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Black failed: {e}")
        logger.error(f"stderr: {e.stderr}")
        return False
    except FileNotFoundError:
        logger.error("black not found. Please install it: pip install black")
        return False

def main() -> None:
    """Main entry point to run linting and formatting checks."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger.info("Starting lint and format configuration checks...")

    # Verify configs exist
    if not ensure_ruff_config():
        logger.error("Ruff configuration check failed. Exiting.")
        sys.exit(1)
    
    if not ensure_black_config():
        logger.error("Black configuration check failed. Exiting.")
        sys.exit(1)

    logger.info("Configuration checks passed.")

    # Run linter (non-fatal if errors found, just logs them)
    lint_success = run_lint()
    
    # Run formatter
    format_success = run_format()

    # Run isort
    isort_success = run_isort()

    if not lint_success:
        logger.warning("Linting issues found. Please fix them manually or run 'ruff check --fix .'")
    
    if format_success and isort_success:
        logger.info("Formatting and import sorting completed successfully.")
    else:
        logger.error("Formatting or import sorting failed.")
        sys.exit(1)

    logger.info("Linting and formatting pipeline finished.")

if __name__ == "__main__":
    main()