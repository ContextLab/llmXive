import subprocess
import sys
import os
import logging
from typing import Tuple, Optional
from config import ensure_directories, get_config

def setup_script_logging():
    """Initialize logging for the setup script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def check_tool_installed(tool_name: str) -> Tuple[bool, str]:
    """Check if a tool is installed and return version if available."""
    try:
        result = subprocess.run(
            [tool_name, '--version'],
            capture_output=True,
            text=True,
            check=True
        )
        return True, result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False, "Not found"

def install_tool(tool_name: str, logger: logging.Logger) -> bool:
    """Install a tool using pip if not already installed."""
    logger.info(f"Attempting to install {tool_name}...")
    try:
        subprocess.run(
            [sys.executable, '-m', 'pip', 'install', tool_name],
            check=True,
            capture_output=True
        )
        logger.info(f"{tool_name} installed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install {tool_name}: {e.stderr.decode()}")
        return False

def create_ruff_config(logger: logging.Logger) -> bool:
    """Create a standard ruff.toml configuration file."""
    config_path = os.path.join(os.getcwd(), 'ruff.toml')
    if os.path.exists(config_path):
        logger.info(f"ruff.toml already exists at {config_path}")
        return True

    ruff_config = """
[lint]
select = ["E", "F", "W", "I", "N", "UP", "B", "C4", "ARG", "SIM"]
ignore = ["E501", "F401"]
target-version = "py311"

[format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"
"""
    try:
        with open(config_path, 'w') as f:
            f.write(ruff_config.strip())
        logger.info(f"Created ruff.toml at {config_path}")
        return True
    except IOError as e:
        logger.error(f"Failed to create ruff.toml: {e}")
        return False

def create_black_config(logger: logging.Logger) -> bool:
    """Create a standard pyproject.toml with Black configuration."""
    config_path = os.path.join(os.getcwd(), 'pyproject.toml')
    if os.path.exists(config_path):
        # Check if [tool.black] section exists
        with open(config_path, 'r') as f:
            content = f.read()
            if '[tool.black]' in content:
                logger.info(f"Black configuration already exists in {config_path}")
                return True

    # Load existing content if file exists, otherwise start fresh
    existing_content = ""
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            existing_content = f.read()

    black_section = """
[tool.black]
line-length = 88
target-version = ['py311']
include = '\\.pyi?$'
exclude = '''
/(
    \\.eggs
  | \\.git
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
        with open(config_path, 'w') as f:
            if existing_content:
                f.write(existing_content.rstrip() + '\n' + black_section)
            else:
                f.write(black_section)
        logger.info(f"Updated {config_path} with Black configuration")
        return True
    except IOError as e:
        logger.error(f"Failed to update {config_path}: {e}")
        return False

def run_flake8_check(logger: logging.Logger) -> bool:
    """Run flake8 to check for linting issues."""
    logger.info("Running flake8 check...")
    try:
        result = subprocess.run(
            ['flake8', 'code/', 'tests/'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            logger.info("No flake8 issues found.")
            return True
        else:
            logger.warning("Flake8 found issues:")
            logger.warning(result.stdout)
            return False
    except FileNotFoundError:
        logger.error("flake8 is not installed or not in PATH.")
        return False

def run_black_check(logger: logging.Logger) -> bool:
    """Run black --check to verify formatting."""
    logger.info("Running black --check...")
    try:
        result = subprocess.run(
            ['black', '--check', 'code/', 'tests/'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            logger.info("Code is formatted correctly with Black.")
            return True
        else:
            logger.warning("Code needs reformatting with Black:")
            logger.warning(result.stdout)
            return False
    except FileNotFoundError:
        logger.error("Black is not installed or not in PATH.")
        return False

def main():
    """Main entry point for setting up linting and formatting tools."""
    logger = setup_script_logging()
    logger.info("Starting linting and formatting setup...")

    # Ensure directories exist
    config = get_config()
    ensure_directories(config)

    # Check and install tools
    tools = [('ruff', 'ruff'), ('black', 'black'), ('flake8', 'flake8')]
    all_installed = True

    for display_name, tool_name in tools:
        is_installed, version = check_tool_installed(tool_name)
        if not is_installed:
            logger.warning(f"{display_name} is not installed.")
            if install_tool(tool_name, logger):
                is_installed = True
            else:
                all_installed = False
        else:
            logger.info(f"{display_name} is installed: {version}")

    if not all_installed:
        logger.error("Some tools could not be installed. Aborting setup.")
        sys.exit(1)

    # Create configuration files
    create_ruff_config(logger)
    create_black_config(logger)

    # Run checks
    flake8_ok = run_flake8_check(logger)
    black_ok = run_black_check(logger)

    if flake8_ok and black_ok:
        logger.info("Linting and formatting setup completed successfully.")
        sys.exit(0)
    else:
        logger.warning("Linting or formatting checks failed. Please fix the issues.")
        sys.exit(1)

if __name__ == "__main__":
    main()