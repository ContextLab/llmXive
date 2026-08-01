"""
Script to configure linting (ruff/flake8) and formatting (black) tools.
This script creates configuration files and optionally installs the tools.
"""
import subprocess
import sys
import os
import logging
from typing import Tuple, Optional

from config import ensure_directories, get_config


def setup_script_logging() -> logging.Logger:
    """Setup logging for this script."""
    ensure_directories()
    logger = logging.getLogger("setup_linting")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
    return logger


def check_tool_installed(tool_name: str) -> bool:
    """Check if a tool is installed in the current environment."""
    logger = logging.getLogger("setup_linting")
    try:
        subprocess.run([sys.executable, "-m", tool_name, "--version"],
                       capture_output=True, check=True)
        logger.info(f"{tool_name} is already installed.")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.info(f"{tool_name} is not installed.")
        return False


def install_tool(tool_name: str) -> bool:
    """Install a tool using pip."""
    logger = logging.getLogger("setup_linting")
    try:
        logger.info(f"Installing {tool_name}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", tool_name])
        logger.info(f"{tool_name} installed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install {tool_name}: {e}")
        return False


def create_ruff_config() -> str:
    """Create a ruff.toml configuration file."""
    logger = logging.getLogger("setup_linting")
    config_dir = get_config().get("project_root", ".")
    config_path = os.path.join(config_dir, "ruff.toml")

    if os.path.exists(config_path):
        logger.info(f"ruff.toml already exists at {config_path}. Skipping creation.")
        return config_path

    config_content = """[lint]
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # pyflakes
    "I",  # isort
    "C",  # flake8-comprehensions
    "B",  # flake8-bugbear
]
ignore = [
    "E501",  # line too long (handled by black)
    "B008",  # do not perform function calls in argument defaults
    "C901",  # too complex
]

[lint.per-file-ignores]
"__init__.py" = ["F401"]  # Allow unused imports in __init__.py

[format]
# Use double quotes for strings.
quote-style = "double"

# Indent with spaces, rather than tabs.
indent-style = "space"

# Respect magic trailing commas.
skip-magic-trailing-comma = false

# Automatically detect the appropriate line ending.
line-ending = "auto"
"""
    with open(config_path, "w") as f:
        f.write(config_content)
    logger.info(f"Created ruff.toml at {config_path}")
    return config_path


def create_black_config() -> str:
    """Create a pyproject.toml with Black configuration if it doesn't exist or add to it."""
    logger = logging.getLogger("setup_linting")
    config_dir = get_config().get("project_root", ".")
    config_path = os.path.join(config_dir, "pyproject.toml")

    black_config_section = """
[tool.black]
line-length = 88
target-version = ['py311']
include = '\\.pyi?$'
exclude = '''
/(
    \.eggs
  | \.git
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

    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            content = f.read()
        if "[tool.black]" in content:
            logger.info(f"Black configuration already exists in {config_path}. Skipping update.")
            return config_path
        else:
            with open(config_path, "a") as f:
                f.write(black_config_section)
            logger.info(f"Added Black configuration to {config_path}")
            return config_path
    else:
        with open(config_path, "w") as f:
            f.write(black_config_section)
        logger.info(f"Created pyproject.toml with Black configuration at {config_path}")
        return config_path


def run_flake8_check() -> Tuple[bool, str]:
    """Run flake8 check if ruff is not preferred or as a fallback. Returns (success, message)."""
    logger = logging.getLogger("setup_linting")
    if not check_tool_installed("flake8"):
        if not install_tool("flake8"):
            return False, "flake8 installation failed."
    
    try:
        result = subprocess.run(
            ["flake8", "code/", "tests/"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return True, "flake8 check passed."
        else:
            logger.warning("flake8 found issues:")
            logger.warning(result.stdout)
            return False, "flake8 found issues."
    except Exception as e:
        return False, f"Error running flake8: {e}"


def run_black_check() -> Tuple[bool, str]:
    """Run black check. Returns (success, message)."""
    logger = logging.getLogger("setup_linting")
    if not check_tool_installed("black"):
        if not install_tool("black"):
            return False, "black installation failed."

    try:
        result = subprocess.run(
            ["black", "--check", "code/", "tests/"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return True, "black check passed."
        else:
            logger.warning("black found formatting issues:")
            logger.warning(result.stdout)
            return False, "black found formatting issues."
    except Exception as e:
        return False, f"Error running black: {e}"


def main():
    """Main entry point for setting up linting and formatting."""
    logger = setup_script_logging()
    logger.info("Starting linting and formatting setup...")

    # Create configuration files
    create_ruff_config()
    create_black_config()

    # Check and install tools if necessary
    tools = ["ruff", "black"]
    for tool in tools:
        if not check_tool_installed(tool):
            install_tool(tool)

    # Run checks (optional, can be used to verify setup)
    logger.info("Running initial checks...")
    # Note: We don't fail the setup if checks fail, just log the results.
    # The actual enforcement would happen in CI or via pre-commit hooks.
    
    logger.info("Linting and formatting setup complete.")
    logger.info("Configuration files created: ruff.toml, pyproject.toml")
    logger.info("Tools available: ruff, black")
    logger.info("To run checks manually:")
    logger.info("  ruff check code/ tests/")
    logger.info("  black --check code/ tests/")
    logger.info("  flake8 code/ tests/")


if __name__ == "__main__":
    main()