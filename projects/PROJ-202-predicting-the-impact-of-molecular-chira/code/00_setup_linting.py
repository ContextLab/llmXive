import os
import sys
import subprocess
from pathlib import Path

def check_config_files():
    """Verify that ruff and black configuration files exist."""
    base_dir = Path(__file__).parent
    ruff_config = base_dir / ".ruff.toml"
    black_config = base_dir / ".black.toml"

    if not ruff_config.exists():
        print("Error: .ruff.toml not found in code directory.")
        return False
    if not black_config.exists():
        print("Error: .black.toml not found in code directory.")
        return False
    
    print("Configuration files found.")
    return True

def run_ruff_check():
    """Run ruff check on the code directory."""
    base_dir = Path(__file__).parent
    try:
        result = subprocess.run(
            ["ruff", "check", str(base_dir)],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0:
            print("Ruff check passed: No issues found.")
            return True
        else:
            print("Ruff check failed:")
            print(result.stdout)
            print(result.stderr)
            return False
    except FileNotFoundError:
        print("Error: 'ruff' command not found. Please install it via pip.")
        return False

def run_black_check():
    """Run black --check on the code directory."""
    base_dir = Path(__file__).parent
    try:
        result = subprocess.run(
            ["black", "--check", str(base_dir)],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0:
            print("Black check passed: Code is formatted correctly.")
            return True
        else:
            print("Black check failed: Code needs formatting.")
            print(result.stdout)
            print(result.stderr)
            return False
    except FileNotFoundError:
        print("Error: 'black' command not found. Please install it via pip.")
        return False

def main():
    """Main entry point for linting configuration verification."""
    print("Verifying linting configuration...")
    if not check_config_files():
        sys.exit(1)

    print("\nRunning Ruff check...")
    ruff_ok = run_ruff_check()

    print("\nRunning Black check...")
    black_ok = run_black_check()

    if ruff_ok and black_ok:
        print("\nAll linting checks passed.")
        sys.exit(0)
    else:
        print("\nSome linting checks failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()