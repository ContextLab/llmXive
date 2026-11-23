"""
Linting and formatting configuration utilities.
Provides functions to run flake8, black, and isort checks from Python.
"""
import subprocess
import sys
from pathlib import Path


def run_flake8() -> int:
    """Run flake8 linter on the codebase."""
    result = subprocess.run(
        [sys.executable, "-m", "flake8", "code/", "tests/"],
        cwd=Path(__file__).parent.parent,
    )
    return result.returncode


def run_black(check_only: bool = True) -> int:
    """Run black formatter on the codebase.
    
    Args:
        check_only: If True, only check formatting (return 0 if OK, 1 if not).
                   If False, reformat files in place.
    """
    cmd = [sys.executable, "-m", "black"]
    if check_only:
        cmd.append("--check")
        cmd.append("--diff")
    cmd.extend(["code/", "tests/"])
    
    result = subprocess.run(
        cmd,
        cwd=Path(__file__).parent.parent,
    )
    return result.returncode


def run_isort(check_only: bool = True) -> int:
    """Run isort import sorter on the codebase.
    
    Args:
        check_only: If True, only check import order (return 0 if OK, 1 if not).
                   If False, reorder imports in place.
    """
    cmd = [sys.executable, "-m", "isort"]
    if check_only:
        cmd.append("--check-only")
        cmd.append("--diff")
    cmd.extend(["code/", "tests/"])
    
    result = subprocess.run(
        cmd,
        cwd=Path(__file__).parent.parent,
    )
    return result.returncode


def main() -> None:
    """Run all linting and formatting checks."""
    print("Running flake8...")
    flake8_code = run_flake8()
    
    print("\nRunning black (check mode)...")
    black_code = run_black(check_only=True)
    
    print("\nRunning isort (check mode)...")
    isort_code = run_isort(check_only=True)
    
    if flake8_code == 0 and black_code == 0 and isort_code == 0:
        print("\n✓ All linting and formatting checks passed!")
        sys.exit(0)
    else:
        print("\n✗ Some checks failed. Run 'make format' or 'make lint-fix' to auto-fix.")
        sys.exit(1)


if __name__ == "__main__":
    main()