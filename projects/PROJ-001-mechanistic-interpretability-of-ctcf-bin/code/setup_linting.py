"""
Setup script for linting and formatting tools.
Installs pre-commit hooks and verifies configuration.
"""
import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd: list[str], description: str) -> bool:
    """Run a shell command and report status."""
    print(f"Running: {description}")
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=False,
            text=True
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running {description}: {e}")
        return False

def main() -> int:
    """Main entry point for setup_linting."""
    project_root = Path(__file__).parent.parent
    code_dir = project_root / "code"

    # Ensure pre-commit is installed
    print("Checking for pre-commit installation...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "pre-commit"], check=True)
    except subprocess.CalledProcessError:
        print("Failed to install pre-commit. Please install manually.")
        return 1

    # Install pre-commit hooks
    hooks_dir = code_dir / ".pre-commit-hooks"
    hooks_dir.mkdir(exist_ok=True)

    print("Installing pre-commit hooks...")
    if not run_command(
        [sys.executable, "-m", "pre_commit", "install"],
        "Installing pre-commit hooks"
    ):
        return 1

    # Verify configuration files exist
    required_files = [
        code_dir / ".flake8",
        code_dir / "pyproject.toml",
        project_root / ".pre-commit-config.yaml"
    ]

    missing = [f for f in required_files if not f.exists()]
    if missing:
        print(f"Warning: Missing configuration files: {missing}")
        print("Please ensure .flake8, pyproject.toml, and .pre-commit-config.yaml are present.")
        return 1

    print("Linting and formatting tools configured successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
