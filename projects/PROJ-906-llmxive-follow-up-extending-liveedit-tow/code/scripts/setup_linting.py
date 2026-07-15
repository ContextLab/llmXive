"""
Script to verify linting (ruff) and formatting (black) configuration.
This script checks that the tools are installed and the configuration files exist.
"""
import subprocess
import sys
import os
import tomli
from pathlib import Path

def check_tool_installed(tool_name: str) -> bool:
    """Check if a tool is installed and accessible."""
    try:
        subprocess.run(
            [tool_name, "--version"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def verify_config(project_root: Path) -> bool:
    """Verify that pyproject.toml exists and contains valid ruff/black sections."""
    config_path = project_root / "pyproject.toml"
    if not config_path.exists():
        print("ERROR: pyproject.toml not found.")
        return False

    try:
        with open(config_path, "rb") as f:
            config = tomli.load(f)
    except tomli.TOMLDecodeError as e:
        print(f"ERROR: Invalid TOML in pyproject.toml: {e}")
        return False

    if "tool" not in config:
        print("ERROR: 'tool' section missing in pyproject.toml.")
        return False

    if "black" not in config["tool"]:
        print("WARNING: 'tool.black' section not found. Black may not be configured.")
    else:
        print("OK: Black configuration found.")

    if "ruff" not in config["tool"]:
        print("WARNING: 'tool.ruff' section not found. Ruff may not be configured.")
    else:
        print("OK: Ruff configuration found.")

    return True

def main():
    """Main entry point for the setup verification script."""
    # Determine project root (assuming script is in code/scripts/)
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent

    print(f"Checking project at: {project_root}")
    print("-" * 40)

    # Check tools
    tools = ["black", "ruff"]
    all_installed = True
    for tool in tools:
        installed = check_tool_installed(tool)
        status = "INSTALLED" if installed else "MISSING"
        print(f"{tool:10} : {status}")
        if not installed:
            all_installed = False

    print("-" * 40)

    # Check config
    config_valid = verify_config(project_root)

    print("-" * 40)
    if all_installed and config_valid:
        print("SUCCESS: Linting and formatting tools are configured correctly.")
        sys.exit(0)
    else:
        print("FAILURE: Linting/Formatting setup is incomplete.")
        if not all_installed:
            print("  -> Install missing tools: pip install black ruff")
        sys.exit(1)

if __name__ == "__main__":
    main()