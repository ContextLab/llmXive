"""
Configuration and execution utilities for linting (Ruff) and formatting (Black).
This module ensures the project adheres to the style guidelines defined in pyproject.toml.
"""
import os
import subprocess
import sys
from pathlib import Path


def ensure_config_files() -> bool:
    """
    Verify that the required configuration files exist in the project root.
    Returns True if 'pyproject.toml' is present, False otherwise.
    """
    project_root = Path(__file__).resolve().parent.parent
    config_file = project_root / "pyproject.toml"

    if not config_file.exists():
        print(f"ERROR: Configuration file not found at {config_file}. "
              "Please ensure 'pyproject.toml' with Black and Ruff settings exists.")
        return False

    # Basic validation: check if [tool.black] and [tool.ruff] sections exist
    content = config_file.read_text()
    if "[tool.black]" not in content:
        print("WARNING: [tool.black] section not found in pyproject.toml")
    if "[tool.ruff]" not in content:
        print("WARNING: [tool.ruff] section not found in pyproject.toml")

    return True


def run_linter() -> int:
    """
    Execute the Ruff linter on the 'code' directory.
    Returns the exit code of the linter (0 for success, non-zero for errors).
    """
    project_root = Path(__file__).resolve().parent.parent
    code_dir = project_root / "code"
    tests_dir = project_root / "tests"

    if not code_dir.exists():
        print("ERROR: 'code' directory not found.")
        return 1

    cmd = [
        sys.executable, "-m", "ruff", "check",
        str(code_dir),
        str(tests_dir),
    ]

    print(f"Running linter: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, cwd=project_root)
        if result.returncode == 0:
            print("Linting passed: No issues found.")
        else:
            print("Linting failed: Issues found.")
        return result.returncode
    except FileNotFoundError:
        print("ERROR: 'ruff' is not installed. Please run 'pip install ruff'.")
        return 1
    except Exception as e:
        print(f"ERROR: Failed to run linter: {e}")
        return 1


def run_formatter() -> int:
    """
    Execute the Black formatter on the 'code' directory.
    Returns the exit code of the formatter (0 for success, non-zero for errors).
    """
    project_root = Path(__file__).resolve().parent.parent
    code_dir = project_root / "code"
    tests_dir = project_root / "tests"

    if not code_dir.exists():
        print("ERROR: 'code' directory not found.")
        return 1

    cmd = [
        sys.executable, "-m", "black",
        "--check",
        str(code_dir),
        str(tests_dir),
    ]

    print(f"Running formatter (check mode): {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, cwd=project_root)
        if result.returncode == 0:
            print("Formatting check passed: Code is formatted correctly.")
        else:
            print("Formatting check failed: Code needs formatting. Run 'black code tests' to fix.")
        return result.returncode
    except FileNotFoundError:
        print("ERROR: 'black' is not installed. Please run 'pip install black'.")
        return 1
    except Exception as e:
        print(f"ERROR: Failed to run formatter: {e}")
        return 1


def main():
    """
    Main entry point for the linting and formatting configuration task.
    Runs checks and optionally fixes issues if --fix is passed.
    """
    if not ensure_config_files():
        sys.exit(1)

    # Run linter
    lint_code = run_linter()

    # Run formatter check
    fmt_code = run_formatter()

    if lint_code != 0 or fmt_code != 0:
        print("\n--- Summary ---")
        print("Linting: FAILED" if lint_code != 0 else "Linting: PASSED")
        print("Formatting: FAILED" if fmt_code != 0 else "Formatting: PASSED")
        print("\nFix suggestions:")
        print("  pip install ruff black")
        print("  ruff check code tests --fix")
        print("  black code tests")
        sys.exit(1)
    else:
        print("\n--- Summary ---")
        print("All checks passed.")
        sys.exit(0)


if __name__ == "__main__":
    main()