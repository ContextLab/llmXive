import subprocess
import sys
import os
import logging
from typing import Tuple, Optional
from config import ensure_directories, get_config

def setup_script_logging():
    """Configure logging for the setup script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('artifacts/logs/setup_linting.log')
        ]
    )
    return logging.getLogger(__name__)

def check_tool_installed(tool_name: str) -> Tuple[bool, str]:
    """Check if a tool is installed and return its version."""
    try:
        result = subprocess.run(
            [sys.executable, '-m', tool_name, '--version'],
            capture_output=True,
            text=True,
            check=True
        )
        return True, result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return False, str(e)
    except FileNotFoundError:
        return False, f"Command '{tool_name}' not found"

def install_tool(tool_name: str, logger: logging.Logger) -> bool:
    """Install a Python tool using pip."""
    logger.info(f"Installing {tool_name}...")
    try:
        subprocess.run(
            [sys.executable, '-m', 'pip', 'install', tool_name],
            check=True,
            capture_output=True,
            text=True
        )
        logger.info(f"{tool_name} installed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install {tool_name}: {e.stderr}")
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
    "UP", # pyupgrade
]
ignore = [
    "E501", # line too long (handled by black)
    "B008", # do not perform function calls in argument defaults
]

[lint.isort]
known-first-party = ["code", "tests"]

[format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"
"""
    config_path = os.path.join(os.getcwd(), "ruff.toml")
    with open(config_path, 'w') as f:
        f.write(config_content)
    logger.info(f"Created ruff configuration at {config_path}")

def create_black_config(logger: logging.Logger):
    """Create a pyproject.toml configuration file with Black settings if not exists."""
    pyproject_path = os.path.join(os.getcwd(), "pyproject.toml")
    
    # Read existing content if file exists
    existing_content = ""
    if os.path.exists(pyproject_path):
        with open(pyproject_path, 'r') as f:
            existing_content = f.read()

    # Check if [tool.black] section exists
    if "[tool.black]" not in existing_content:
        black_section = """
[tool.black]
line-length = 88
target-version = ['py311']
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
        with open(pyproject_path, 'a') as f:
            f.write(black_section)
        logger.info(f"Added Black configuration to {pyproject_path}")
    else:
        logger.info(f"Black configuration already exists in {pyproject_path}")

def run_flake8_check(logger: logging.Logger) -> bool:
    """Run flake8 to check for linting errors."""
    logger.info("Running flake8 check...")
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'flake8', 'code/', 'tests/'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            logger.info("Flake8 check passed: No linting errors found.")
            return True
        else:
            logger.warning(f"Flake8 found issues:\n{result.stdout}")
            return False
    except FileNotFoundError:
        logger.error("flake8 not found. Please install it.")
        return False

def run_black_check(logger: logging.Logger) -> bool:
    """Run black --check to verify formatting."""
    logger.info("Running black check...")
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'black', '--check', 'code/', 'tests/'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            logger.info("Black check passed: Code is properly formatted.")
            return True
        else:
            logger.warning(f"Black found formatting issues:\n{result.stdout}")
            return False
    except FileNotFoundError:
        logger.error("black not found. Please install it.")
        return False

def main():
    """Main entry point for linting setup."""
    logger = setup_script_logging()
    logger.info("Starting linting and formatting setup...")

    # Ensure directories exist
    config = get_config()
    ensure_directories(config)

    # Check and install tools
    tools = {
        'ruff': 'ruff',
        'black': 'black',
        'flake8': 'flake8'
    }

    for tool_name, pip_name in tools.items():
        installed, version = check_tool_installed(pip_name)
        if not installed:
            logger.warning(f"{tool_name} is not installed.")
            if install_tool(pip_name, logger):
                installed, version = check_tool_installed(pip_name)
                if installed:
                    logger.info(f"{tool_name} version {version}")
                else:
                    logger.error(f"Failed to install {tool_name} despite retry.")
                    sys.exit(1)
            else:
                logger.error(f"Failed to install {tool_name}.")
                sys.exit(1)
        else:
            logger.info(f"{tool_name} is installed: {version}")

    # Create configuration files
    create_ruff_config(logger)
    create_black_config(logger)

    # Run checks (informational, do not fail setup if issues found)
    run_flake8_check(logger)
    run_black_check(logger)

    logger.info("Linting and formatting setup complete.")

if __name__ == "__main__":
    main()