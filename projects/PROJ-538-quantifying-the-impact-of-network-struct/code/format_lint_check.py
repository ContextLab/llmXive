"""
Utility script to run linting and formatting checks.
This script ensures that the codebase adheres to the configured
ruff/flake8 and black standards.
"""
import subprocess
import sys
from pathlib import Path

def run_command(cmd: list[str], check: bool = True) -> None:
    """Run a command and exit if it fails."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        if check:
            print(f"Error: Command failed with exit code {result.returncode}")
            sys.exit(result.returncode)
        else:
            print(f"Warning: Command returned exit code {result.returncode}")

def main() -> None:
    """Run linting and formatting checks."""
    project_root = Path(__file__).parent.parent

    # 1. Run Black (formatting)
    # We use --check to verify formatting without modifying files
    run_command(["black", "--check", "--diff", str(project_root)])

    # 2. Run Ruff (linting)
    run_command(["ruff", "check", str(project_root)])

    # 3. Run Flake8 (legacy linting, if needed for specific checks)
    # Note: Ruff is preferred, but we run flake8 for compatibility if configured
    try:
        run_command(["flake8", str(project_root)])
    except FileNotFoundError:
        print("Warning: flake8 not found. Skipping flake8 checks.")

    print("All checks passed.")

if __name__ == "__main__":
    main()