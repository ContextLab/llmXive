"""
T003: Configure linting (flake8/black) and formatting tools.

This script ensures the project has the necessary configuration files for
code quality tools (flake8, black) and installs the required dependencies.
"""
import os
import sys
import configparser
import toml
import logging
from datetime import datetime

# Import from utils as per API surface
from utils import setup_logging, get_logger, set_task_id, get_task_id

TASK_ID = "T003"

# Configuration constants
FLAKE8_CONFIG_FILE = ".flake8"
PYPROJECT_CONFIG_FILE = "pyproject.toml"
REQUIREMENTS_FILE = "code/requirements.txt"
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def check_file_exists(filepath, create=False):
    """Check if a file exists, optionally creating it."""
    if os.path.exists(filepath):
        return True
    if create:
        with open(filepath, 'w') as f:
            f.write("")
        return True
    return False

def validate_flake8_config(config_path):
    """Validate or create a .flake8 configuration file."""
    if not os.path.exists(config_path):
        logger = get_logger()
        logger.info(f"Creating {config_path} with default settings...")
        config_content = """[flake8]
max-line-length = 88
extend-ignore = E203, E501, W503
exclude =
    .git,
    __pycache__,
    .eggs,
    build,
    dist,
    *.egg-info
max-complexity = 10
"""
        with open(config_path, 'w') as f:
            f.write(config_content)
        return True
    return True

def validate_pyproject_config(config_path):
    """Validate or create a pyproject.toml configuration file with Black settings."""
    if not os.path.exists(config_path):
        logger = get_logger()
        logger.info(f"Creating {config_path} with Black settings...")
        config_content = """[tool.black]
line-length = 88
target-version = ['py38', 'py39', 'py310']
include = '\\.pyi?$'
exclude = '''
/(
    \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | _build
  | buck-out
  | build
  | dist
  | \.egg-info
)/
'''

[tool.isort]
profile = "black"
line_length = 88
"""
        with open(config_path, 'w') as f:
            f.write(config_content)
        return True
    
    # If it exists, try to parse it to ensure it's valid TOML
    try:
        with open(config_path, 'r') as f:
            toml.load(f)
        return True
    except Exception as e:
        logger = get_logger()
        logger.error(f"Invalid TOML in {config_path}: {e}")
        return False

def update_requirements():
    """Ensure linting dependencies are in requirements.txt."""
    logger = get_logger()
    required_packages = ["flake8", "black", "isort", "pylint"]
    
    if not os.path.exists(REQUIREMENTS_FILE):
        logger.warning(f"{REQUIREMENTS_FILE} not found. Creating with linting tools...")
        with open(REQUIREMENTS_FILE, 'w') as f:
            f.write("# Linting and Formatting Tools\n")
            for pkg in required_packages:
                f.write(f"{pkg}\n")
        return True

    with open(REQUIREMENTS_FILE, 'r') as f:
        content = f.read()
    
    updated = False
    for pkg in required_packages:
        if pkg not in content:
            logger.info(f"Adding {pkg} to {REQUIREMENTS_FILE}")
            updated = True
    
    if updated:
        with open(REQUIREMENTS_FILE, 'a') as f:
            f.write("\n# Linting and Formatting Tools\n")
            for pkg in required_packages:
                if pkg not in content:
                    f.write(f"{pkg}\n")
    
    return True

def main():
    """Main entry point for T003: Configure linting and formatting."""
    logger = setup_logging(task_id=TASK_ID)
    logger.info("Starting T003: Configure linting (flake8/black) and formatting tools.")
    
    try:
        # 1. Create .flake8 configuration
        flake8_path = os.path.join(PROJECT_ROOT, FLAKE8_CONFIG_FILE)
        if not validate_flake8_config(flake8_path):
            logger.error(f"Failed to validate/create {FLAKE8_CONFIG_FILE}")
            return 1
        logger.info(f"✓ {FLAKE8_CONFIG_FILE} configured.")

        # 2. Create pyproject.toml with Black settings
        pyproject_path = os.path.join(PROJECT_ROOT, PYPROJECT_CONFIG_FILE)
        if not validate_pyproject_config(pyproject_path):
            logger.error(f"Failed to validate/create {PYPROJECT_CONFIG_FILE}")
            return 1
        logger.info(f"✓ {PYPROJECT_CONFIG_FILE} configured.")

        # 3. Update requirements.txt with linting tools
        if not update_requirements():
            logger.error("Failed to update requirements.txt")
            return 1
        logger.info("✓ requirements.txt updated with linting tools.")

        # 4. Log success
        logger.info("T003 completed successfully. Linting and formatting tools configured.")
        return 0

    except Exception as e:
        logger.error(f"T003 failed with error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())