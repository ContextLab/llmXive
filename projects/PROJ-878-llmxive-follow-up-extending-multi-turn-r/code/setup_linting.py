"""
Script to verify and install linting and formatting tools (ruff, black).
"""
import subprocess
import sys
import logging

def check_tool(tool_name: str) -> bool:
    """Check if a tool is installed and returns its version."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", tool_name, "--version"],
            capture_output=True,
            text=True,
            check=True,
        )
        logging.info(f"{tool_name} is installed: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError:
        logging.warning(f"{tool_name} is not installed or not working.")
        return False

def install_tool(tool_name: str) -> bool:
    """Install a tool using pip."""
    logging.info(f"Installing {tool_name}...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", tool_name],
            check=True,
        )
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to install {tool_name}: {e}")
        return False

def main():
    """Main entry point for linting setup."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    tools = ["ruff", "black"]
    all_installed = True

    for tool in tools:
        if not check_tool(tool):
            if install_tool(tool):
                if not check_tool(tool):
                    all_installed = False
            else:
                all_installed = False

    if all_installed:
        logging.info("All linting and formatting tools are ready.")
    else:
        logging.error("Some tools could not be installed or verified.")
        sys.exit(1)

if __name__ == "__main__":
    main()