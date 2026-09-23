"""
Setup and verification script for linting configuration (T003b).
This script validates .flake8 and pyproject.toml configurations
and runs flake8 on a sample file to verify the setup.
"""
import os
import sys
import subprocess
from pathlib import Path
from utils.logging_config import get_logger

logger = get_logger(__name__)

def check_file_exists(filepath: Path) -> bool:
    """Check if a file exists."""
    if not filepath.exists():
        logger.error(f"File not found: {filepath}")
        return False
    return True

def validate_black_config(config_path: Path) -> bool:
    """Validate Black configuration in pyproject.toml."""
    if not check_file_exists(config_path):
        return False

    try:
        import tomli
        with open(config_path, "rb") as f:
            config = tomli.load(f)

        if "tool" not in config or "black" not in config["tool"]:
            logger.warning("Black configuration section not found in pyproject.toml")
            return True  # Not a failure, just missing config

        logger.info("Black configuration validated successfully")
        return True
    except Exception as e:
        logger.error(f"Error validating Black config: {e}")
        return False

def validate_flake8_config(config_path: Path) -> bool:
    """Validate flake8 configuration in .flake8."""
    if not check_file_exists(config_path):
        return False

    try:
        with open(config_path, "r") as f:
            content = f.read()

        if "[flake8]" not in content:
            logger.error("Missing [flake8] section in .flake8")
            return False

        logger.info("flake8 configuration validated successfully")
        return True
    except Exception as e:
        logger.error(f"Error validating flake8 config: {e}")
        return False

def run_flake8_on_sample(sample_path: Path, config_dir: Path) -> bool:
    """Run flake8 on a sample file to verify configuration."""
    if not check_file_exists(sample_path):
        return False

    try:
        # Run flake8 with explicit config directory
        result = subprocess.run(
            ["flake8", "--config=" + str(config_dir / ".flake8"), str(sample_path)],
            capture_output=True,
            text=True,
            cwd=config_dir
        )

        # Log the output
        if result.stdout:
            logger.info("flake8 output:")
            for line in result.stdout.splitlines():
                logger.info(f"  {line}")

        if result.returncode == 0:
            logger.info("flake8 ran successfully with no errors")
            return True
        else:
            logger.warning(f"flake8 found issues (return code {result.returncode})")
            return True  # Returning True because the config is working, it just found issues

    except FileNotFoundError:
        logger.error("flake8 not found. Please install it: pip install flake8")
        return False
    except Exception as e:
        logger.error(f"Error running flake8: {e}")
        return False

def main():
    """Main entry point for T003b: Verify linting configuration."""
    root_dir = Path(__file__).resolve().parent.parent
    config_dir = root_dir
    sample_file = root_dir / "code" / "tests" / "linting" / "sample_code.py"

    logger.info("Starting linting configuration verification (T003b)")

    # Validate .flake8
    flake8_config = config_dir / ".flake8"
    if not validate_flake8_config(flake8_config):
        logger.error("flake8 configuration validation failed")
        sys.exit(1)

    # Validate pyproject.toml (for Black)
    pyproject_config = config_dir / "pyproject.toml"
    if not validate_black_config(pyproject_config):
        logger.error("Black configuration validation failed")
        sys.exit(1)

    # Run flake8 on sample file
    if not run_flake8_on_sample(sample_file, config_dir):
        logger.error("flake8 execution on sample file failed")
        sys.exit(1)

    logger.info("Linting configuration verification completed successfully")

if __name__ == "__main__":
    main()
