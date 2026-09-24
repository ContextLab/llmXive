"""
Linting and formatting setup utilities for the project.
Provides functions to check tool availability and install them if missing.
"""
import subprocess
import sys
from pathlib import Path

from config import get_project_root


def check_tool(tool_name: str) -> bool:
    """
    Check if a specific tool (ruff or black) is installed.

    Args:
        tool_name: Name of the tool to check (e.g., 'ruff', 'black').

    Returns:
        True if the tool is installed and executable, False otherwise.
    """
    try:
        subprocess.run(
            [tool_name, "--version"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def install_tool(tool_name: str) -> bool:
    """
    Install a specific tool using pip if it is not already installed.

    Args:
        tool_name: Name of the tool to install (e.g., 'ruff', 'black').

    Returns:
        True if installation was successful or tool was already installed,
        False if installation failed.
    """
    if check_tool(tool_name):
        print(f"✓ {tool_name} is already installed.")
        return True

    print(f"Installing {tool_name}...")
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", tool_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        print(f"✓ {tool_name} installed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install {tool_name}: {e}")
        return False


def main() -> int:
    """
    Main entry point for linting setup.
    Ensures ruff and black are installed and configuration files are valid.

    Returns:
        0 on success, 1 on failure.
    """
    project_root = get_project_root()
    print(f"Setting up linting tools in: {project_root}")

    tools = ["ruff", "black"]
    all_success = True

    for tool in tools:
        if not install_tool(tool):
            all_success = False

    if not all_success:
        print("\nFailed to install some tools. Please install them manually.")
        return 1

    # Verify configuration files exist
    pyproject = project_root / "pyproject.toml"
    if not pyproject.exists():
        print(f"✗ Configuration file {pyproject} not found.")
        return 1

    print(f"\n✓ Linting setup complete. Configuration found in {pyproject}")
    print("Run 'ruff check .' to check for issues.")
    print("Run 'black .' to format code.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
