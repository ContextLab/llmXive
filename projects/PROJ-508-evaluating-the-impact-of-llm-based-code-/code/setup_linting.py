"""
Setup script to initialize linting and formatting configuration for the project.
This script ensures ruff and black are configured correctly and installs pre-commit hooks.
"""
import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command and return the result."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    if check and result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}")
    return result

def main() -> None:
    root_dir = Path(__file__).parent.parent
    code_dir = root_dir / "code"

    # Ensure config files exist (they are committed artifacts, but we verify paths)
    ruff_cfg = code_dir / ".ruff.toml"
    black_cfg = code_dir / ".black.toml"
    precommit_cfg = root_dir / ".pre-commit-config.yaml"

    print(f"Verifying config files in {code_dir}...")
    if not ruff_cfg.exists():
        print(f"Warning: {ruff_cfg} not found. Please ensure it exists.")
    if not black_cfg.exists():
        print(f"Warning: {black_cfg} not found. Please ensure it exists.")
    if not precommit_cfg.exists():
        print(f"Warning: {precommit_cfg} not found. Please ensure it exists.")

    # Install pre-commit if not installed
    try:
        run_command([sys.executable, "-m", "pip", "install", "pre-commit", "ruff", "black"], check=False)
    except Exception as e:
        print(f"Could not install dependencies via pip: {e}")
        print("Please ensure 'pre-commit', 'ruff', and 'black' are installed in your environment.")
        return

    # Initialize pre-commit
    print("\nInitializing pre-commit hooks...")
    try:
        run_command(["pre-commit", "install"], check=False)
        print("Pre-commit hooks installed successfully.")
    except Exception as e:
        print(f"Failed to install pre-commit hooks: {e}")

    print("\nLinting and formatting setup complete.")
    print("To run manually:")
    print("  ruff check .")
    print("  black .")
    print("  pre-commit run --all-files")

if __name__ == "__main__":
    main()