"""
Setup script for linting (flake8) and formatting (black) tools.
This script creates configuration files for flake8 and black
and provides utility functions to check their installation and configuration.
"""
import os
import sys
from pathlib import Path
from typing import List, Tuple
import logging

from utils.logging import get_logger, configure_root_logger
from utils.config import get_project_root


def run_flake8_check() -> Tuple[bool, str]:
    """
    Check if flake8 is installed and run a basic check.
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    logger = get_logger(__name__)
    
    # Check if flake8 is installed
    try:
        import flake8
        logger.info("flake8 is installed.")
    except ImportError:
        error_msg = "flake8 is not installed. Please install it: pip install flake8"
        logger.error(error_msg)
        return False, error_msg
    
    # Run a basic flake8 check on the code directory
    code_dir = get_project_root() / "code"
    if not code_dir.exists():
        error_msg = f"Code directory not found: {code_dir}"
        logger.error(error_msg)
        return False, error_msg
    
    # Try to run flake8
    import subprocess
    try:
        result = subprocess.run(
            ["flake8", str(code_dir), "--count", "--select=E9,F63,F7,F82"],
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            logger.info("flake8 check passed (no critical errors).")
            return True, "flake8 check passed."
        else:
            logger.warning(f"flake8 found issues:\n{result.stdout}")
            return True, f"flake8 found issues (non-critical):\n{result.stdout}"
    except subprocess.TimeoutExpired:
        error_msg = "flake8 check timed out."
        logger.error(error_msg)
        return False, error_msg
    except FileNotFoundError:
        error_msg = "flake8 command not found. Please ensure it is installed and in PATH."
        logger.error(error_msg)
        return False, error_msg


def run_black_check() -> Tuple[bool, str]:
    """
    Check if black is installed and run a basic check.
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    logger = get_logger(__name__)
    
    # Check if black is installed
    try:
        import black
        logger.info("black is installed.")
    except ImportError:
        error_msg = "black is not installed. Please install it: pip install black"
        logger.error(error_msg)
        return False, error_msg
    
    # Run a basic black check on the code directory
    code_dir = get_project_root() / "code"
    if not code_dir.exists():
        error_msg = f"Code directory not found: {code_dir}"
        logger.error(error_msg)
        return False, error_msg
    
    # Try to run black
    import subprocess
    try:
        result = subprocess.run(
            ["black", "--check", "--diff", str(code_dir)],
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            logger.info("black check passed (code is formatted).")
            return True, "black check passed."
        else:
            logger.warning(f"black found formatting issues:\n{result.stdout}")
            return True, f"black found formatting issues (run 'black . code' to fix):\n{result.stdout}"
    except subprocess.TimeoutExpired:
        error_msg = "black check timed out."
        logger.error(error_msg)
        return False, error_msg
    except FileNotFoundError:
        error_msg = "black command not found. Please ensure it is installed and in PATH."
        logger.error(error_msg)
        return False, error_msg


def create_flake8_config() -> Path:
    """
    Create a .flake8 configuration file.
    
    Returns:
        Path to the created config file.
    """
    logger = get_logger(__name__)
    project_root = get_project_root()
    config_path = project_root / ".flake8"
    
    config_content = """[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude =
    .git,
    __pycache__,
    build,
    dist,
    .eggs,
    *.egg-info
"""
    try:
        with open(config_path, "w") as f:
            f.write(config_content)
        logger.info(f"Created flake8 configuration at {config_path}")
        return config_path
    except IOError as e:
        error_msg = f"Failed to create flake8 configuration: {e}"
        logger.error(error_msg)
        raise IOError(error_msg)


def create_black_config() -> Path:
    """
    Create a pyproject.toml configuration for black (if not already present).
    
    Returns:
        Path to the pyproject.toml file.
    """
    logger = get_logger(__name__)
    project_root = get_project_root()
    config_path = project_root / "pyproject.toml"
    
    # Check if pyproject.toml exists and already has [tool.black]
    if config_path.exists():
        try:
            with open(config_path, "r") as f:
                content = f.read()
            if "[tool.black]" in content:
                logger.info("black configuration already exists in pyproject.toml")
                return config_path
        except IOError:
            pass
    
    # Append black configuration
    black_config = """
[tool.black]
line-length = 88
target-version = ['py38', 'py39', 'py310', 'py311']
include = '\\.pyi?$'
exclude = '''
/(
    \\.git
  | \\.hg
  | \\.mypy_cache
  | \\.tox
  | \\.venv
  | _build
  | buck-out
  | build
  | dist
)/
'''
"""
    try:
        with open(config_path, "a") as f:
            f.write(black_config)
        logger.info(f"Appended black configuration to {config_path}")
        return config_path
    except IOError as e:
        error_msg = f"Failed to create black configuration: {e}"
        logger.error(error_msg)
        raise IOError(error_msg)


def main():
    """
    Main entry point for setting up linting and formatting tools.
    """
    configure_root_logger()
    logger = get_logger(__name__)
    
    logger.info("Setting up linting and formatting tools...")
    
    # Create configuration files
    try:
        create_flake8_config()
        create_black_config()
    except Exception as e:
        logger.error(f"Failed to create configuration files: {e}")
        sys.exit(1)
    
    # Run checks
    flake8_success, flake8_msg = run_flake8_check()
    black_success, black_msg = run_black_check()
    
    logger.info("Setup complete.")
    logger.info(f"Flake8: {flake8_msg}")
    logger.info(f"Black: {black_msg}")
    
    # Exit with error if tools are not installed
    if not flake8_success or not black_success:
        logger.warning("One or more tools are not properly installed. Please install them manually.")
        sys.exit(1)
    else:
        logger.info("All linting and formatting tools are ready.")
        sys.exit(0)


if __name__ == "__main__":
    main()