import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd: list, check: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command and return the result."""
    try:
        result = subprocess.run(
            cmd,
            check=check,
            capture_output=True,
            text=True,
            shell=False,
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {' '.join(cmd)}")
        print(f"Return code: {e.returncode}")
        print(f"Stderr: {e.stderr}")
        raise

def main():
    """
    Configure linting (ruff), formatting (black), and pre-commit hooks.
    This script verifies the presence of config files and initializes pre-commit.
    """
    project_root = Path(__file__).resolve().parent.parent
    print(f"Project root: {project_root}")

    # Verify config files exist
    config_files = [
        project_root / ".ruff.toml",
        project_root / "pyproject.toml",
        project_root / ".pre-commit-config.yaml",
    ]

    missing = [f for f in config_files if not f.exists()]
    if missing:
        print("Error: Missing configuration files:")
        for f in missing:
            print(f"  - {f.name}")
        sys.exit(1)

    print("Configuration files found.")

    # Install pre-commit hooks if not already installed
    # We assume pre-commit is installed in the environment (via requirements.txt if needed, 
    # though typically it's a dev dependency not strictly in runtime requirements)
    # If not installed, we attempt to install it or skip gracefully depending on strictness.
    # For this implementation, we try to install hooks.
    
    print("Installing pre-commit hooks...")
    try:
        run_command([sys.executable, "-m", "pip", "install", "pre-commit"])
        run_command([sys.executable, "-m", "pre_commit", "install"])
        print("Pre-commit hooks installed successfully.")
    except FileNotFoundError:
        print("Warning: 'pre-commit' not found in PATH. Please install it manually or ensure it is in the environment.")
        print("Run: pip install pre-commit && pre-commit install")
    except subprocess.CalledProcessError:
        print("Warning: Failed to install pre-commit hooks automatically.")
        print("Please run manually: pre-commit install")

    # Optional: Run a dry-run check to ensure configs are valid
    print("Validating configuration...")
    try:
        run_command(["ruff", "check", "."], check=False)
        run_command(["black", "--check", "--diff", "."], check=False)
        print("Configuration validation complete (see output above for any warnings).")
    except FileNotFoundError:
        print("Note: Ruff or Black not found in PATH. Ensure they are installed.")

    print("Linting and formatting setup complete.")

if __name__ == "__main__":
    main()