"""
config_linting.py

Handles configuration file checks and tool availability verification.
"""

import os
import subprocess
import sys
from pathlib import Path

def ensure_config_files() -> bool:
    """
    Ensure required configuration files exist.
    Returns True if all required files are present, False otherwise.
    """
    config_files = [
        "pyproject.toml",
        ".ruff.toml",
        ".flake8",
        ".black",
    ]
    missing = []
    for cfg in config_files:
        if not Path(cfg).exists():
            missing.append(cfg)

    if missing:
        print(f"Missing configuration files: {', '.join(missing)}", file=sys.stderr)
        return False
    return True


def check_tool_availability() -> Dict[str, bool]:
    """
    Check if required linting and formatting tools are available in PATH.
    Returns a dict of tool_name -> is_available.
    """
    tools = ["ruff", "flake8", "black"]
    availability = {}

    for tool in tools:
        try:
            subprocess.run(
                [tool, "--version"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
            )
            availability[tool] = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            availability[tool] = False

    return availability


def main() -> None:
    """Main entry point for configuration checks."""
    print("Checking configuration files...")
    config_ok = ensure_config_files()

    print("Checking tool availability...")
    tools = check_tool_availability()
    for tool, available in tools.items():
        status = "OK" if available else "MISSING"
        print(f"  {tool}: {status}")

    if not config_ok or not all(tools.values()):
        print("Configuration or tools incomplete.", file=sys.stderr)
        sys.exit(1)
    else:
        print("All checks passed.")
        sys.exit(0)


if __name__ == "__main__":
    main()
