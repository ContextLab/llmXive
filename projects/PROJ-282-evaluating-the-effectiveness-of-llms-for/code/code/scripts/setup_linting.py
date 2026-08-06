"""
Script to configure and validate linting (ruff) and formatting (black) tools.
This script ensures the project is set up with the correct configuration files
and that the tools are installed and runnable.
"""
import os
import sys
import subprocess
from pathlib import Path

def get_project_root() -> Path:
    """Return the root of the project (parent of 'code' directory)."""
    current = Path(__file__).resolve()
    # Assuming this script is at code/code/scripts/setup_linting.py
    # We need to go up two levels to get to 'code' which is the project root for this task
    # However, the task says "paths are relative to project root and MUST live under code/..."
    # The pyproject.toml is expected at the root of the repository, which seems to be 'code' in this context
    # based on the artifact path "code/pyproject.toml".
    # Let's assume the repository root is the directory containing 'pyproject.toml'.
    # If we are in code/code/scripts, we go up 2 to get to code/.
    return current.parent.parent.parent

def check_command(cmd: str) -> bool:
    """Check if a command is available in the system PATH."""
    try:
        subprocess.run(
            [cmd, "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def install_if_missing(cmd: str) -> None:
    """Install a tool via pip if it is not available."""
    if not check_command(cmd):
        print(f"Installing {cmd}...")
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", cmd],
                check=True,
            )
            print(f"{cmd} installed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Failed to install {cmd}: {e}")
            sys.exit(1)

def validate_config_files(root: Path) -> bool:
    """Validate that required configuration files exist."""
    required_files = [
        root / "pyproject.toml",
        root / ".ruff.toml",
        root / ".pre-commit-config.yaml",
    ]
    all_exist = True
    for f in required_files:
        if not f.exists():
            print(f"Missing required file: {f}")
            all_exist = False
    return all_exist

def run_precommit_install(root: Path) -> None:
    """Install pre-commit hooks."""
    print("Installing pre-commit hooks...")
    try:
        subprocess.run(
            ["pre-commit", "install"],
            cwd=root,
            check=True,
        )
        print("Pre-commit hooks installed.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to install pre-commit hooks: {e}")
        # Non-fatal, but log it
        print("You can run 'pre-commit install' manually later.")

def main() -> None:
    """Main entry point for the setup script."""
    root = get_project_root()
    print(f"Project root detected at: {root}")

    # Ensure tools are installed
    install_if_missing("ruff")
    install_if_missing("black")
    install_if_missing("pre-commit")

    # Validate configuration
    if not validate_config_files(root):
        print("Configuration validation failed. Please check the files.")
        sys.exit(1)

    # Install hooks
    run_precommit_install(root)

    print("Linting and formatting setup complete.")
    print("Run 'pre-commit run --all-files' to check the entire codebase.")

if __name__ == "__main__":
    main()
