"""
Configuration and execution wrappers for linting (ruff) and formatting (black) tools.
Provides CLI entry points and programmatic access to check/fix project code quality.
"""
import subprocess
import sys
import os
from pathlib import Path


def get_project_root() -> Path:
    """Return the root directory of the project."""
    return Path(__file__).resolve().parent.parent


def run_ruff_check(project_root: Path) -> subprocess.CompletedProcess:
    """
    Run ruff check on the project.
    Returns the completed process result.
    """
    config_file = project_root / "pyproject.toml"
    cmd = [
        sys.executable, "-m", "ruff", "check",
        str(project_root / "code"),
        str(project_root / "tests"),
        "--config", str(config_file)
    ]
    return subprocess.run(cmd, cwd=project_root)


def run_ruff_fix(project_root: Path) -> subprocess.CompletedProcess:
    """
    Run ruff check with --fix to automatically resolve fixable issues.
    """
    config_file = project_root / "pyproject.toml"
    cmd = [
        sys.executable, "-m", "ruff", "check",
        "--fix",
        str(project_root / "code"),
        str(project_root / "tests"),
        "--config", str(config_file)
    ]
    return subprocess.run(cmd, cwd=project_root)


def run_black_check(project_root: Path) -> subprocess.CompletedProcess:
    """
    Run black --check to verify formatting without modifying files.
    """
    config_file = project_root / "pyproject.toml"
    cmd = [
        sys.executable, "-m", "black",
        "--check",
        "--config", str(config_file),
        str(project_root / "code"),
        str(project_root / "tests")
    ]
    return subprocess.run(cmd, cwd=project_root)


def run_black_format(project_root: Path) -> subprocess.CompletedProcess:
    """
    Run black to format all Python files in the project.
    """
    config_file = project_root / "pyproject.toml"
    cmd = [
        sys.executable, "-m", "black",
        "--config", str(config_file),
        str(project_root / "code"),
        str(project_root / "tests")
    ]
    return subprocess.run(cmd, cwd=project_root)


def main():
    """
    CLI entry point for linting and formatting tasks.
    Usage:
      python code/linting_config.py check   -> Run ruff and black checks
      python code/linting_config.py fix     -> Run ruff fix and black format
      python code/linting_config.py ruff    -> Ruff only
      python code/linting_config.py black   -> Black only
    """
    import argparse

    parser = argparse.ArgumentParser(description="Project Linting and Formatting Tools")
    parser.add_argument(
        "action",
        choices=["check", "fix", "ruff", "black"],
        help="Action to perform: check (run checks), fix (apply fixes), ruff (ruff only), black (black only)"
    )
    args = parser.parse_args()

    root = get_project_root()
    exit_code = 0

    if args.action in ["check", "ruff"]:
        print("Running Ruff Check...")
        result = run_ruff_check(root)
        if result.returncode != 0:
            exit_code = result.returncode
            print("Ruff check failed.")
        else:
            print("Ruff check passed.")

    if args.action in ["check", "black"]:
        print("Running Black Check...")
        result = run_black_check(root)
        if result.returncode != 0:
            exit_code = result.returncode
            print("Black check failed (code not formatted).")
        else:
            print("Black check passed.")

    if args.action == "fix":
        print("Running Ruff Fix...")
        result = run_ruff_fix(root)
        if result.returncode != 0:
            print("Ruff fix completed with some unfixable issues.")
        else:
            print("Ruff fix completed successfully.")

        print("Running Black Format...")
        result = run_black_format(root)
        if result.returncode != 0:
            print("Black format failed.")
            exit_code = result.returncode
        else:
            print("Black format completed successfully.")

    if exit_code != 0 and args.action != "fix":
        sys.exit(exit_code)
    elif args.action == "fix" and exit_code != 0:
        # If fix was requested, we might still exit 0 if we just fixed what we could,
        # but usually we want to report failure if formatting still fails.
        # For this implementation, we pass the exit code if black failed.
        sys.exit(exit_code)

    print("All requested operations completed.")


if __name__ == "__main__":
    main()