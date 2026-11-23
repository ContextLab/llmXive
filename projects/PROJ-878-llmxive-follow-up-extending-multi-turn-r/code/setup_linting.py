import subprocess
import sys
import logging
import os
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def check_tool(tool_name: str) -> bool:
    """Check if a tool is installed and accessible."""
    try:
        subprocess.run([tool_name, "--version"], check=True, capture_output=True, text=True)
        logger.info(f"✓ {tool_name} is installed.")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.warning(f"✗ {tool_name} is not installed.")
        return False

def install_tool(tool_name: str) -> bool:
    """Install a tool using pip."""
    logger.info(f"Installing {tool_name}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", tool_name])
        logger.info(f"✓ {tool_name} installed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"✗ Failed to install {tool_name}: {e}")
        return False

def main():
    """Main entry point to configure linting and formatting."""
    logger.info("Starting linting and formatting configuration...")

    tools = {
        "ruff": "ruff",
        "black": "black",
    }

    all_installed = True
    for friendly_name, cmd in tools.items():
        if not check_tool(cmd):
            if not install_tool(cmd):
                all_installed = False

    if not all_installed:
        logger.error("Some tools failed to install. Please check the logs.")
        sys.exit(1)

    logger.info("All tools installed. Configuration files (.ruff.toml, pyproject.toml) should be present in the project root.")
    logger.info("Run 'ruff check .' to lint and 'black .' to format.")

if __name__ == "__main__":
    main()