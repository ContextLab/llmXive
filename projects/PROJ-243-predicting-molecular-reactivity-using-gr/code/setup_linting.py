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
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def check_tool_installed(tool_name: str) -> Tuple[bool, str]:
    """Check if a tool is installed and return version or error."""
    try:
        result = subprocess.run(
            [tool_name, '--version'],
            capture_output=True,
            text=True,
            check=True
        )
        return True, result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        return False, str(e)

def install_tool(tool_name: str) -> bool:
    """Install a tool using pip."""
    logging.info(f"Installing {tool_name}...")
    try:
        subprocess.run(
            [sys.executable, '-m', 'pip', 'install', tool_name],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        logging.info(f"{tool_name} installed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to install {tool_name}: {e.stderr.decode()}")
        return False

def create_ruff_config():
    """Create a .ruff.toml configuration file."""
    config_content = """# Ruff configuration for llmXive project
[lint]
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # Pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade
]
ignore = [
    "E501", # line too long (handled by black)
    "B008", # do not perform function calls in argument defaults
]

[lint.isort]
known-first-party = ["code", "tests", "utils"]

[format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"
"""
    config_path = os.path.join(os.getcwd(), '.ruff.toml')
    with open(config_path, 'w') as f:
        f.write(config_content)
    logging.info(f"Created {config_path}")

def create_black_config():
    """Create a pyproject.toml configuration for Black if not exists or update it."""
    config_path = os.path.join(os.getcwd(), 'pyproject.toml')
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

[tool.ruff]
# Inherit settings from .ruff.toml if it exists, otherwise define here
lint.select = ["E", "W", "F", "I", "B", "C4", "UP"]
lint.ignore = ["E501"]
"""
    
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            content = f.read()
        if '[tool.black]' not in content:
            with open(config_path, 'a') as f:
                f.write(black_section)
            logging.info(f"Updated {config_path} with Black settings.")
        else:
            logging.info(f"{config_path} already contains Black settings.")
    else:
        with open(config_path, 'w') as f:
            f.write(black_section)
        logging.info(f"Created {config_path} with Black settings.")

def run_flake8_check() -> bool:
    """Run flake8 (or ruff as drop-in) to check code style."""
    logging.info("Running style check (ruff/flake8)...")
    try:
        # Use ruff as the primary linter since we configured it
        result = subprocess.run(
            ['ruff', 'check', 'code/', 'tests/'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            logging.info("Style check passed.")
            return True
        else:
            logging.warning("Style check found issues:\n" + result.stdout)
            return False
    except FileNotFoundError:
        logging.error("ruff not found. Please install it.")
        return False

def run_black_check() -> bool:
    """Run black to check formatting."""
    logging.info("Running format check (black)...")
    try:
        result = subprocess.run(
            ['black', '--check', 'code/', 'tests/'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            logging.info("Format check passed.")
            return True
        else:
            logging.warning("Format check found issues:\n" + result.stdout)
            return False
    except FileNotFoundError:
        logging.error("black not found. Please install it.")
        return False

def main():
    """Main entry point for linting and formatting setup."""
    logger = setup_script_logging()
    ensure_directories()
    
    # Ensure config directory exists if needed, though configs are root-level
    config = get_config()
    
    # 1. Check and Install Tools
    tools = [('ruff', 'ruff'), ('black', 'black')]
    for name, pkg in tools:
        installed, msg = check_tool_installed(name)
        if not installed:
            logger.info(f"{name} not found ({msg}). Attempting installation...")
            if not install_tool(pkg):
                logger.error(f"Could not install {name}. Aborting.")
                sys.exit(1)
        else:
            logger.info(f"{name} found: {msg}")

    # 2. Create Configuration Files
    create_ruff_config()
    create_black_config()

    # 3. Run Checks (Non-fatal for setup, but informative)
    logger.info("Running initial checks on existing code...")
    run_flake8_check()
    run_black_check()

    logger.info("Linting and formatting configuration complete.")

if __name__ == '__main__':
    main()