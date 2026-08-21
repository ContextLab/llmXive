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
        handler.setFormatter(logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        ))
        logger.addHandler(handler)
    return logger

def check_tool_installed(tool_name: str) -> bool:
    """Check if a tool is installed in the current environment."""
    try:
        subprocess.run([sys.executable, "-m", tool_name, "--version"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def install_tool(tool_name: str, logger: logging.Logger) -> bool:
    """Install a tool using pip."""
    logger.info(f"Installing {tool_name}...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-U", tool_name],
                       check=True)
        logger.info(f"{tool_name} installed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install {tool_name}: {e}")
        return False

def create_ruff_config(logger: logging.Logger) -> str:
    """Create a ruff.toml configuration file."""
    config_path = "ruff.toml"
    content = """[lint]
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
known-first-party = ["code", "tests", "utils", "config"]

[format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"
"""
    with open(config_path, "w") as f:
        f.write(content)
    logger.info(f"Created {config_path}")
    return config_path

def create_black_config(logger: logging.Logger) -> str:
    """Create a pyproject.toml configuration file for Black."""
    config_path = "pyproject.toml"
    # Check if file exists to avoid overwriting other configs
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            content = f.read()
        if "[tool.black]" in content:
            logger.info(f"{config_path} already contains Black config.")
            return config_path
        # Append if exists but doesn't have black section
        with open(config_path, "a") as f:
            f.write("\n[tool.black]\n")
            f.write('line-length = 88\n')
            f.write('target-version = ["py311"]\n')
    else:
        content = """[tool.black]
line-length = 88
target-version = ["py311"]

[tool.isort]
profile = "black"
"""
        with open(config_path, "w") as f:
            f.write(content)
    logger.info(f"Updated {config_path} with Black/Isort config")
    return config_path

def run_flake8_check(logger: logging.Logger) -> bool:
    """Run flake8 check (optional, for verification)."""
    if not check_tool_installed("flake8"):
        logger.warning("flake8 not installed, skipping check.")
        return True
    try:
        logger.info("Running flake8 check...")
        # Ignore E501 as it's handled by black
        result = subprocess.run(
            [sys.executable, "-m", "flake8", "code/", "tests/", "--ignore=E501,W503,W504"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.returncode == 0:
            logger.info("flake8 check passed.")
            return True
        else:
            logger.warning("flake8 found issues:\n" + result.stdout)
            return False
    except Exception as e:
        logger.error(f"Error running flake8: {e}")
        return False

def run_black_check(logger: logging.Logger) -> bool:
    """Run black check (optional, for verification)."""
    if not check_tool_installed("black"):
        logger.warning("black not installed, skipping check.")
        return True
    try:
        logger.info("Running black check...")
        result = subprocess.run(
            [sys.executable, "-m", "black", "--check", "code/", "tests/"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.returncode == 0:
            logger.info("black check passed.")
            return True
        else:
            logger.warning("black found formatting issues. Run 'black code/ tests/' to fix.")
            return False
    except Exception as e:
        logger.error(f"Error running black: {e}")
        return False

def main() -> int:
    """Main entry point for setting up linting and formatting."""
    logger = setup_script_logging()
    logger.info("Starting linting and formatting setup...")

    # Ensure directories exist
    config = get_config()
    ensure_directories(config)

    # 1. Install Ruff
    if not check_tool_installed("ruff"):
        if not install_tool("ruff", logger):
            logger.error("Failed to install ruff. Exiting.")
            return 1

    # 2. Install Black
    if not check_tool_installed("black"):
        if not install_tool("black", logger):
            logger.error("Failed to install black. Exiting.")
            return 1

    # 3. Create Configuration Files
    create_ruff_config(logger)
    create_black_config(logger)

    # 4. Verify (Optional but good practice)
    run_flake8_check(logger)
    run_black_check(logger)

    logger.info("Linting and formatting setup complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())