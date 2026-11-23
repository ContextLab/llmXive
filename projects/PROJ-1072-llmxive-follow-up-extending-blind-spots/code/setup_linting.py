"""
Script to verify and initialize linting and formatting configuration.
This script checks if ruff and black are installed and validates the configuration.
"""
import subprocess
import sys
import tomllib
from pathlib import Path

def check_tool_installed(tool_name: str) -> bool:
    """Check if a tool is installed in the current environment."""
    try:
        subprocess.run(
            [sys.executable, "-m", tool_name, "--version"],
            check=True,
            capture_output=True,
        )
        return True
    except subprocess.CalledProcessError:
        return False

def validate_pyproject() -> bool:
    """Validate that pyproject.toml exists and contains tool configurations."""
    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        print("ERROR: pyproject.toml not found.")
        return False

    try:
        with open(pyproject_path, "rb") as f:
            config = tomllib.load(f)
    except Exception as e:
        print(f"ERROR: Failed to parse pyproject.toml: {e}")
        return False

    has_black = "tool.black" in config
    has_ruff = "tool.ruff" in config

    if not has_black:
        print("WARNING: Black configuration not found in pyproject.toml")
    if not has_ruff:
        print("WARNING: Ruff configuration not found in pyproject.toml")

    return has_black and has_ruff

def main():
    print("=== Linting and Formatting Setup Verification ===")

    # Check tools
    black_ok = check_tool_installed("black")
    ruff_ok = check_tool_installed("ruff")

    if not black_ok:
        print("ERROR: Black is not installed. Run: pip install black")
        sys.exit(1)
    else:
        print("✓ Black is installed.")

    if not ruff_ok:
        print("ERROR: Ruff is not installed. Run: pip install ruff")
        sys.exit(1)
    else:
        print("✓ Ruff is installed.")

    # Validate config
    if not validate_pyproject():
        print("ERROR: Configuration validation failed.")
        sys.exit(1)

    print("✓ Configuration validated successfully.")
    print("\nTo format code, run: black code/ tests/")
    print("To lint code, run: ruff check code/ tests/")
    print("To fix lint issues automatically, run: ruff check --fix code/ tests/")

if __name__ == "__main__":
    main()