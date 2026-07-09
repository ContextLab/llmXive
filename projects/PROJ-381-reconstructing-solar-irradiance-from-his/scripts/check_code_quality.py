"""
Script to run linting (ruff) and formatting (black) checks.
This script acts as a simple wrapper to ensure the tools are installed
and to provide a single entry point for CI/CD or manual verification.
"""
import subprocess
import sys
import os

def run_command(cmd: list[str], description: str) -> bool:
    """Run a command and return True if successful."""
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error in {description}:")
        print(e.stdout)
        return False

def main():
    # Check if tools are available
    tools = [
        ("black", ["black", "--version"]),
        ("ruff", ["ruff", "--version"]),
    ]

    for name, cmd in tools:
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"{name} is installed.")
        except FileNotFoundError:
            print(f"Error: {name} is not installed. Please run: pip install -e '.[dev]'")
            sys.exit(1)

    # Run checks
    checks = [
        (
            "Black Formatting Check",
            ["black", "--check", "code/", "tests/", "scripts/"],
        ),
        (
            "Ruff Linting Check",
            ["ruff", "check", "code/", "tests/", "scripts/"],
        ),
    ]

    all_passed = True
    for desc, cmd in checks:
        if not run_command(cmd, desc):
            all_passed = False

    if all_passed:
        print("\n✓ All code quality checks passed.")
        sys.exit(0)
    else:
        print("\n✗ Some checks failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()