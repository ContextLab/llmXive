"""
Setup script to install linting and formatting tools and verify configuration.
This script corresponds to Task T003.
"""
import os
import sys
import subprocess
from pathlib import Path

def main():
    """Install ruff and black, then verify versions and run a check."""
    print("Installing linting and formatting tools...")
    
    # Install ruff and black
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "ruff", "black"])
    except subprocess.CalledProcessError as e:
        print(f"Failed to install tools: {e}")
        sys.exit(1)

    # Verify versions
    try:
        ruff_version = subprocess.check_output(["ruff", "--version"], text=True).strip()
        print(f"Ruff installed: {ruff_version}")
    except Exception as e:
        print(f"Failed to verify ruff: {e}")
        sys.exit(1)

    try:
        black_version = subprocess.check_output(["black", "--version"], text=True).strip()
        print(f"Black installed: {black_version}")
    except Exception as e:
        print(f"Failed to verify black: {e}")
        sys.exit(1)

    # Run ruff check on code directory
    code_dir = Path("code")
    if code_dir.exists():
        print(f"Running ruff check on {code_dir}...")
        try:
            result = subprocess.run(
                ["ruff", "check", str(code_dir)],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print("Ruff check passed: No errors found.")
            else:
                print("Ruff check found issues (this is expected for initial runs):")
                print(result.stdout)
                # We do not exit with error here as the task is to configure, not necessarily fix all pre-existing issues immediately
                # unless the configuration itself is broken.
        except Exception as e:
            print(f"Error running ruff check: {e}")
    else:
        print(f"Code directory {code_dir} not found, skipping check.")

    print("Linting and formatting configuration setup complete.")

if __name__ == "__main__":
    main()
