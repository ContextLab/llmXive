"""
Setup script to install and configure linting (ruff) and formatting (black) tools.
This script ensures the project adheres to the configured standards.
"""
import subprocess
import sys
from pathlib import Path

def run_command(cmd: list[str]) -> None:
    """Run a shell command and raise if it fails."""
    print(f"Running: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {e}")
        sys.exit(1)

def main() -> None:
    """Install dependencies and run initial checks."""
    project_root = Path(__file__).parent.parent
    print(f"Project root: {project_root}")

    # Install tools
    run_command([sys.executable, "-m", "pip", "install", "-U", "ruff", "black"])

    # Check formatting (dry run)
    print("\n--- Checking Black formatting ---")
    run_command(["black", "--check", "--diff", str(project_root / "code")])

    # Check linting
    print("\n--- Checking Ruff linting ---")
    run_command(["ruff", "check", str(project_root / "code")])

    print("\nLinting and formatting checks passed.")

if __name__ == "__main__":
    main()
