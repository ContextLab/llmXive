"""
Setup script for linting (ruff), formatting (black), and pre-commit hooks.
This script installs pre-commit hooks into the local .git/hooks directory.
"""
import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command and optionally raise on failure."""
    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            check=check,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return result
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {e}")
        print(f"stderr: {e.stderr}")
        if check:
            sys.exit(1)
        return e

def main() -> None:
    """Main entry point for setup_linting."""
    root_dir = Path(__file__).parent.parent

    # 1. Verify pre-commit is installed
    print("Checking for pre-commit installation...")
    run_command([sys.executable, "-m", "pip", "install", "pre-commit", "ruff", "black"], check=True)

    # 2. Initialize pre-commit in the repository
    print("Initializing pre-commit...")
    run_command(["pre-commit", "install"], check=True)

    # 3. Run a sample check on existing files to ensure configuration works
    print("Running initial pre-commit check on code/ directory...")
    # We run with --all-files to check everything, ignoring failures if files are missing
    # as this is a setup script, not a CI gate.
    run_command(["pre-commit", "run", "--all-files"], check=False)

    print("\nLinting and formatting setup complete.")
    print("Hooks installed. Run 'pre-commit run' to check manually.")
    print("Run 'black code/' and 'ruff check code/' directly if needed.")

if __name__ == "__main__":
    main()
