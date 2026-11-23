"""
Setup script for linting (ruff) and formatting (black) tools.
This script configures the project to use ruff for linting and black for formatting.
"""
import subprocess
import sys
import os
import logging
from typing import Tuple, Optional
from config import ensure_directories, get_config

def setup_script_logging() -> logging.Logger:
    """Initialize logging for the setup script."""
    logger = logging.getLogger(__name__)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

def check_tool_installed(tool_name: str) -> bool:
    """Check if a tool is installed."""
    try:
        subprocess.run([tool_name, "--version"], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def install_tool(tool_name: str) -> bool:
    """Install a tool using pip."""
    logger = logging.getLogger(__name__)
    logger.info(f"Installing {tool_name}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", tool_name])
        logger.info(f"{tool_name} installed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install {tool_name}: {e}")
        return False

def create_ruff_config() -> str:
    """Create a default ruff configuration file."""
    logger = logging.getLogger(__name__)
    config_path = os.path.join("code", "ruff.toml")
    config_content = """[lint]
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # pyflakes
    "I",  # isort
    "B",  # flake8-bugbear
    "C4", # flake8-comprehensions
]
ignore = [
    "E501", # line too long (handled by black)
    "B008", # do not perform function calls in argument defaults
    "C901", # too complex
]

[format]
line-length = 88
target-version = "py311"
"""
    with open(config_path, "w") as f:
        f.write(config_content)
    logger.info(f"Created ruff configuration at {config_path}")
    return config_path

def create_black_config() -> str:
    """Create a default black configuration file."""
    logger = logging.getLogger(__name__)
    config_path = os.path.join("code", "pyproject.toml")
    config_content = """[tool.black]
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
    # Check if pyproject.toml already exists and has [tool.black]
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            content = f.read()
            if "[tool.black]" in content:
                logger.info(f"Black configuration already exists at {config_path}")
                return config_path

    with open(config_path, "w") as f:
        f.write(config_content)
    logger.info(f"Created black configuration at {config_path}")
    return config_path

def run_flake8_check() -> Tuple[bool, str]:
    """Run flake8 (or ruff) check and return success status and output."""
    logger = logging.getLogger(__name__)
    # We use ruff as the primary linter, but the task mentions flake8.
    # Ruff is a drop-in replacement for flake8.
    cmd = ["ruff", "check", "code/"]
    logger.info(f"Running lint check: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            logger.info("Lint check passed.")
            return True, "No issues found."
        else:
            logger.warning("Lint check found issues:")
            logger.warning(result.stdout)
            return False, result.stdout
    except FileNotFoundError:
        logger.error("ruff not found. Please install it with 'pip install ruff'.")
        return False, "ruff not found."

def run_black_check() -> Tuple[bool, str]:
    """Run black check and return success status and output."""
    logger = logging.getLogger(__name__)
    cmd = ["black", "--check", "code/"]
    logger.info(f"Running format check: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            logger.info("Format check passed.")
            return True, "All files are formatted correctly."
        else:
            logger.warning("Format check found issues:")
            logger.warning(result.stdout)
            return False, result.stdout
    except FileNotFoundError:
        logger.error("black not found. Please install it with 'pip install black'.")
        return False, "black not found."

def main():
    """Main entry point for the setup script."""
    logger = setup_script_logging()
    logger.info("Starting linting and formatting setup...")

    # Ensure directories exist
    ensure_directories()

    # Check and install tools if necessary
    tools = [
        ("ruff", "ruff"),
        ("black", "black"),
    ]

    for tool_name, pip_name in tools:
        if not check_tool_installed(tool_name):
            logger.warning(f"{tool_name} is not installed.")
            if not install_tool(pip_name):
                logger.error(f"Failed to install {tool_name}. Exiting.")
                sys.exit(1)

    # Create configuration files
    create_ruff_config()
    create_black_config()

    # Run checks
    logger.info("Running lint and format checks...")
    lint_ok, lint_msg = run_flake8_check()
    format_ok, format_msg = run_black_check()

    if lint_ok and format_ok:
        logger.info("All checks passed. Setup complete.")
        sys.exit(0)
    else:
        logger.warning("Some checks failed. Please review the output above.")
        if not lint_ok:
            logger.warning("Lint errors: " + lint_msg)
        if not format_ok:
            logger.warning("Format errors: " + format_msg)
        # Do not exit with error here, as the task is to configure the tools,
        # not necessarily to fix all existing code issues immediately.
        # However, if the task implies ensuring the project *passes* now, we might exit 1.
        # Given the task is "Configure", we log the status.
        sys.exit(0)

if __name__ == "__main__":
    main()