"""
Linting and formatting configuration for the project.

This module provides utilities to check code quality using
black, flake8, and pylint.
"""

import subprocess
import sys
from pathlib import Path

def check_black(project_root: Path = None) -> bool:
    """
    Check code formatting with black.

    Args:
        project_root: Root directory of the project. Defaults to current directory.

    Returns:
        True if formatting is correct, False otherwise.
    """
    if project_root is None:
        project_root = Path.cwd()

    code_dir = project_root / "code"
    tests_dir = project_root / "tests"

    try:
        result = subprocess.run(
            ["black", "--check", "--diff", str(code_dir), str(tests_dir)],
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode == 0:
            print("✓ Code formatting is correct (black)")
            return True
        else:
            print("✗ Code formatting issues found:")
            print(result.stdout)
            return False

    except FileNotFoundError:
        print("⚠ black not installed. Run: pip install black")
        return False

def check_flake8(project_root: Path = None) -> bool:
    """
    Check code style with flake8.

    Args:
        project_root: Root directory of the project. Defaults to current directory.

    Returns:
        True if no style issues, False otherwise.
    """
    if project_root is None:
        project_root = Path.cwd()

    code_dir = project_root / "code"
    tests_dir = project_root / "tests"

    try:
        result = subprocess.run(
            ["flake8", str(code_dir), str(tests_dir)],
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode == 0:
            print("✓ No style issues found (flake8)")
            return True
        else:
            print("✗ Style issues found:")
            print(result.stdout)
            return False

    except FileNotFoundError:
        print("⚠ flake8 not installed. Run: pip install flake8")
        return False

def check_pylint(project_root: Path = None) -> bool:
    """
    Check code quality with pylint.

    Args:
        project_root: Root directory of the project. Defaults to current directory.

    Returns:
        True if quality score is acceptable, False otherwise.
    """
    if project_root is None:
        project_root = Path.cwd()

    code_dir = project_root / "code"

    try:
        result = subprocess.run(
            ["pylint", "--score=yes", str(code_dir)],
            capture_output=True,
            text=True,
            check=False
        )

        # Parse score from output
        output = result.stdout
        if "Your code has been rated at" in output:
            # Extract rating
            rating_line = [line for line in output.split('\n') if "Your code has been rated at" in line][0]
            score = float(rating_line.split('/')[-1].strip().split()[0])

            if score >= 8.0:
                print(f"✓ Code quality score: {score}/10 (pylint)")
                return True
            else:
                print(f"✗ Code quality score too low: {score}/10 (pylint)")
                return False
        else:
            print("⚠ Could not parse pylint score")
            print(output)
            return False

    except FileNotFoundError:
        print("⚠ pylint not installed. Run: pip install pylint")
        return False

def main():
    """Run all linting checks."""
    print("Running linting checks...")
    print("=" * 50)

    results = []
    results.append(check_black())
    results.append(check_flake8())
    results.append(check_pylint())

    print("=" * 50)
    if all(results):
        print("✓ All linting checks passed!")
        return 0
    else:
        print("✗ Some linting checks failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())