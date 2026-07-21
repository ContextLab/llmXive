"""
Configuration and execution helpers for linting and formatting tools.
Provides functions to run ruff and black checks/formats programmatically.
"""
import subprocess
import sys
from pathlib import Path
from typing import Tuple, Optional

# Project root is assumed to be the parent of the 'code' directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def run_linter(check_only: bool = True, fix: bool = False) -> Tuple[int, str]:
    """
    Run ruff linter on the project code directory.

    Args:
        check_only: If True, only check for errors (exit code != 0 on failure).
                   If False, attempt to fix issues automatically.
        fix: Deprecated, kept for compatibility. If True, implies --fix.

    Returns:
        Tuple of (exit_code, output_string)
    """
    code_dir = PROJECT_ROOT / "code"
    config_file = PROJECT_ROOT / "pyproject.toml"

    cmd = [
        sys.executable, "-m", "ruff",
        "check" if check_only else "check",
        str(code_dir),
        "--config", str(config_file),
    ]

    if fix:
        cmd.append("--fix")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT)
        )
        return result.returncode, result.stdout + result.stderr
    except FileNotFoundError:
        return 1, "Error: ruff is not installed. Please run 'pip install ruff'."
    except Exception as e:
        return 1, f"Error running ruff: {e}"


def run_formatter(check_only: bool = True) -> Tuple[int, str]:
    """
    Run black formatter on the project code directory.

    Args:
        check_only: If True, only check formatting (exit code != 0 if unformatted).
                   If False, reformat files in place.

    Returns:
        Tuple of (exit_code, output_string)
    """
    code_dir = PROJECT_ROOT / "code"
    config_file = PROJECT_ROOT / "pyproject.toml"

    cmd = [
        sys.executable, "-m", "black",
        "--config", str(config_file),
    ]

    if check_only:
        cmd.append("--check")
        cmd.append("--diff")

    cmd.append(str(code_dir))

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT)
        )
        return result.returncode, result.stdout + result.stderr
    except FileNotFoundError:
        return 1, "Error: black is not installed. Please run 'pip install black'."
    except Exception as e:
        return 1, f"Error running black: {e}"


def main():
    """
    Main entry point to run linting and formatting checks.
    Useful for CI/CD pipelines or local verification scripts.
    """
    print("Running Linting (ruff)...")
    lint_code, lint_out = run_linter(check_only=True)
    if lint_code == 0:
        print("✓ Linting passed.")
    else:
        print("✗ Linting failed:")
        print(lint_out)

    print("\nRunning Formatting Check (black)...")
    fmt_code, fmt_out = run_formatter(check_only=True)
    if fmt_code == 0:
        print("✓ Formatting check passed.")
    else:
        print("✗ Formatting check failed:")
        print(fmt_out)

    if lint_code != 0 or fmt_code != 0:
        sys.exit(1)
    else:
        print("\n✓ All checks passed.")
        sys.exit(0)


if __name__ == "__main__":
    main()