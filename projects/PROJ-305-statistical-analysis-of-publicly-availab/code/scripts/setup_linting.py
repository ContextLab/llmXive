"""
Script to set up linting and formatting tools for the project.
This task (T003) configures ruff and black.
"""
import os
import sys
from pathlib import Path


def main():
    """
    Verify that linting and formatting tools are configured.
    Checks for the presence of configuration files: pyproject.toml, .ruff.toml, .flake8
    """
    project_root = Path(__file__).parent.parent

    # Required configuration files
    config_files = [
        "pyproject.toml",
        ".ruff.toml",
        ".flake8",
    ]

    missing_files = []
    for config_file in config_files:
        config_path = project_root / config_file
        if not config_path.exists():
            missing_files.append(config_file)
        else:
            print(f"[OK] Found configuration: {config_file}")

    if missing_files:
        print(f"[ERROR] Missing configuration files: {missing_files}")
        print("Please ensure these files are created with appropriate settings.")
        sys.exit(1)

    # Verify tools are available
    tools = ["ruff", "black"]
    missing_tools = []

    for tool in tools:
        try:
            import importlib.util
            spec = importlib.util.find_spec(tool)
            if spec is None:
                missing_tools.append(tool)
            else:
                print(f"[OK] Tool available: {tool}")
        except (ImportError, ModuleNotFoundError):
            missing_tools.append(tool)

    if missing_tools:
        print(f"[WARNING] Tools not installed: {missing_tools}")
        print("Install with: pip install {' '.join(missing_tools)}")
        # Don't exit with error here as this is a setup script

    print("\nLinting and formatting configuration verified.")
    print("Run 'ruff check . --fix' and 'black .' to format code.")


if __name__ == "__main__":
    main()