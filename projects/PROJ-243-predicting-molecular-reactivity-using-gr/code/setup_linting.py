import subprocess
import sys
import os
import logging
from typing import Tuple, Optional
from config import ensure_directories, get_config

def setup_script_logging() -> logging.Logger:
    """Initialize logging for the setup script."""
    logger = logging.getLogger("setup_linting")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

def check_tool_installed(tool_name: str) -> Tuple[bool, Optional[str]]:
    """
    Check if a tool is installed via pip.
    Returns (is_installed, error_message).
    """
    try:
        subprocess.run([sys.executable, "-m", "pip", "show", tool_name],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return True, None
    except subprocess.CalledProcessError:
        return False, f"Tool '{tool_name}' is not installed."

def install_tool(tool_name: str, logger: logging.Logger) -> bool:
    """Install a tool via pip."""
    logger.info(f"Installing {tool_name}...")
    try:
        result = subprocess.run([sys.executable, "-m", "pip", "install", tool_name],
                                check=True, capture_output=True, text=True)
        logger.info(f"{tool_name} installed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install {tool_name}: {e.stderr}")
        return False

def create_ruff_config(logger: logging.Logger) -> str:
    """Create a ruff.toml configuration file."""
    config_content = """[lint]
select = ["E", "F", "W", "I", "N", "UP", "B", "C4", "SIM"]
ignore = ["E501", "E731", "F403"]
target-version = "py311"

[lint.isort]
known-first-party = ["code", "utils", "config"]
force-single-line = true

[format]
line-length = 88
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
"""
    path = os.path.join("code", "..", "ruff.toml")
    with open(path, "w") as f:
        f.write(config_content)
    logger.info(f"Created ruff.toml at {path}")
    return path

def create_black_config(logger: logging.Logger) -> str:
    """Create a pyproject.toml configuration file with Black settings if not exists."""
    pyproject_path = os.path.join("code", "..", "pyproject.toml")
    
    # Check if file exists and has [tool.black]
    if os.path.exists(pyproject_path):
        with open(pyproject_path, "r") as f:
            content = f.read()
        if "[tool.black]" in content:
            logger.info("Black configuration already exists in pyproject.toml.")
            return pyproject_path

    # Append Black configuration
    black_config = """
[tool.black]
line-length = 88
target-version = ['py311']
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
)/
'''
"""
    with open(pyproject_path, "a") as f:
        f.write(black_config)
    logger.info(f"Updated pyproject.toml with Black configuration at {pyproject_path}")
    return pyproject_path

def run_flake8_check(logger: logging.Logger) -> bool:
    """Run flake8 to check for linting errors (dry run)."""
    logger.info("Running flake8 check...")
    try:
        result = subprocess.run([sys.executable, "-m", "flake8", "code", "tests"],
                                capture_output=True, text=True)
        if result.returncode == 0:
            logger.info("Flake8 check passed.")
            return True
        else:
            logger.warning("Flake8 found issues (not fatal for setup, but review recommended):")
            logger.warning(result.stdout)
            return True
    except FileNotFoundError:
        logger.error("Flake8 not found. Please install it.")
        return False

def run_black_check(logger: logging.Logger) -> bool:
    """Run black --check to verify formatting (dry run)."""
    logger.info("Running black check...")
    try:
        result = subprocess.run([sys.executable, "-m", "black", "--check", "--diff", "code", "tests"],
                                capture_output=True, text=True)
        if result.returncode == 0:
            logger.info("Black check passed.")
            return True
        else:
            logger.warning("Black found formatting issues (not fatal for setup, but review recommended):")
            logger.warning(result.stdout)
            return True
    except FileNotFoundError:
        logger.error("Black not found. Please install it.")
        return False

def main() -> int:
    """Main entry point for setting up linting and formatting."""
    logger = setup_script_logging()
    logger.info("Starting linting and formatting setup...")

    # Ensure directories exist
    config = get_config()
    ensure_directories()

    # Check and install Ruff
    is_installed, error = check_tool_installed("ruff")
    if not is_installed:
        if not install_tool("ruff", logger):
            logger.error("Failed to install ruff. Exiting.")
            return 1

    # Check and install Black
    is_installed, error = check_tool_installed("black")
    if not is_installed:
        if not install_tool("black", logger):
            logger.error("Failed to install black. Exiting.")
            return 1

    # Check and install Flake8 (optional but good practice)
    is_installed, error = check_tool_installed("flake8")
    if not is_installed:
        if not install_tool("flake8", logger):
            logger.warning("Failed to install flake8. Continuing without flake8 check.")

    # Create configuration files
    create_ruff_config(logger)
    create_black_config(logger)

    logger.info("Linting and formatting setup complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())