"""
Setup script to ensure linting and formatting tools are configured.
This script validates the pyproject.toml configuration.
"""

import json
import os
import sys
from pathlib import Path

try:
    import tomli
except ImportError:
    try:
        import tomllib as tomli
    except ImportError:
        # Fallback for older Python versions without tomllib
        print("Installing tomli for parsing pyproject.toml...")
        import subprocess

        subprocess.check_call([sys.executable, "-m", "pip", "install", "tomli"])
        import tomli


def create_ruff_config():
    """Validate and return ruff configuration details."""
    return {
        "tool": "ruff",
        "line_length": 88,
        "target_version": "py311",
        "checks": [
            "E",
            "W",
            "F",
            "I",
            "B",
            "C4",
            "UP",
        ],
    }


def create_black_config():
    """Validate and return black configuration details."""
    return {
        "tool": "black",
        "line_length": 88,
        "target_version": ["py311"],
    }


def main():
    """Main entry point to validate linting configuration."""
    project_root = Path(__file__).resolve().parent.parent
    pyproject_path = project_root / "pyproject.toml"

    if not pyproject_path.exists():
        print("ERROR: pyproject.toml not found. Please run setup first.")
        sys.exit(1)

    try:
        with open(pyproject_path, "rb") as f:
            config = tomli.load(f)
    except Exception as e:
        print(f"ERROR: Failed to parse pyproject.toml: {e}")
        sys.exit(1)

    # Validate Ruff
    if "tool" not in config or "ruff" not in config["tool"]:
        print("ERROR: [tool.ruff] section missing in pyproject.toml")
        sys.exit(1)

    ruff_config = config["tool"]["ruff"]
    if ruff_config.get("line-length") != 88:
        print(f"ERROR: Ruff line-length must be 88, got {ruff_config.get('line-length')}")
        sys.exit(1)

    if ruff_config.get("target-version") != "py311":
        print(f"ERROR: Ruff target-version must be py311, got {ruff_config.get('target-version')}")
        sys.exit(1)

    print("✓ Ruff configuration valid")

    # Validate Black
    if "tool" not in config or "black" not in config["tool"]:
        print("ERROR: [tool.black] section missing in pyproject.toml")
        sys.exit(1)

    black_config = config["tool"]["black"]
    if black_config.get("line-length") != 88:
        print(f"ERROR: Black line-length must be 88, got {black_config.get('line-length')}")
        sys.exit(1)

    target_versions = black_config.get("target-version", [])
    if not isinstance(target_versions, list) or "py311" not in target_versions:
        print(f"ERROR: Black target-version must include py311, got {target_versions}")
        sys.exit(1)

    print("✓ Black configuration valid")
    print("Linting and formatting configuration validated successfully.")


if __name__ == "__main__":
    main()