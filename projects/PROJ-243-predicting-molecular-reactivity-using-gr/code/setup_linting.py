import subprocess
import sys
import os
import logging
from typing import Tuple, Optional
from config import ensure_directories, get_config

def setup_script_logging() -> logging.Logger:
    """Setup logging for the linting setup script."""
    logger = logging.getLogger("setup_linting")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
    return logger

def check_tool_installed(tool_name: str) -> bool:
    """Check if a tool is installed."""
    try:
        subprocess.run([tool_name, "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def install_tool(tool_name: str, logger: logging.Logger) -> bool:
    """Install a tool using pip."""
    logger.info(f"Installing {tool_name}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", tool_name])
        logger.info(f"{tool_name} installed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install {tool_name}: {e}")
        return False

def create_ruff_config(logger: logging.Logger) -> str:
    """Create a default ruff.toml configuration file."""
    config_path = "ruff.toml"
    if os.path.exists(config_path):
        logger.info(f"{config_path} already exists, skipping creation.")
        return config_path

    config_content = """[lint]
select = ["E", "F", "W", "I", "N", "UP", "B", "C4", "PIE", "SIM", "T20"]
ignore = ["E501", "F401", "F811"]

[lint.per-file-ignores]
"__init__.py" = ["F401"]

[format]
quote-style = "double"
indent-style = "space"
line-ending = "auto"
"""
    with open(config_path, "w") as f:
        f.write(config_content)
    logger.info(f"Created {config_path}")
    return config_path

def create_black_config(logger: logging.Logger) -> str:
    """Create a pyproject.toml configuration file for Black if not present."""
    config_path = "pyproject.toml"
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            content = f.read()
            if "[tool.black]" in content:
                logger.info(f"[tool.black] section already exists in {config_path}, skipping creation.")
                return config_path

    with open(config_path, "a") as f:
        f.write("\n[tool.black]\nline-length = 88\ntarget-version = ['py311']\n")
    logger.info(f"Added [tool.black] section to {config_path}")
    return config_path

def run_flake8_check(logger: logging.Logger) -> bool:
    """Run flake8 check (deprecated, but kept for legacy compatibility)."""
    logger.info("Running flake8 check (deprecated, using ruff instead)...")
    if not check_tool_installed("flake8"):
        logger.warning("flake8 not installed. Skipping.")
        return False
    try:
        subprocess.run(["flake8", "code/"], check=False)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"flake8 check failed: {e}")
        return False

def run_black_check(logger: logging.Logger) -> bool:
    """Run black check."""
    logger.info("Running black check...")
    if not check_tool_installed("black"):
        logger.warning("black not installed. Skipping.")
        return False
    try:
        result = subprocess.run(["black", "--check", "code/"], capture_output=True, text=True)
        if result.returncode != 0:
            logger.warning("Code is not formatted according to Black standards.")
            logger.warning(result.stdout)
            logger.warning(result.stderr)
        else:
            logger.info("Code is formatted correctly according to Black standards.")
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        logger.error(f"black check failed: {e}")
        return False

def main() -> int:
    """Main entry point for the setup_linting script."""
    logger = setup_script_logging()
    logger.info("Starting linting and formatting setup...")

    # Ensure directories exist
    config = get_config()
    ensure_directories(config)

    # Install tools
    tools = ["ruff", "black"]
    for tool in tools:
        if not check_tool_installed(tool):
            if not install_tool(tool, logger):
                logger.error(f"Could not install {tool}. Exiting.")
                return 1

    # Create config files
    create_ruff_config(logger)
    create_black_config(logger)

    # Run checks
    logger.info("Running initial checks...")
    black_ok = run_black_check(logger)
    # flake8 is deprecated, ruff is the recommended tool
    # run_flake8_check(logger)

    if not black_ok:
        logger.warning("Initial formatting check failed. Please run 'black code/' to fix.")

    logger.info("Linting and formatting setup complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())