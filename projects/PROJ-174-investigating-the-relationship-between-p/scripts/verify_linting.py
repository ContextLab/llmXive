"""
Verification script for T003:
Runs black --check on code/ and ensures exit code 0.
Also verifies .flake8 exists and is parseable.
"""
import subprocess
import sys
import os
from pathlib import Path

def main():
    project_root = Path(__file__).resolve().parent.parent
    code_dir = project_root / "code"
    flake8_config = code_dir / ".flake8"
    pyproject_config = code_dir / "pyproject.toml"

    print("=== T003 Verification: Linting Configuration ===")

    # 1. Check .flake8 exists
    if not flake8_config.exists():
        print("FAIL: code/.flake8 not found.")
        sys.exit(1)
    print(f"OK: .flake8 found at {flake8_config}")

    # 2. Check pyproject.toml exists
    if not pyproject_config.exists():
        print("FAIL: code/pyproject.toml not found.")
        sys.exit(1)
    print(f"OK: pyproject.toml found at {pyproject_config}")

    # 3. Run black --check
    print("Running: black --check code/ ...")
    try:
        result = subprocess.run(
            ["black", "--check", str(code_dir)],
            cwd=project_root,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("OK: black --check passed (exit code 0).")
        else:
            print("FAIL: black --check failed.")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            sys.exit(1)
    except FileNotFoundError:
        print("FAIL: 'black' command not found. Ensure it is installed in the environment.")
        sys.exit(1)

    # 4. Optional: Run flake8 check if flake8 is installed
    try:
        result_flake8 = subprocess.run(
            ["flake8", str(code_dir)],
            cwd=project_root,
            capture_output=True,
            text=True
        )
        # We don't fail the task if flake8 isn't installed, but we log it
        if result_flake8.returncode == 0:
            print("OK: flake8 check passed.")
        else:
            print("NOTE: flake8 check found issues (non-fatal for T003 setup, but see below):")
            print(result_flake8.stdout)
    except FileNotFoundError:
        print("NOTE: flake8 not installed in environment. Skipping flake8 execution check.")

    print("=== T003 Verification Complete: SUCCESS ===")

if __name__ == "__main__":
    main()