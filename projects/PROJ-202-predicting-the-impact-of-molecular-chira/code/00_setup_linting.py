"""
Script to verify linting and formatting configuration.
This script checks if ruff and black are configured correctly
and runs them to ensure the project adheres to style guidelines.
"""
import os
import sys
import subprocess
from pathlib import Path


def check_config_files():
    """Check if required configuration files exist."""
    code_root = Path(__file__).parent
    required_files = [
        ".ruff.toml",
        ".flake8",
        "pyproject.toml",
    ]

    missing = []
    for file_name in required_files:
        file_path = code_root / file_name
        if not file_path.exists():
            missing.append(file_path)

    if missing:
        print(f"ERROR: Missing configuration files: {missing}")
        return False

    print("✓ All configuration files found.")
    return True


def run_ruff_check():
    """Run ruff to check for linting issues."""
    code_root = Path(__file__).parent
    try:
        result = subprocess.run(
            ["ruff", "check", "."],
            cwd=code_root,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0:
            print("✓ Ruff check passed: No linting issues found.")
            return True
        else:
            print("✗ Ruff check failed:")
            print(result.stdout)
            print(result.stderr)
            return False
    except FileNotFoundError:
        print("WARNING: 'ruff' not found in PATH. Please install it.")
        return False
    except subprocess.TimeoutExpired:
        print("ERROR: Ruff check timed out.")
        return False


def run_black_check():
    """Run black to check formatting."""
    code_root = Path(__file__).parent
    try:
        result = subprocess.run(
            ["black", "--check", "."],
            cwd=code_root,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0:
            print("✓ Black check passed: Code is properly formatted.")
            return True
        else:
            print("✗ Black check failed:")
            print(result.stdout)
            print(result.stderr)
            return False
    except FileNotFoundError:
        print("WARNING: 'black' not found in PATH. Please install it.")
        return False
    except subprocess.TimeoutExpired:
        print("ERROR: Black check timed out.")
        return False


def main():
    """Main entry point for linting setup verification."""
    print("=== Linting Configuration Verification ===\n")

    if not check_config_files():
        sys.exit(1)

    print("\n--- Running Linting Checks ---")
    ruff_ok = run_ruff_check()
    black_ok = run_black_check()

    if ruff_ok and black_ok:
        print("\n✓ All linting and formatting checks passed.")
        sys.exit(0)
    else:
        print("\n✗ Some checks failed. Please fix the issues above.")
        sys.exit(1)


if __name__ == "__main__":
    main()