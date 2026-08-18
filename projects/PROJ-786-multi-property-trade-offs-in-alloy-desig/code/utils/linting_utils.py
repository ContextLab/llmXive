"""
Utility functions to assist in linting and formatting verification.
This module provides helpers to validate code quality programmatically
if needed during CI/CD or local verification steps.
"""
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple, Optional

def run_ruff_check(paths: Optional[List[str]] = None) -> Tuple[int, str, str]:
    """
    Run ruff check on specified paths.

    Args:
        paths: List of paths to check. If None, checks current directory.

    Returns:
        Tuple of (return_code, stdout, stderr)
    """
    cmd = [sys.executable, "-m", "ruff", "check"]
    if paths:
        cmd.extend(paths)
    else:
        cmd.append(".")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return 1, "", "Error: ruff not found. Install with: pip install ruff"

def run_black_check(paths: Optional[List[str]] = None) -> Tuple[int, str, str]:
    """
    Run black --check on specified paths.

    Args:
        paths: List of paths to check. If None, checks current directory.

    Returns:
        Tuple of (return_code, stdout, stderr)
    """
    cmd = [sys.executable, "-m", "black", "--check"]
    if paths:
        cmd.extend(paths)
    else:
        cmd.append(".")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return 1, "", "Error: black not found. Install with: pip install black"

def run_ruff_format(paths: Optional[List[str]] = None) -> Tuple[int, str, str]:
    """
    Run ruff format on specified paths.

    Args:
        paths: List of paths to format. If None, formats current directory.

    Returns:
        Tuple of (return_code, stdout, stderr)
    """
    cmd = [sys.executable, "-m", "ruff", "format"]
    if paths:
        cmd.extend(paths)
    else:
        cmd.append(".")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return 1, "", "Error: ruff not found. Install with: pip install ruff"

def run_black_format(paths: Optional[List[str]] = None) -> Tuple[int, str, str]:
    """
    Run black on specified paths.

    Args:
        paths: List of paths to format. If None, formats current directory.

    Returns:
        Tuple of (return_code, stdout, stderr)
    """
    cmd = [sys.executable, "-m", "black"]
    if paths:
        cmd.extend(paths)
    else:
        cmd.append(".")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return 1, "", "Error: black not found. Install with: pip install black"

def verify_linting_setup() -> bool:
    """
    Verify that ruff and black are installed and configured.

    Returns:
        True if both tools are available, False otherwise.
    """
    ruff_ok = run_ruff_check([])[0] != 11  # 11 means command not found in some versions, 0 means success
    black_ok = run_black_check([])[0] != 11

    # Check for config files
    root = Path(__file__).parent.parent.parent
    has_ruff_config = (root / "pyproject.toml").exists() or (root / ".ruff.toml").exists()
    has_black_config = (root / "pyproject.toml").exists()

    return ruff_ok and black_ok and has_ruff_config and has_black_config

def main():
    """CLI entry point for linting verification."""
    import argparse

    parser = argparse.ArgumentParser(description="Linting and formatting utilities")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Run checks only (ruff check, black --check)"
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Run formatters to fix issues (ruff format, black)"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify that tools are installed and configured"
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Paths to process (default: current directory)"
    )

    args = parser.parse_args()

    if args.verify:
        if verify_linting_setup():
            print("✓ Linting and formatting tools are properly configured.")
            sys.exit(0)
        else:
            print("✗ Linting and formatting tools are NOT properly configured.")
            print("  Ensure ruff and black are installed and config files exist.")
            sys.exit(1)

    if args.check:
        print("Running ruff check...")
        code, out, err = run_ruff_check(args.paths if args.paths else None)
        print(out)
        print(err)
        if code != 0:
            print("✗ Ruff check failed.")

        print("\nRunning black check...")
        code, out, err = run_black_check(args.paths if args.paths else None)
        print(out)
        print(err)
        if code != 0:
            print("✗ Black check failed.")

    if args.fix:
        print("Running ruff format...")
        code, out, err = run_ruff_format(args.paths if args.paths else None)
        print(out)
        print(err)

        print("\nRunning black format...")
        code, out, err = run_black_format(args.paths if args.paths else None)
        print(out)
        print(err)

if __name__ == "__main__":
    main()
