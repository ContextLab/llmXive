"""
Script to set up linting and formatting tools for the project.
This script installs pre-commit hooks and verifies tool availability.
"""
import subprocess
import sys
from pathlib import Path

def run_command(cmd: list[str], description: str) -> bool:
    """Run a command and report status."""
    print(f"Running: {description}")
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True
        )
        print(f"  ✓ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ✗ {description} failed: {e}")
        if e.stdout:
            print(f"    stdout: {e.stdout}")
        if e.stderr:
            print(f"    stderr: {e.stderr}")
        return False

def main():
    """Set up linting infrastructure."""
    project_root = Path(__file__).parent.parent
    code_dir = project_root

    print("=" * 60)
    print("Setting up linting and formatting tools")
    print("=" * 60)

    # Install pre-commit if not present
    run_command(
        [sys.executable, "-m", "pip", "install", "-q", "pre-commit"],
        "Installing pre-commit"
    )

    # Install pre-commit hooks
    run_command(
        ["pre-commit", "install"],
        "Installing pre-commit hooks"
    )

    # Verify ruff is available
    run_command(
        ["ruff", "--version"],
        "Verifying ruff installation"
    )

    # Verify black is available
    run_command(
        ["black", "--version"],
        "Verifying black installation"
    )

    # Run initial check on all files
    print("\nRunning initial linting check...")
    run_command(
        ["ruff", "check", str(code_dir), "--fix"],
        "Running ruff check with auto-fix"
    )

    run_command(
        ["black", "--check", str(code_dir)],
        "Running black format check"
    )

    print("\n" + "=" * 60)
    print("Linting setup complete!")
    print("=" * 60)
    print("\nTo run linting manually:")
    print("  pre-commit run --all-files")
    print("\nTo enable automatic checks on git commit:")
    print("  pre-commit install (already done)")

if __name__ == "__main__":
    main()
