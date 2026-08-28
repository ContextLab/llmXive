"""
Setup script to initialize linting (ruff), formatting (black), and pre-commit hooks.
This script installs the necessary tools and configures the git hooks.
"""
import os
import subprocess
import sys
from pathlib import Path

def run_command(command: list[str], description: str) -> bool:
    """Run a shell command and print the result."""
    print(f"Running: {description}")
    print(f"Command: {' '.join(command)}")
    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR: {description} failed.", file=sys.stderr)
        print(f"Stderr: {e.stderr}", file=sys.stderr)
        return False

def main() -> int:
    """Main entry point for linting setup."""
    project_root = Path(__file__).parent.parent

    # Verify config files exist
    pyproject = project_root / "pyproject.toml"
    precommit = project_root / ".pre-commit-config.yaml"

    if not pyproject.exists():
        print("ERROR: pyproject.toml not found. Please ensure it exists.", file=sys.stderr)
        return 1
    
    if not precommit.exists():
        print("ERROR: .pre-commit-config.yaml not found. Please ensure it exists.", file=sys.stderr)
        return 1

    # Step 1: Install pre-commit
    success = run_command(
        [sys.executable, "-m", "pip", "install", "-e", ".[dev]"],
        "Installing development dependencies (ruff, black, pre-commit)"
    )
    if not success:
        return 1

    # Step 2: Initialize pre-commit hooks
    success = run_command(
        ["pre-commit", "install"],
        "Installing pre-commit hooks"
    )
    if not success:
        return 1

    # Step 3: Run a dry-run check to ensure configs are valid
    success = run_command(
        ["pre-commit", "run", "--all-files"],
        "Running pre-commit on all files (dry run)"
    )
    
    if success:
        print("\n✅ Linting and formatting setup complete.")
        print("   - Ruff and Black configured in pyproject.toml")
        print("   - Pre-commit hooks installed")
        print("   - Run 'pre-commit run' to check files manually")
    else:
        print("\n⚠️  Pre-commit check failed. Please fix the issues above.", file=sys.stderr)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())