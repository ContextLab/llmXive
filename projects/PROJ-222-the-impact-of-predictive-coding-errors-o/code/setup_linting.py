"""
Setup script to install and configure linting (ruff) and formatting (black) tools.
This script ensures the necessary tools are installed and configuration files exist.
"""
import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd: list, description: str) -> bool:
    """Run a shell command and report status."""
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running {description}: {e}")
        print(f"stderr: {e.stderr}")
        return False

def main():
    """Install tools and verify configuration."""
    project_root = Path(__file__).parent.parent
    code_dir = project_root / "code"

    # Ensure configuration files exist
    ruff_config = code_dir / ".ruff.toml"
    pre_commit_config = code_dir / ".pre-commit-config.yaml"

    if not ruff_config.exists():
        print(f"Error: {ruff_config} not found. Please create it manually or run setup.")
        sys.exit(1)

    if not pre_commit_config.exists():
        print(f"Error: {pre_commit_config} not found. Please create it manually or run setup.")
        sys.exit(1)

    print("Configuration files found.")

    # Install ruff
    success = run_command(
        [sys.executable, "-m", "pip", "install", "ruff"],
        "Installing ruff"
    )
    if not success:
        print("Failed to install ruff.")
        sys.exit(1)

    # Install black
    success = run_command(
        [sys.executable, "-m", "pip", "install", "black"],
        "Installing black"
    )
    if not success:
        print("Failed to install black.")
        sys.exit(1)

    # Install pre-commit
    success = run_command(
        [sys.executable, "-m", "pip", "install", "pre-commit"],
        "Installing pre-commit"
    )
    if not success:
        print("Failed to install pre-commit.")
        sys.exit(1)

    # Initialize pre-commit hooks
    success = run_command(
        ["pre-commit", "install"],
        "Installing pre-commit hooks"
    )
    if not success:
        print("Failed to install pre-commit hooks. You may need to run 'pre-commit install' manually.")
    
    print("\nLinting and formatting setup complete.")
    print("To run manually:")
    print(f"  ruff check {code_dir}")
    print(f"  black {code_dir}")
    print(f"  pre-commit run --all-files")

if __name__ == "__main__":
    main()
