import os
import sys
import subprocess
from pathlib import Path
from config import get_project_root


def ensure_linting_config() -> None:
    """
    Ensure that pyproject.toml exists and contains valid black/ruff configuration.
    If missing, the project structure is considered incomplete for linting tasks.
    """
    project_root = get_project_root()
    config_path = project_root / "pyproject.toml"

    if not config_path.exists():
        raise FileNotFoundError(
            f"pyproject.toml not found at {config_path}. "
            "T002 (Configure linting) must be completed first."
        )

    # Basic validation: check for [tool.black] and [tool.ruff] sections
    content = config_path.read_text()
    if "[tool.black]" not in content:
        raise ValueError("pyproject.toml missing [tool.black] configuration.")
    if "[tool.ruff]" not in content:
        raise ValueError("pyproject.toml missing [tool.ruff] configuration.")


def run_black_check() -> int:
    """
    Run black --check on the project.
    Returns 0 if all files are formatted correctly, non-zero otherwise.
    """
    project_root = get_project_root()
    try:
        result = subprocess.run(
            ["black", "--check", "--diff", "."],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            sys.stderr.write("Black formatting check failed:\n")
            sys.stderr.write(result.stdout)
            sys.stderr.write(result.stderr)
        return result.returncode
    except FileNotFoundError:
        sys.stderr.write("Error: 'black' command not found. Please install it.\n")
        return 1


def run_ruff_check() -> int:
    """
    Run ruff check on the project.
    Returns 0 if no linting errors found, non-zero otherwise.
    """
    project_root = get_project_root()
    try:
        result = subprocess.run(
            ["ruff", "check", "."],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            sys.stderr.write("Ruff linting check failed:\n")
            sys.stderr.write(result.stdout)
            sys.stderr.write(result.stderr)
        return result.returncode
    except FileNotFoundError:
        sys.stderr.write("Error: 'ruff' command not found. Please install it.\n")
        return 1


def run_black_format() -> int:
    """
    Run black --diff on the project to format files in-place.
    Returns 0 on success, non-zero on failure.
    """
    project_root = get_project_root()
    try:
        result = subprocess.run(
            ["black", "."],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            sys.stderr.write("Black formatting failed:\n")
            sys.stderr.write(result.stdout)
            sys.stderr.write(result.stderr)
        return result.returncode
    except FileNotFoundError:
        sys.stderr.write("Error: 'black' command not found. Please install it.\n")
        return 1


def run_ruff_fix() -> int:
    """
    Run ruff check --fix to automatically fix linting errors.
    Returns 0 on success, non-zero on failure.
    """
    project_root = get_project_root()
    try:
        result = subprocess.run(
            ["ruff", "check", "--fix", "."],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            sys.stderr.write("Ruff auto-fix failed or issues remain:\n")
            sys.stderr.write(result.stdout)
            sys.stderr.write(result.stderr)
        return result.returncode
    except FileNotFoundError:
        sys.stderr.write("Error: 'ruff' command not found. Please install it.\n")
        return 1


def main() -> None:
    """
    Main entry point for T002: Configure linting and formatting tools.
    Validates that configuration exists and runs checks.
    """
    print("Running T002: Configure linting and formatting tools...")

    # 1. Ensure configuration exists
    try:
        ensure_linting_config()
        print("✓ pyproject.toml with black/ruff configuration found.")
    except (FileNotFoundError, ValueError) as e:
        print(f"✗ Configuration check failed: {e}")
        sys.exit(1)

    # 2. Run checks (non-destructive)
    print("Running black --check...")
    black_code = run_black_check()
    print("Running ruff check...")
    ruff_code = run_ruff_check()

    if black_code == 0 and ruff_code == 0:
        print("✓ All linting and formatting checks passed.")
        sys.exit(0)
    else:
        print("✗ Some checks failed. Run 'python code/linting_config.py format' to fix.")
        sys.exit(1)


if __name__ == "__main__":
    main()
