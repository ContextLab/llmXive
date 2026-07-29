"""
Linting and Formatting Setup Script.

This script configures the project's linting (ruff/flake8) and formatting (black)
tools by generating the necessary configuration files and verifying installation.
"""
import subprocess
import sys
import os
import logging
from typing import Tuple, Optional

# Configure logging for this script
logger = logging.getLogger(__name__)

def check_tool_installed(tool_name: str) -> bool:
    """
    Check if a specific tool is installed in the current environment.

    Args:
        tool_name: The name of the tool to check (e.g., 'ruff', 'black').

    Returns:
        True if the tool is installed, False otherwise.
    """
    try:
        subprocess.run([tool_name, "--version"], capture_output=True, check=True)
        logger.info(f"Tool '{tool_name}' is installed.")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.warning(f"Tool '{tool_name}' is not installed.")
        return False

def install_tool(tool_name: str) -> bool:
    """
    Install a specific tool using pip.

    Args:
        tool_name: The name of the tool to install.

    Returns:
        True if installation was successful, False otherwise.
    """
    logger.info(f"Attempting to install '{tool_name}'...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", tool_name])
        logger.info(f"Successfully installed '{tool_name}'.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install '{tool_name}': {e}")
        return False

def create_ruff_config() -> None:
    """
    Create a ruff.toml configuration file with project-specific settings.
    """
    config_content = """# Ruff configuration for PROJ-243
target-version = "py311"

[lint]
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # Pyflakes
    "I",  # isort
    "C",  # flake8-comprehensions
    "B",  # flake8-bugbear
]
ignore = [
    "E501", # line too long (handled by black)
    "B008", # do not perform function calls in argument defaults
    "C901", # too complex
]

[lint.isort]
known-first-party = ["code", "utils"]
"""
    config_path = os.path.join("code", "ruff.toml")
    with open(config_path, "w", encoding="utf-8") as f:
        f.write(config_content)
    logger.info(f"Created ruff configuration at {config_path}")

def create_black_config() -> None:
    """
    Create a pyproject.toml section for Black configuration if not exists,
    or a black configuration file.
    """
    pyproject_path = os.path.join("code", "pyproject.toml")
    
    # Check if pyproject.toml exists
    if os.path.exists(pyproject_path):
        with open(pyproject_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        if "[tool.black]" in content:
            logger.info("Black configuration already exists in pyproject.toml")
            return
    else:
        content = ""

    black_config = """
[tool.black]
line-length = 88
target-version = ['py311']
include = '\\.pyi?$'
"""
    
    # Append black config
    with open(pyproject_path, "w", encoding="utf-8") as f:
        f.write(content + black_config)
    
    logger.info(f"Created/updated Black configuration in {pyproject_path}")

def run_flake8_check() -> Tuple[bool, Optional[str]]:
    """
    Run flake8 (or ruff as a drop-in replacement) to check for linting errors.

    Returns:
        Tuple of (success: bool, error_message: Optional[str])
    """
    # Prefer ruff if installed, otherwise fall back to flake8
    tool = "ruff" if check_tool_installed("ruff") else "flake8"
    
    if tool == "ruff":
        cmd = ["ruff", "check", "code/"]
    else:
        cmd = ["flake8", "code/"]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode == 0:
            logger.info("Linting check passed.")
            return True, None
        else:
            logger.warning(f"Linting check found issues:\n{result.stdout}\n{result.stderr}")
            return False, result.stdout + result.stderr
    except FileNotFoundError:
        logger.error(f"Neither '{tool}' nor 'flake8' is installed.")
        return False, f"Tool '{tool}' not found."

def run_black_check() -> Tuple[bool, Optional[str]]:
    """
    Run black --check to verify formatting.

    Returns:
        Tuple of (success: bool, error_message: Optional[str])
    """
    cmd = ["black", "--check", "code/"]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode == 0:
            logger.info("Formatting check passed.")
            return True, None
        else:
            logger.warning(f"Formatting check found issues:\n{result.stdout}\n{result.stderr}")
            return False, result.stdout + result.stderr
    except FileNotFoundError:
        logger.error("Black is not installed.")
        return False, "Black not found."

def main() -> int:
    """
    Main entry point for the linting setup script.
    
    Returns:
        Exit code (0 for success, 1 for failure).
    """
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info("Starting linting and formatting setup...")
    
    # Ensure code directory exists
    code_dir = "code"
    if not os.path.exists(code_dir):
        os.makedirs(code_dir)
        logger.info(f"Created directory: {code_dir}")
    
    # Install tools if necessary
    tools_needed = [("ruff", "ruff"), ("black", "black")]
    for display_name, pkg_name in tools_needed:
        if not check_tool_installed(display_name):
            if not install_tool(pkg_name):
                logger.error(f"Failed to install {display_name}. Exiting.")
                return 1
    
    # Generate configuration files
    create_ruff_config()
    create_black_config()
    
    # Run checks
    lint_ok, lint_err = run_flake8_check()
    fmt_ok, fmt_err = run_black_check()
    
    if lint_ok and fmt_ok:
        logger.info("All linting and formatting checks passed.")
        return 0
    else:
        logger.warning("Some checks failed. Please review the output above.")
        logger.info("To auto-fix formatting, run: black code/")
        logger.info("To fix linting issues, run: ruff check --fix code/")
        return 1

if __name__ == "__main__":
    sys.exit(main())