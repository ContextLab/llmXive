import os
import sys
import subprocess
from pathlib import Path

def run_command(cmd: list[str], description: str) -> bool:
    """
    Execute a shell command and print the result.
    Returns True if successful, False otherwise.
    """
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        print(f"✓ {description} completed successfully.\n")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed with code {e.returncode}")
        if e.stdout:
            print(e.stdout)
        if e.stderr:
            print(e.stderr, file=sys.stderr)
        print()
        return False
    except FileNotFoundError:
        print(f"✗ {description} failed: Command not found.")
        print("Ensure the tool is installed (e.g., via pip install black flake8).\n")
        return False

def main():
    """
    Main entry point for setting up linting and formatting tools.
    This script verifies installation and runs initial checks on the codebase.
    """
    project_root = Path(__file__).parent.parent.parent
    code_dir = project_root / "code"
    tests_dir = project_root / "tests"

    print("=" * 60)
    print("Setting up Linting and Formatting Tools")
    print("=" * 60 + "\n")

    # 1. Verify / Install dependencies
    print("Step 1: Verifying tool installation...")
    deps = ["black", "flake8", "isort"]
    for dep in deps:
        try:
            subprocess.run([dep, "--version"], check=True, capture_output=True)
            print(f"  - {dep} is installed.")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"  - {dep} not found. Attempting to install...")
            if run_command([sys.executable, "-m", "pip", "install", dep], f"Installing {dep}"):
                print(f"  - {dep} installed successfully.")
            else:
                print(f"  - Failed to install {dep}. Please install manually.")
                return 1
    print()

    # 2. Run Black (format)
    print("Step 2: Running Black formatter...")
    # Format code and tests directories
    success = True
    if code_dir.exists():
        if not run_command([sys.executable, "-m", "black", str(code_dir)], "Black formatting on code/"):
            success = False
    if tests_dir.exists():
        if not run_command([sys.executable, "-m", "black", str(tests_dir)], "Black formatting on tests/"):
            success = False
    print()

    # 3. Run Isort (imports)
    print("Step 3: Running Isort...")
    if code_dir.exists():
        if not run_command([sys.executable, "-m", "isort", str(code_dir)], "Isort on code/"):
            success = False
    if tests_dir.exists():
        if not run_command([sys.executable, "-m", "isort", str(tests_dir)], "Isort on tests/"):
            success = False
    print()

    # 4. Run Flake8 (lint)
    print("Step 4: Running Flake8...")
    # We run flake8 but do not treat warnings as fatal for the setup script itself,
    # though the CI would likely treat them as errors.
    flake8_cmd = [sys.executable, "-m", "flake8", str(code_dir), str(tests_dir)]
    print(f"Running: {' '.join(flake8_cmd)}")
    try:
        result = subprocess.run(
            flake8_cmd,
            capture_output=True,
            text=True,
            cwd=project_root
        )
        if result.returncode == 0:
            print("✓ Flake8 passed with no issues.\n")
        else:
            print("⚠ Flake8 found issues (review output below):")
            print(result.stdout)
            print(result.stderr)
            print("Note: This is informational. Fix issues manually or via auto-fixers if available.\n")
    except FileNotFoundError:
        print("✗ Flake8 command not found.\n")
        success = False

    print("=" * 60)
    if success:
        print("Setup completed. Please review any Flake8 warnings above.")
    else:
        print("Setup completed with errors. Please check the output.")
    print("=" * 60)
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())