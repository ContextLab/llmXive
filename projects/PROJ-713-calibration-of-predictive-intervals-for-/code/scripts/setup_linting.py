"""
Script to configure and verify linting and formatting tools.
This script ensures that flake8, black, isort, and pre-commit are properly
configured and can be run against the codebase.
"""
import os
import sys
import subprocess
from pathlib import Path

def run_command(cmd: list, description: str) -> bool:
    """Run a command and report status."""
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        print(f"✓ {description} completed successfully\n")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed with return code {e.returncode}")
        if e.stdout:
            print(f"STDOUT: {e.stdout}")
        if e.stderr:
            print(f"STDERR: {e.stderr}")
        return False
    except FileNotFoundError:
        print(f"✗ {description} failed: command not found")
        print("Ensure the required tools are installed in your environment.")
        return False

def main():
    """Main entry point for linting setup verification."""
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    print("=" * 60)
    print("Linting and Formatting Configuration Verification")
    print("=" * 60)
    print(f"Project root: {project_root}")
    print()

    # Verify configuration files exist
    config_files = [
        "code/.flake8",
        "code/pyproject.toml",
        "code/.pre-commit-config.yaml",
        "requirements.txt"
    ]

    print("Checking configuration files...")
    all_configs_exist = True
    for config_file in config_files:
        config_path = project_root / config_file
        if config_path.exists():
            print(f"  ✓ {config_file} exists")
        else:
            print(f"  ✗ {config_file} is MISSING")
            all_configs_exist = False

    if not all_configs_exist:
        print("\nConfiguration files are missing. Please ensure T003 artifacts are created.")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("Verifying tool availability...")
    print("=" * 60)

    # Check if tools are installed
    tools = [
        (["flake8", "--version"], "flake8"),
        (["black", "--version"], "black"),
        (["isort", "--version"], "isort"),
        (["pre-commit", "--version"], "pre-commit")
    ]

    tools_available = True
    for cmd, name in tools:
        if not run_command(cmd, f"Checking {name} availability"):
            tools_available = False

    if not tools_available:
        print("\nSome tools are missing. Install them with:")
        print("  pip install flake8 black isort pre-commit")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("Running linting and formatting checks...")
    print("=" * 60)

    # Run flake8
    flake8_success = run_command(
        ["flake8", "code/", "--config=code/.flake8", "--count"],
        "Flake8 linting check"
    )

    # Run black check (dry run)
    black_success = run_command(
        ["black", "code/", "--check", "--diff"],
        "Black formatting check (dry run)"
    )

    # Run isort check
    isort_success = run_command(
        ["isort", "code/", "--check-only", "--diff"],
        "Isort import sorting check"
    )

    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Flake8: {'✓ PASS' if flake8_success else '✗ FAIL'}")
    print(f"Black:  {'✓ PASS' if black_success else '✗ FAIL'}")
    print(f"Isort:  {'✓ PASS' if isort_success else '✗ FAIL'}")

    if flake8_success and black_success and isort_success:
        print("\n✓ All linting and formatting checks passed!")
        print("\nTo run these checks automatically on every commit, install pre-commit:")
        print("  pre-commit install")
        sys.exit(0)
    else:
        print("\n✗ Some checks failed. Please fix the issues above.")
        print("You can auto-fix formatting issues with:")
        print("  black code/")
        print("  isort code/")
        sys.exit(1)

if __name__ == "__main__":
    main()