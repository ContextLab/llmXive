"""
Setup and verification script for linting configuration.
This script verifies that flake8 and black configurations are correct
and runs flake8 on a sample file to ensure the setup works.
"""
import os
import sys
import subprocess
import tomli
from pathlib import Path
from utils.logging_config import get_logger

logger = get_logger(__name__)


def check_file_exists(file_path: Path) -> bool:
    """Check if a file exists at the given path."""
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return False
    logger.info(f"File found: {file_path}")
    return True


def validate_black_config(pyproject_path: Path) -> bool:
    """Validate black configuration in pyproject.toml."""
    if not check_file_exists(pyproject_path):
        return False

    try:
        with open(pyproject_path, "rb") as f:
            config = tomli.load(f)

        if "tool" not in config or "black" not in config["tool"]:
            logger.error("Black configuration not found in pyproject.toml")
            return False

        black_config = config["tool"]["black"]
        logger.info(f"Black config: {black_config}")
        return True
    except Exception as e:
        logger.error(f"Error validating black config: {e}")
        return False


def validate_flake8_config(flake8_path: Path) -> bool:
    """Validate flake8 configuration file."""
    if not check_file_exists(flake8_path):
        return False

    try:
        with open(flake8_path, "r") as f:
            content = f.read()

        # Check for essential configuration
        if "max-line-length" not in content:
            logger.warning("max-line-length not explicitly set in .flake8")
        else:
            logger.info("max-line-length is set in .flake8")

        return True
    except Exception as e:
        logger.error(f"Error validating flake8 config: {e}")
        return False


def run_flake8_on_sample(sample_path: Path, flake8_path: Path) -> bool:
    """Run flake8 on a sample file to verify configuration works."""
    if not check_file_exists(sample_path):
        return False

    if not check_file_exists(flake8_path):
        logger.error("Cannot run flake8 without configuration file")
        return False

    try:
        # Run flake8 with the config file
        result = subprocess.run(
            [
                sys.executable, "-m", "flake8",
                "--config=" + str(flake8_path),
                str(sample_path)
            ],
            capture_output=True,
            text=True
        )

        logger.info(f"Flake8 exit code: {result.returncode}")
        if result.stdout:
            logger.info(f"Flake8 stdout:\n{result.stdout}")
        if result.stderr:
            logger.warning(f"Flake8 stderr:\n{result.stderr}")

        # Exit code 0 means no issues, 1 means issues found, 2 means error
        # For this verification, we just want to ensure flake8 runs without crashing
        if result.returncode <= 1:
            logger.info("Flake8 ran successfully on sample file")
            return True
        else:
            logger.error(f"Flake8 failed with exit code {result.returncode}")
            return False

    except Exception as e:
        logger.error(f"Error running flake8: {e}")
        return False


def main():
    """Main entry point for linting setup verification."""
    logger.info("Starting linting configuration verification")

    # Define paths relative to project root
    project_root = Path(__file__).parent.parent
    flake8_config = project_root / ".flake8"
    pyproject_config = project_root / "pyproject.toml"
    sample_file = project_root / "code" / "tests" / "linting" / "sample_code.py"

    # Verify configurations exist and are valid
    flake8_valid = validate_flake8_config(flake8_config)
    black_valid = validate_black_config(pyproject_config)

    if not flake8_valid or not black_valid:
        logger.error("Configuration validation failed")
        sys.exit(1)

    # Run flake8 on sample file
    flake8_runs = run_flake8_on_sample(sample_file, flake8_config)

    if flake8_runs:
        logger.info("Linting configuration verification completed successfully")
        sys.exit(0)
    else:
        logger.error("Flake8 verification failed")
        sys.exit(1)


if __name__ == "__main__":
    main()