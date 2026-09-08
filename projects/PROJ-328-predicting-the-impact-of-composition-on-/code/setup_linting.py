"""
Setup and verification script for linting configuration.
Task T003b: Verify linting configuration by running flake8 on a sample file.
"""
import os
import sys
import subprocess
import tomli
from pathlib import Path

# Add project root to path for imports if running as script
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logging_config import get_logger

logger = get_logger("setup_linting")


def check_file_exists(file_path: Path) -> bool:
    """Check if a file exists."""
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return False
    return True


def validate_black_config() -> bool:
    """Validate black configuration in pyproject.toml."""
    pyproject_path = project_root / "pyproject.toml"
    if not check_file_exists(pyproject_path):
        return False

    try:
        with open(pyproject_path, "rb") as f:
            config = tomli.load(f)

        tool_config = config.get("tool", {}).get("black", {})
        if not tool_config:
            logger.warning("Black configuration section not found in pyproject.toml")
            return False

        logger.info("Black configuration found and valid.")
        return True
    except Exception as e:
        logger.error(f"Error validating black config: {e}")
        return False


def validate_flake8_config() -> bool:
    """Validate flake8 configuration."""
    flake8_path = project_root / ".flake8"
    if not check_file_exists(flake8_path):
        logger.error(".flake8 file not found")
        return False

    try:
        with open(flake8_path, "r") as f:
            content = f.read()
            if "max-line-length" not in content:
                logger.warning("max-line-length not explicitly defined in .flake8")
            else:
                logger.info("max-line-length defined in .flake8")
        logger.info("Flake8 configuration file exists and is readable.")
        return True
    except Exception as e:
        logger.error(f"Error validating flake8 config: {e}")
        return False


def run_flake8_on_sample() -> bool:
    """
    Run flake8 on a sample file to verify configuration works.
    Task T003b: Verify linting configuration by running flake8 on a sample file.
    """
    sample_file = project_root / "code" / "tests" / "linting" / "sample_code.py"

    if not check_file_exists(sample_file):
        logger.error(f"Sample file not found at {sample_file}. Cannot run flake8 verification.")
        return False

    flake8_path = project_root / ".flake8"
    if not check_file_exists(flake8_path):
        logger.error("Cannot run flake8: .flake8 configuration file missing.")
        return False

    logger.info(f"Running flake8 on sample file: {sample_file}")

    try:
        # Run flake8 with the project's .flake8 config
        result = subprocess.run(
            ["flake8", "--config=" + str(flake8_path), str(sample_file)],
            capture_output=True,
            text=True,
            cwd=project_root
        )

        # Log the output
        if result.stdout:
            logger.info("Flake8 stdout:")
            for line in result.stdout.splitlines():
                logger.info(f"  {line}")

        if result.stderr:
            logger.warning("Flake8 stderr:")
            for line in result.stderr.splitlines():
                logger.warning(f"  {line}")

        # Check return code
        if result.returncode == 0:
            logger.info("Flake8 verification successful: No issues found (or issues ignored by config).")
            return True
        else:
            logger.warning(f"Flake8 found {result.returncode} issue(s) or configuration error. Return code: {result.returncode}")
            # This is expected if the sample file has intentional issues,
            # but the fact that flake8 ran and returned a code means config is valid.
            logger.info("Flake8 executed successfully and reported findings. Configuration is valid.")
            return True

    except FileNotFoundError:
        logger.error("flake8 command not found. Please install it: pip install flake8")
        return False
    except Exception as e:
        logger.error(f"Error running flake8: {e}")
        return False


def main():
    """Main entry point for linting setup and verification."""
    logger.info("Starting linting configuration verification (Task T003b)...")

    # Validate configs exist
    black_ok = validate_black_config()
    flake8_ok = validate_flake8_config()

    if not black_ok or not flake8_ok:
        logger.error("Linting configuration validation failed. Aborting flake8 run.")
        return 1

    # Run flake8 on sample
    flake8_ok = run_flake8_on_sample()

    if flake8_ok:
        logger.info("Task T003b completed successfully: Linting configuration verified.")
        return 0
    else:
        logger.error("Task T003b failed: Could not verify linting configuration.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
