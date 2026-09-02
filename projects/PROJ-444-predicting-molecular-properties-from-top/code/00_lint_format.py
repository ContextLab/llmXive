"""
Linting and Formatting Runner for llmXive Pipeline.

This script executes ruff (linting) and black (formatting) checks
and fixes based on the project's pyproject.toml configuration.

Usage:
    python code/00_lint_format.py check   # Run checks only (fail on error)
    python code/00_lint_format.py fix     # Auto-fix issues and format
"""
import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd: list[str], check: bool = True) -> bool:
    """
    Run a shell command and return True if successful.

    Args:
        cmd: List of command arguments.
        check: If True, raise SystemExit on failure.

    Returns:
        True if the command succeeded.
    """
    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            check=check,
            capture_output=False,
            text=True,
        )
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"Command failed with return code {e.returncode}")
        if not check:
            return False
        raise SystemExit(e.returncode)


def main() -> None:
    """Main entry point for linting and formatting."""
    if len(sys.argv) < 2:
        print("Usage: python code/00_lint_format.py [check|fix]")
        sys.exit(1)

    mode = sys.argv[1].lower()
    project_root = Path(__file__).resolve().parent.parent

    # Ensure tools are installed
    try:
        import ruff
        import black
    except ImportError:
        print("Error: Linting tools not found. Installing dev dependencies...")
        run_command([sys.executable, "-m", "pip", "install", "-e", ".[dev]"], check=True)

    code_dir = project_root / "code"
    tests_dir = project_root / "tests"

    if mode == "check":
        print("--- Running Linting Checks (Ruff) ---")
        ruff_cmd = [
            sys.executable, "-m", "ruff", "check",
            str(code_dir), str(tests_dir),
        ]
        run_command(ruff_cmd, check=True)

        print("\n--- Running Formatting Checks (Black) ---")
        black_cmd = [
            sys.executable, "-m", "black",
            "--check",
            str(code_dir), str(tests_dir),
        ]
        run_command(black_cmd, check=True)

        print("\n✅ All checks passed!")

    elif mode == "fix":
        print("--- Running Linting Fixes (Ruff) ---")
        ruff_cmd = [
            sys.executable, "-m", "ruff", "check",
            "--fix",
            str(code_dir), str(tests_dir),
        ]
        run_command(ruff_cmd, check=False) # Ruff might exit non-zero if it can't fix everything, but we proceed to format

        print("\n--- Running Formatting (Black) ---")
        black_cmd = [
            sys.executable, "-m", "black",
            str(code_dir), str(tests_dir),
        ]
        run_command(black_cmd, check=True)

        print("\n--- Re-checking after fix ---")
        # Final verification
        ruff_check = [sys.executable, "-m", "ruff", "check", str(code_dir), str(tests_dir)]
        if not run_command(ruff_check, check=False):
            print("⚠️  Ruff still reports issues that could not be auto-fixed.")
            print("    Please review the output above.")
        else:
            print("✅ Linting clean.")

        black_check = [sys.executable, "-m", "black", "--check", str(code_dir), str(tests_dir)]
        if not run_command(black_check, check=False):
            print("⚠️  Black still reports formatting issues.")
        else:
            print("✅ Formatting clean.")
    else:
        print(f"Unknown mode: {mode}. Use 'check' or 'fix'.")
        sys.exit(1)


if __name__ == "__main__":
    main()