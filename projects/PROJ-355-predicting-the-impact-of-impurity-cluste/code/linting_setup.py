"""
Helper functions to check and install linting tools (ruff, black).
"""
import subprocess
import sys
from pathlib import Path
from config import get_project_root


def check_tool(tool_name: str) -> bool:
    """Check if a tool is installed and accessible."""
    try:
        subprocess.run([tool_name, "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def install_tool(tool_name: str) -> bool:
    """Attempt to install a tool using pip."""
    print(f"Attempting to install {tool_name}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", tool_name])
        return True
    except subprocess.CalledProcessError:
        print(f"Failed to install {tool_name}.")
        return False


def main():
    """Main entry point to ensure tools are installed."""
    tools = ["ruff", "black"]
    all_good = True

    for tool in tools:
        if not check_tool(tool):
            print(f"{tool} is missing.")
            if install_tool(tool):
                print(f"{tool} installed successfully.")
            else:
                print(f"Could not install {tool}. Please install manually: pip install {tool}")
                all_good = False
        else:
            print(f"{tool} is already installed.")

    if all_good:
        print("All linting and formatting tools are ready.")
    else:
        print("Some tools are missing. Pipeline may fail on linting steps.")
        sys.exit(1)


if __name__ == "__main__":
    main()