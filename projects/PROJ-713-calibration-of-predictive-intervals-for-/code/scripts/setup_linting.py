"""
Script to verify linting and formatting configuration.
This script checks if flake8 and black are configured correctly.
"""
import os
import sys
import subprocess
from pathlib import Path

def run_command(cmd: list, description: str) -> bool:
    """Run a command and return True if successful."""
    print(f"Running: {description}")
    try:
        result = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        if result.returncode == 0:
            print(f"  ✓ {description} passed")
            return True
        else:
            print(f"  ✗ {description} failed")
            if result.stdout:
                print(f"    stdout: {result.stdout[:200]}")
            if result.stderr:
                print(f"    stderr: {result.stderr[:200]}")
            return False
    except FileNotFoundError:
        print(f"  ✗ Command not found: {cmd[0]}")
        return False

def main():
    """Verify linting setup."""
    project_root = Path(__file__).parent.parent
    config_file = project_root / ".flake8"
    pyproject_file = project_root / "pyproject.toml"

    print("Verifying Linting and Formatting Setup...")
    print("-" * 40)

    if not config_file.exists():
        print("✗ .flake8 configuration file missing!")
        return 1
    print("✓ .flake8 found")

    if not pyproject_file.exists():
        print("✗ pyproject.toml configuration file missing!")
        return 1
    print("✓ pyproject.toml found")

    # Check if tools are installed
    tools_installed = True
    for tool in ["flake8", "black"]:
        if not run_command([tool, "--version"], f"{tool} installation"):
            tools_installed = False

    if not tools_installed:
        print("\n⚠ Some tools are missing. Install with: pip install -r requirements-dev.txt")
        return 1

    # Run a dry check on a sample file (config.py is guaranteed to exist)
    sample_file = project_root / "code" / "config.py"
    if sample_file.exists():
        print("\nChecking sample file: config.py")
        run_command(["flake8", str(sample_file)], "Flake8 check on config.py")
        run_command(["black", "--check", "--diff", str(sample_file)], "Black check on config.py")
        run_command(["isort", "--check-only", "--diff", str(sample_file)], "Isort check on config.py")
    else:
        print("\n⚠ Sample file 'code/config.py' not found for verification.")

    print("\n" + "=" * 40)
    print("Linting setup verification complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())