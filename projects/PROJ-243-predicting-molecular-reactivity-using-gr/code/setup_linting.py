import subprocess
import sys
import os
import logging
from typing import Tuple, Optional
from config import ensure_directories, get_config

def setup_script_logging():
    """Initialize logging for the script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def check_tool_installed(tool_name: str) -> Tuple[bool, str]:
    """Check if a tool is installed via pip."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", tool_name],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0:
            return True, "Installed"
        else:
            return False, "Not installed"
    except Exception as e:
        return False, f"Error checking: {str(e)}"

def install_tool(tool_name: str, logger: logging.Logger) -> bool:
    """Install a tool via pip."""
    logger.info(f"Installing {tool_name}...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", tool_name],
            capture_output=True,
            text=True,
            check=True
        )
        logger.info(f"{tool_name} installed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install {tool_name}: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error installing {tool_name}: {str(e)}")
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
    "E501", # line too long (handled by black)
    "B008", # do not perform function calls in argument defaults
]

[format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"
"""
    config_path = os.path.join("code", "ruff.toml")
    try:
        with open(config_path, 'w') as f:
            f.write(config_content)
        logger.info(f"Created ruff config at {config_path}")
    except Exception as e:
        logger.error(f"Failed to create ruff config: {str(e)}")

def create_black_config(logger: logging.Logger):
    """Create a pyproject.toml configuration file for black if it doesn't exist."""
    config_path = os.path.join("code", "pyproject.toml")
    black_section = """[tool.black]
line-length = 88
target-version = ['py311']
include = '\\.pyi?$'
exclude = '''
/(
    \\.(git|hg|svn|bzr)
    | __pycache__
    | build
    | dist
)/
'''
"""
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                content = f.read()
                if "[tool.black]" not in content:
                    with open(config_path, 'a') as f:
                        f.write("\n" + black_section)
                    logger.info(f"Appended black config to {config_path}")
                else:
                    logger.info(f"Black config already exists in {config_path}")
        else:
            with open(config_path, 'w') as f:
                f.write(black_section)
            logger.info(f"Created pyproject.toml with black config at {config_path}")
    except Exception as e:
        logger.error(f"Failed to create/update black config: {str(e)}")

def run_flake8_check(logger: logging.Logger) -> bool:
    """Run flake8 check on the code directory."""
    logger.info("Running flake8 check...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "flake8", "code/"],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0:
            logger.info("Flake8 check passed.")
            return True
        else:
            logger.warning("Flake8 check found issues:")
            logger.warning(result.stdout)
            return False
    except Exception as e:
        logger.error(f"Error running flake8: {str(e)}")
        return False

def run_black_check(logger: logging.Logger) -> bool:
    """Run black check (diff mode) on the code directory."""
    logger.info("Running black check...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "black", "--check", "--diff", "code/"],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0:
            logger.info("Black check passed.")
            return True
        else:
            logger.warning("Black check found formatting issues.")
            if result.stdout:
                logger.warning(result.stdout)
            return False
    except Exception as e:
        logger.error(f"Error running black: {str(e)}")
        return False

def main():
    """Main entry point for setting up linting and formatting tools."""
    logger = setup_script_logging()
    logger.info("Starting setup of linting and formatting tools...")

    # Ensure directories exist
    config = get_config()
    ensure_directories(config)

    # Check and install Ruff
    is_installed, status = check_tool_installed("ruff")
    if not is_installed:
        logger.warning(f"Ruff is {status}. Attempting to install...")
        if not install_tool("ruff", logger):
            logger.error("Failed to install Ruff. Exiting.")
            sys.exit(1)
    else:
        logger.info("Ruff is already installed.")

    # Check and install Black
    is_installed, status = check_tool_installed("black")
    if not is_installed:
        logger.warning(f"Black is {status}. Attempting to install...")
        if not install_tool("black", logger):
            logger.error("Failed to install Black. Exiting.")
            sys.exit(1)
    else:
        logger.info("Black is already installed.")

    # Create configuration files
    create_ruff_config(logger)
    create_black_config(logger)

    # Run initial checks (non-fatal, just informational)
    run_flake8_check(logger)
    run_black_check(logger)

    logger.info("Setup of linting and formatting tools completed.")

if __name__ == "__main__":
    main()