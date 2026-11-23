"""
Script to verify linting and formatting tool configuration.
This script checks if ruff and black are installed and configured correctly.
"""
import os
import subprocess
import sys
from pathlib import Path

def check_tool(tool_name: str) -> bool:
    """Check if a tool is installed and available."""
    try:
        subprocess.run(
            [tool_name, "--version"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        print(f"✓ {tool_name} is installed.")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(f"✗ {tool_name} is NOT installed or not in PATH.")
        return False

def check_config_files() -> bool:
    """Check if configuration files exist."""
    config_files = [
        "pyproject.toml",
    ]
    all_exist = True
    for cfg in config_files:
        if Path(cfg).exists():
            print(f"✓ {cfg} exists.")
        else:
            print(f"✗ {cfg} is missing.")
            all_exist = False
    return all_exist

def run_lint_check() -> bool:
    """Run ruff check on the codebase."""
    try:
        result = subprocess.run(
            ["ruff", "check", "src", "code"],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print("✓ Ruff check passed.")
            return True
        else:
            print("✗ Ruff check failed:")
            print(result.stdout)
            print(result.stderr)
            return False
    except FileNotFoundError:
        print("✗ Ruff is not installed.")
        return False

def run_format_check() -> bool:
    """Run black check on the codebase."""
    try:
        result = subprocess.run(
            ["black", "--check", "src", "code"],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print("✓ Black check passed.")
            return True
        else:
            print("✗ Black check failed:")
            print(result.stdout)
            print(result.stderr)
            return False
    except FileNotFoundError:
        print("✗ Black is not installed.")
        return False

def main():
    """Main entry point for linting verification."""
    print("=== Linting and Formatting Verification ===\n")

    # Check tools
    ruff_ok = check_tool("ruff")
    black_ok = check_tool("black")

    # Check config
    config_ok = check_config_files()

    if not (ruff_ok and black_ok and config_ok):
        print("\n⚠ Configuration incomplete. Please install missing tools or files.")
        print("  Install dev dependencies: pip install -e '.[dev]'")
        sys.exit(1)

    # Run checks
    print("\n=== Running Checks ===")
    lint_ok = run_lint_check()
    format_ok = run_format_check()

    if lint_ok and format_ok:
        print("\n✓ All checks passed successfully.")
        sys.exit(0)
    else:
        print("\n✗ Some checks failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()