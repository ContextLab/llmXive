"""
Script to check and install linting and formatting tools.
"""
import subprocess
import sys
import os
import logging
from typing import Tuple, Optional

logger = logging.getLogger("setup_linting")

def check_tool_installed(tool_name: str) -> bool:
    """Check if a tool is installed."""
    try:
        subprocess.run([tool_name, "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def install_tool(tool_name: str) -> bool:
    """Install a tool using pip."""
    logger.info(f"Installing {tool_name}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", tool_name])
        return True
    except subprocess.CalledProcessError:
        logger.error(f"Failed to install {tool_name}")
        return False

def run_flake8_check() -> Tuple[bool, str]:
    """Run flake8 check."""
    try:
        result = subprocess.run(["flake8", "code"], capture_output=True, text=True)
        if result.returncode == 0:
            return True, "Flake8 passed."
        else:
            return False, f"Flake8 issues found:\n{result.stdout}\n{result.stderr}"
    except FileNotFoundError:
        return False, "Flake8 not installed."

def run_black_check() -> Tuple[bool, str]:
    """Run black check."""
    try:
        result = subprocess.run(["black", "--check", "code"], capture_output=True, text=True)
        if result.returncode == 0:
            return True, "Black passed."
        else:
            return False, f"Black issues found:\n{result.stdout}\n{result.stderr}"
    except FileNotFoundError:
        return False, "Black not installed."

def main():
    """Main entry point."""
    logging.basicConfig(level=logging.INFO)
    
    tools = ["flake8", "black"]
    for tool in tools:
        if not check_tool_installed(tool):
            logger.warning(f"{tool} not found. Attempting to install...")
            if not install_tool(tool):
                logger.error(f"Could not install {tool}. Please install manually.")
                sys.exit(1)
    
    flake8_ok, flake8_msg = run_flake8_check()
    black_ok, black_msg = run_black_check()
    
    print(flake8_msg)
    print(black_msg)
    
    if not flake8_ok or not black_ok:
        sys.exit(1)

if __name__ == "__main__":
    main()
