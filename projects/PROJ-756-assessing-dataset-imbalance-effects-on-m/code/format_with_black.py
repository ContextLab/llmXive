"""
T044b Implementation: Run Black on all Python files in code/.

This script executes `black` on the `code/` directory to ensure
consistent code formatting across the project. It handles the
installation of `black` if missing and reports the results.
"""
import os
import sys
import subprocess
from pathlib import Path

def main():
    """Run black formatter on the code directory."""
    project_root = Path(__file__).parent.parent
    code_dir = project_root / "code"

    if not code_dir.exists():
        print(f"Error: Code directory not found at {code_dir}")
        sys.exit(1)

    print(f"Running Black formatter on {code_dir}...")

    # Check if black is installed
    try:
        result = subprocess.run(
            ["black", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"Black version: {result.stdout.strip()}")
    except subprocess.CalledProcessError:
        print("Black not found. Installing black...")
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "black"],
                check=True,
                capture_output=True
            )
            print("Black installed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Failed to install black: {e}")
            sys.exit(1)

    # Run black
    try:
        result = subprocess.run(
            ["black", str(code_dir)],
            capture_output=True,
            text=True,
            check=False  # We want to see output even if changes were made
        )

        if result.stdout:
            print("STDOUT:")
            print(result.stdout)

        if result.stderr:
            print("STDERR:")
            print(result.stderr)

        if result.returncode == 0:
            print("Success: All files are formatted correctly or were formatted.")
            sys.exit(0)
        elif result.returncode == 1:
            print("Success: Files were reformatted.")
            sys.exit(0)
        else:
            print(f"Error: Black exited with code {result.returncode}")
            sys.exit(1)

    except FileNotFoundError:
        print("Error: 'black' command not found. Please ensure it is installed.")
        sys.exit(1)
    except Exception as e:
        print(f"Error running black: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()