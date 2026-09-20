"""
Setup script to install linting and formatting tools.
"""
import subprocess
import sys
from pathlib import Path
from config import get_project_root


def check_tool(tool_name: str, version: str) -> bool:
    """
    Check if a tool is installed with the correct version.

    Args:
        tool_name: Name of the tool (e.g., 'ruff', 'black').
        version: Expected version string (e.g., '0.1.0').

    Returns:
        True if the tool is installed with the correct version, False otherwise.
    """
    try:
        result = subprocess.run(
            [tool_name, "--version"],
            capture_output=True,
            text=True,
            check=True,
            cwd=get_project_root(),
        )
        # Simple version check (might need refinement for complex version strings)
        output = result.stdout.strip()
        if version in output:
            print(f"✓ {tool_name} {version} is installed.")
            return True
        else:
            print(f"⚠ {tool_name} found but version mismatch. Expected {version}, got: {output}")
            return False
    except subprocess.CalledProcessError:
        print(f"✗ {tool_name} is not installed.")
        return False
    except FileNotFoundError:
        print(f"✗ {tool_name} command not found.")
        return False


def install_tool(tool_name: str, version: str) -> bool:
    """
    Install a tool with a specific version.

    Args:
        tool_name: Name of the tool.
        version: Version to install.

    Returns:
        True if installation was successful, False otherwise.
    """
    print(f"Installing {tool_name}=={version}...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", f"{tool_name}=={version}"],
            check=True,
            cwd=get_project_root(),
        )
        print(f"✓ {tool_name}=={version} installed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install {tool_name}=={version}: {e}")
        return False


def main() -> int:
    """
    Main entry point for the linting setup script.
    """
    print("Setting up linting and formatting tools...")
    root = get_project_root()
    print(f"Project Root: {root}")

    tools = [
        ("ruff", "0.1.0"),
        ("black", "23.10.0"),
    ]

    all_installed = True
    for tool, version in tools:
        if not check_tool(tool, version):
            if not install_tool(tool, version):
                all_installed = False

    if all_installed:
        print("\n✓ All tools installed and verified.")
        return 0
    else:
        print("\n✗ Some tools failed to install.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
