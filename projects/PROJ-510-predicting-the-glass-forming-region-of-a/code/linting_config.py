"""
Linting and formatting configuration for the Glass Forming Region project.

This module provides configuration constants and helper functions for:
- Flake8 linting rules
- Black code formatting
- Isort import sorting
"""

import os
import subprocess
import sys
from typing import List, Optional

# Flake8 configuration
FLAKE8_CONFIG = {
    "max-line-length": 88,
    "extend-ignore": ["E203", "W503"],  # Black compatibility
    "exclude": ["venv", ".git", "__pycache__", "data"],
    "per-file-ignores": {
        "__init__.py": "F401",  # Allow unused imports in __init__.py
    },
}

# Black configuration
BLACK_CONFIG = {
    "line-length": 88,
    "target-version": ["py311"],
    "include": r"\.pyi?$",
    "exclude": r"/(\.git|\.hg|\.mypy_cache|\.tox|venv|\.venv|data)/",
}

# Isort configuration
ISORT_CONFIG = {
    "profile": "black",
    "line_length": 88,
    "skip": ["venv", ".git", "data"],
    "known_first_party": ["utils", "features", "ingestion", "train", "analyze"],
}

def run_flake8(paths: Optional[List[str]] = None, verbose: bool = False) -> bool:
    """
    Run flake8 linting on the specified paths or default to the code/ directory.

    Args:
        paths: List of paths to lint. If None, defaults to ['code/'].
        verbose: If True, print command being executed.

    Returns:
        True if linting passes, False otherwise.
    """
    if paths is None:
        paths = ["code/"]

    cmd = [
        sys.executable,
        "-m",
        "flake8",
        f"--max-line-length={FLAKE8_CONFIG['max-line-length']}",
        f"--extend-ignore={','.join(FLAKE8_CONFIG['extend-ignore'])}",
    ]

    # Add exclude patterns
    for pattern in FLAKE8_CONFIG["exclude"]:
        cmd.extend(["--exclude", pattern])

    cmd.extend(paths)

    if verbose:
        print(f"Running: {' '.join(cmd)}")

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print("Flake8 found issues:")
        print(result.stdout)
        print(result.stderr)
        return False

    if verbose:
        print("Flake8 passed!")

    return True

def run_black(paths: Optional[List[str]] = None, check_only: bool = False, verbose: bool = False) -> bool:
    """
    Run Black code formatting on the specified paths.

    Args:
        paths: List of paths to format. If None, defaults to ['code/'].
        check_only: If True, only check formatting without modifying files.
        verbose: If True, print command being executed.

    Returns:
        True if formatting is correct (or passes check), False otherwise.
    """
    if paths is None:
        paths = ["code/"]

    cmd = [sys.executable, "-m", "black"]

    if check_only:
        cmd.append("--check")

    cmd.extend(["--line-length", str(BLACK_CONFIG["line-length"])])

    for pattern in BLACK_CONFIG["exclude"].strip("/").split("|"):
        cmd.extend(["--exclude", pattern])

    cmd.extend(paths)

    if verbose:
        print(f"Running: {' '.join(cmd)}")

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        if check_only:
            print("Black formatting check failed. Run 'black code/' to fix.")
            print(result.stdout)
            print(result.stderr)
        else:
            print("Black formatting completed with warnings.")
            print(result.stdout)
            print(result.stderr)
        return False

    if verbose:
        print("Black formatting passed!")

    return True

def run_isort(paths: Optional[List[str]] = None, check_only: bool = False, verbose: bool = False) -> bool:
    """
    Run isort import sorting on the specified paths.

    Args:
        paths: List of paths to sort. If None, defaults to ['code/'].
        check_only: If True, only check sorting without modifying files.
        verbose: If True, print command being executed.

    Returns:
        True if sorting is correct (or passes check), False otherwise.
    """
    if paths is None:
        paths = ["code/"]

    cmd = [sys.executable, "-m", "isort"]

    if check_only:
        cmd.append("--check")

    cmd.extend(["--profile", "black"])
    cmd.extend(["--line-length", str(ISORT_CONFIG["line_length"])])

    for pattern in ISORT_CONFIG["skip"]:
        cmd.extend(["--skip", pattern])

    cmd.extend(paths)

    if verbose:
        print(f"Running: {' '.join(cmd)}")

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        if check_only:
            print("Isort import sorting check failed. Run 'isort code/' to fix.")
            print(result.stdout)
            print(result.stderr)
        else:
            print("Isort import sorting completed with warnings.")
            print(result.stdout)
            print(result.stderr)
        return False

    if verbose:
        print("Isort import sorting passed!")

    return True

def run_all_checks(verbose: bool = False) -> bool:
    """
    Run all linting and formatting checks.

    Args:
        verbose: If True, print detailed output for each tool.

    Returns:
        True if all checks pass, False otherwise.
    """
    print("Running linting and formatting checks...")
    print("=" * 50)

    results = []

    print("\n1. Running Flake8...")
    results.append(run_flake8(verbose=verbose))

    print("\n2. Running Black (check only)...")
    results.append(run_black(check_only=True, verbose=verbose))

    print("\n3. Running Isort (check only)...")
    results.append(run_isort(check_only=True, verbose=verbose))

    print("\n" + "=" * 50)
    if all(results):
        print("All checks passed!")
        return True
    else:
        print("Some checks failed. Please fix the issues above.")
        return False

def fix_all(verbose: bool = False) -> bool:
    """
    Run Black and Isort to automatically fix formatting and import issues.

    Args:
        verbose: If True, print detailed output for each tool.

    Returns:
        True if all fixes applied successfully, False otherwise.
    """
    print("Running automatic fixes...")
    print("=" * 50)

    results = []

    print("\n1. Running Black...")
    results.append(run_black(verbose=verbose))

    print("\n2. Running Isort...")
    results.append(run_isort(verbose=verbose))

    print("\n" + "=" * 50)
    if all(results):
        print("All fixes applied successfully!")
        return True
    else:
        print("Some fixes could not be applied. Please review the output above.")
        return False

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run linting and formatting tools")
    parser.add_argument(
        "--check", action="store_true", help="Only check without fixing"
    )
    parser.add_argument(
        "--fix", action="store_true", help="Automatically fix issues"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Verbose output"
    )
    parser.add_argument(
        "paths", nargs="*", default=["code/"], help="Paths to check/fix"
    )

    args = parser.parse_args()

    if args.fix:
        success = fix_all(verbose=args.verbose)
    elif args.check:
        success = run_all_checks(verbose=args.verbose)
    else:
        # Default: run checks
        success = run_all_checks(verbose=args.verbose)

    sys.exit(0 if success else 1)