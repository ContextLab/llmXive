"""
Linting and formatting configuration helpers.

This module provides functions to run flake8, black, and isort checks
and fixes on the project codebase.
"""
import os
import subprocess
import sys
from typing import List, Optional

def run_flake8(path: Optional[str] = None) -> int:
    """
    Run flake8 linting checks.

    Args:
        path: Optional path to check. Defaults to current directory.

    Returns:
        Exit code from flake8 (0 for success, non-zero for errors).
    """
    target = path if path else "."
    cmd = [sys.executable, "-m", "flake8", target]
    print(f"Running flake8 on {target}...")
    result = subprocess.run(cmd)
    return result.returncode

def run_black(path: Optional[str] = None, check_only: bool = False) -> int:
    """
    Run black formatting checks or fixes.

    Args:
        path: Optional path to check. Defaults to current directory.
        check_only: If True, only check formatting (don't modify files).

    Returns:
        Exit code from black (0 for success, non-zero for errors).
    """
    target = path if path else "."
    if check_only:
        cmd = [sys.executable, "-m", "black", "--check", target]
        print(f"Checking black formatting on {target}...")
    else:
        cmd = [sys.executable, "-m", "black", target]
        print(f"Running black formatter on {target}...")
    result = subprocess.run(cmd)
    return result.returncode

def run_isort(path: Optional[str] = None, check_only: bool = False) -> int:
    """
    Run isort import sorting checks or fixes.

    Args:
        path: Optional path to check. Defaults to current directory.
        check_only: If True, only check sorting (don't modify files).

    Returns:
        Exit code from isort (0 for success, non-zero for errors).
    """
    target = path if path else "."
    if check_only:
        cmd = [sys.executable, "-m", "isort", "--check-only", target]
        print(f"Checking isort imports on {target}...")
    else:
        cmd = [sys.executable, "-m", "isort", target]
        print(f"Running isort import sorter on {target}...")
    result = subprocess.run(cmd)
    return result.returncode

def run_all_checks() -> bool:
    """
    Run all linting and formatting checks.

    Returns:
        True if all checks pass, False otherwise.
    """
    print("=" * 60)
    print("Running all linting and formatting checks")
    print("=" * 60)

    all_passed = True

    # Run flake8
    if run_flake8() != 0:
        all_passed = False
        print("❌ flake8 checks failed")
    else:
        print("✅ flake8 checks passed")

    # Run black check
    if run_black(check_only=True) != 0:
        all_passed = False
        print("❌ black formatting checks failed")
    else:
        print("✅ black formatting checks passed")

    # Run isort check
    if run_isort(check_only=True) != 0:
        all_passed = False
        print("❌ isort import checks failed")
    else:
        print("✅ isort import checks passed")

    if all_passed:
        print("\n" + "=" * 60)
        print("✅ All checks passed!")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ Some checks failed. Run 'python code/linting_config.py fix_all' to fix.")
        print("=" * 60)

    return all_passed

def fix_all() -> bool:
    """
    Automatically fix all formatting and import issues.

    Returns:
        True if fixes were applied successfully, False otherwise.
    """
    print("=" * 60)
    print("Running automatic fixes for formatting and imports")
    print("=" * 60)

    # Fix isort
    print("\nFixing imports with isort...")
    isort_result = run_isort(check_only=False)

    # Fix black
    print("\nFixing formatting with black...")
    black_result = run_black(check_only=False)

    # Run flake8 (no auto-fix, but show remaining issues)
    print("\nChecking remaining linting issues with flake8...")
    flake8_result = run_flake8()

    if isort_result == 0 and black_result == 0:
        print("\n" + "=" * 60)
        print("✅ Formatting and imports fixed successfully!")
        print("=" * 60)
        if flake8_result != 0:
            print("⚠️  Some flake8 issues remain. Please fix them manually.")
        return True
    else:
        print("\n" + "=" * 60)
        print("❌ Some fixes failed. Please check the output above.")
        print("=" * 60)
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "fix":
        success = fix_all()
        sys.exit(0 if success else 1)
    else:
        success = run_all_checks()
        sys.exit(0 if success else 1)