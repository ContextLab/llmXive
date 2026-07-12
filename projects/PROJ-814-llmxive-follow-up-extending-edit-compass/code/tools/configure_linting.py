"""
Configuration script to ensure linting (ruff) and formatting (black) tools are ready.
This script validates that the configuration files exist and attempts to run
the tools in 'check' mode to verify setup.
"""
import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd: list[str], description: str) -> bool:
    """Run a command and print output."""
    print(f"Checking: {description}")
    try:
        # Run with capture output to avoid cluttering if it passes, but print if it fails
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            cwd=Path(__file__).parent.parent
        )
        if result.returncode != 0:
            print(f"  ❌ {description} failed (exit code {result.returncode})")
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(result.stderr)
            return False
        print(f"  ✅ {description} passed")
        return True
    except FileNotFoundError:
        print(f"  ⚠️  {description} tool not found. Please install it via 'pip install {cmd[0]}'.")
        return False

def main():
    project_root = Path(__file__).parent.parent
    config_file = project_root / "pyproject.toml"

    if not config_file.exists():
        print("❌ pyproject.toml not found in project root. Please run T002 or create it.")
        sys.exit(1)

    print("Verifying Linting and Formatting Configuration...")
    print("-" * 40)

    # Check if configuration is readable by ruff/black (implicit check by running)
    success = True

    # Check Black formatting
    if not run_command(["black", "--check", "--diff", "."], "Black formatting check"):
        success = False

    # Check Ruff linting
    if not run_command(["ruff", "check", "."], "Ruff linting check"):
        success = False

    print("-" * 40)
    if success:
        print("✅ All linting and formatting checks passed.")
        print("   To fix issues automatically, run: black . && ruff check --fix .")
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()