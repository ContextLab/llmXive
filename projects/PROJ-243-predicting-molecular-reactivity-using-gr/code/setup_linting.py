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
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def check_tool_installed(tool_name: str) -> Tuple[bool, str]:
    """Check if a tool is installed and return its version."""
    try:
        result = subprocess.run(
            [tool_name, '--version'],
            capture_output=True,
            text=True,
            check=True
        )
        return True, result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False, f"{tool_name} not found"

def install_tool(tool_name: str, logger: logging.Logger) -> bool:
    """Install a tool using pip."""
    logger.info(f"Installing {tool_name}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", tool_name])
        logger.info(f"{tool_name} installed successfully.")
        return True
    except subprocess.CalledProcessError:
        logger.error(f"Failed to install {tool_name}.")
        return False

def create_ruff_config(logger: logging.Logger):
    """Create a ruff.toml configuration file."""
    config_content = """[lint]
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # Pyflakes
    "I",  # isort
    "B",  # flake8-bugbear
    "C4", # flake8-comprehensions
]
ignore = [
    "E501", # Line too long (handled by black)
    "B008", # Do not perform function call in argument defaults (common in fastapi)
]

[lint.per-file-ignores]
"__init__.py" = ["F401"]

[format]
quote-style = "double"
indent-style = "space"
line-length = 88
"""
    config_path = "ruff.toml"
    with open(config_path, 'w') as f:
        f.write(config_content)
    logger.info(f"Created {config_path}")

def create_black_config(logger: logging.Logger):
    """Create a pyproject.toml configuration for Black if it doesn't exist."""
    config_path = "pyproject.toml"
    black_section = """
[tool.black]
line-length = 88
target-version = ['py311']
include = '\\.pyi?$'
"""
    
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            content = f.read()
        if '[tool.black]' not in content:
            with open(config_path, 'a') as f:
                f.write(black_section)
            logger.info(f"Added Black config to {config_path}")
        else:
            logger.info(f"Black config already exists in {config_path}")
    else:
        with open(config_path, 'w') as f:
            f.write(black_section)
        logger.info(f"Created {config_path} with Black config")

def run_flake8_check(logger: logging.Logger) -> bool:
    """Run flake8 to check for linting errors."""
    logger.info("Running flake8 check...")
    try:
        result = subprocess.run(
            ['flake8', 'code/', 'tests/'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            logger.info("Flake8 check passed.")
            return True
        else:
            logger.warning("Flake8 found issues:")
            logger.warning(result.stdout)
            return False
    except FileNotFoundError:
        logger.error("Flake8 not found. Please install it.")
        return False

def run_black_check(logger: logging.Logger) -> bool:
    """Run black --check to verify formatting."""
    logger.info("Running Black check...")
    try:
        result = subprocess.run(
            ['black', '--check', 'code/', 'tests/'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            logger.info("Black check passed.")
            return True
        else:
            logger.warning("Black found formatting issues. Run 'black code/ tests/' to fix.")
            logger.warning(result.stdout)
            return False
    except FileNotFoundError:
        logger.error("Black not found. Please install it.")
        return False

def main():
    """Main entry point for setting up linting and formatting tools."""
    logger = setup_script_logging()
    logger.info("Starting linting and formatting setup...")

    # Ensure directories exist
    ensure_directories()

    # Check for ruff
    is_installed, version = check_tool_installed('ruff')
    if not is_installed:
        logger.warning("Ruff not found. Installing...")
        if not install_tool('ruff', logger):
            logger.error("Ruff installation failed. Aborting.")
            sys.exit(1)
    else:
        logger.info(f"Ruff found: {version}")

    # Check for black
    is_installed, version = check_tool_installed('black')
    if not is_installed:
        logger.warning("Black not found. Installing...")
        if not install_tool('black', logger):
            logger.error("Black installation failed. Aborting.")
            sys.exit(1)
    else:
        logger.info(f"Black found: {version}")

    # Check for flake8 (optional, ruff can replace it, but we keep it for compatibility)
    is_installed, version = check_tool_installed('flake8')
    if not is_installed:
        logger.warning("Flake8 not found. Installing...")
        if not install_tool('flake8', logger):
            logger.warning("Flake8 installation failed. Continuing without it.")
    else:
        logger.info(f"Flake8 found: {version}")

    # Create configuration files
    create_ruff_config(logger)
    create_black_config(logger)

    # Run checks (optional, just to show status)
    run_flake8_check(logger)
    run_black_check(logger)

    logger.info("Linting and formatting setup complete.")

if __name__ == "__main__":
    main()