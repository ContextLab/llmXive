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
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def check_tool_installed(tool_name: str) -> bool:
    """Check if a tool is installed."""
    try:
        subprocess.run([tool_name, '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def install_tool(tool_name: str) -> None:
    """Install a tool using pip."""
    logging.info(f"Installing {tool_name}...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', tool_name], check=True)
        logging.info(f"{tool_name} installed successfully.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to install {tool_name}: {e}")
        sys.exit(1)

def create_ruff_config() -> None:
    """Create a default ruff configuration file."""
    config_content = """[tool.ruff]
select = ["E", "F", "W", "I", "N", "UP", "B", "C4", "ARG", "SIM"]
ignore = ["E501", "W503"]
line-length = 120
target-version = "py311"

[tool.ruff.per-file-ignores]
"__init__.py" = ["F401"]
"""
    config_path = os.path.join('code', 'ruff.toml')
    with open(config_path, 'w') as f:
        f.write(config_content)
    logging.info(f"Created ruff configuration at {config_path}")

def create_black_config() -> None:
    """Create a default black configuration in pyproject.toml."""
    config_path = os.path.join('code', 'pyproject.toml')
    # Check if file exists and append or create
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            content = f.read()
        if '[tool.black]' in content:
            logging.info("Black configuration already exists in pyproject.toml")
            return
        with open(config_path, 'a') as f:
            f.write("\n[tool.black]\nline-length = 120\ntarget-version = ['py311']\n")
    else:
        config_content = """[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[tool.black]
line-length = 120
target-version = ['py311']
"""
        with open(config_path, 'w') as f:
            f.write(config_content)
    logging.info(f"Created/updated Black configuration at {config_path}")

def run_flake8_check() -> Tuple[bool, str]:
    """Run flake8 check and return success status and output."""
    try:
        result = subprocess.run(
            ['flake8', 'code/'],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0:
            return True, "No linting issues found."
        else:
            return False, result.stdout
    except FileNotFoundError:
        return False, "flake8 is not installed."

def run_black_check() -> Tuple[bool, str]:
    """Run black check and return success status and output."""
    try:
        result = subprocess.run(
            ['black', '--check', 'code/'],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0:
            return True, "Code is formatted correctly."
        else:
            return False, result.stdout
    except FileNotFoundError:
        return False, "black is not installed."

def main():
    """Main function to set up linting and formatting tools."""
    logger = setup_script_logging()
    logger.info("Starting linting and formatting setup...")

    # Ensure directories exist
    ensure_directories(get_config())

    # Check and install tools
    tools = [
        ('ruff', 'ruff'),
        ('black', 'black'),
        ('flake8', 'flake8')
    ]

    for display_name, tool_name in tools:
        if not check_tool_installed(tool_name):
            logger.warning(f"{display_name} not found. Installing...")
            install_tool(tool_name)
        else:
            logger.info(f"{display_name} is already installed.")

    # Create configuration files
    create_ruff_config()
    create_black_config()

    # Run checks
    logger.info("Running initial linting and formatting checks...")
    
    flake8_ok, flake8_msg = run_flake8_check()
    if flake8_ok:
        logger.info(f"Flake8: {flake8_msg}")
    else:
        logger.warning(f"Flake8: {flake8_msg}")

    black_ok, black_msg = run_black_check()
    if black_ok:
        logger.info(f"Black: {black_msg}")
    else:
        logger.warning(f"Black: {black_msg}")

    logger.info("Linting and formatting setup complete.")

if __name__ == "__main__":
    main()