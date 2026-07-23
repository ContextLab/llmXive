"""
Linting and formatting utilities for the project.
Provides functions to run flake8, black, and isort checks.
"""
import subprocess
import sys
from pathlib import Path


def run_flake8() -> int:
    """
    Run flake8 linting checks.
    Returns 0 if successful, non-zero otherwise.
    """
    project_root = Path(__file__).resolve().parent.parent
    config_path = project_root / ".flake8"
    
    if not config_path.exists():
        print("Warning: .flake8 config file not found. Using defaults.")
    
    cmd = [
        sys.executable, "-m", "flake8",
        "code/", "tests/"
    ]
    
    try:
        result = subprocess.run(cmd, cwd=project_root)
        return result.returncode
    except FileNotFoundError:
        print("Error: flake8 not found. Please install it: pip install flake8")
        return 1


def run_black(check_only: bool = True) -> int:
    """
    Run black formatting checks.
    If check_only is True, only check formatting without modifying files.
    Returns 0 if successful, non-zero otherwise.
    """
    project_root = Path(__file__).resolve().parent.parent
    config_path = project_root / "pyproject.toml"
    
    if not config_path.exists():
        print("Warning: pyproject.toml config file not found. Using defaults.")
    
    cmd = [
        sys.executable, "-m", "black",
        "--config", str(config_path)
    ]
    
    if check_only:
        cmd.append("--check")
        cmd.append("--diff")
    
    cmd.extend(["code/", "tests/"])
    
    try:
        result = subprocess.run(cmd, cwd=project_root)
        return result.returncode
    except FileNotFoundError:
        print("Error: black not found. Please install it: pip install black")
        return 1


def run_isort(check_only: bool = True) -> int:
    """
    Run isort import sorting checks.
    If check_only is True, only check sorting without modifying files.
    Returns 0 if successful, non-zero otherwise.
    """
    project_root = Path(__file__).resolve().parent.parent
    config_path = project_root / "pyproject.toml"
    
    if not config_path.exists():
        print("Warning: pyproject.toml config file not found. Using defaults.")
    
    cmd = [
        sys.executable, "-m", "isort",
        "--settings-path", str(config_path)
    ]
    
    if check_only:
        cmd.append("--check-only")
        cmd.append("--diff")
    
    cmd.extend(["code/", "tests/"])
    
    try:
        result = subprocess.run(cmd, cwd=project_root)
        return result.returncode
    except FileNotFoundError:
        print("Error: isort not found. Please install it: pip install isort")
        return 1


def main():
    """
    Main entry point for running all linting and formatting checks.
    """
    print("Running flake8...")
    flake8_result = run_flake8()
    
    print("\nRunning black (check mode)...")
    black_result = run_black(check_only=True)
    
    print("\nRunning isort (check mode)...")
    isort_result = run_isort(check_only=True)
    
    if flake8_result == 0 and black_result == 0 and isort_result == 0:
        print("\n✓ All linting and formatting checks passed!")
        return 0
    else:
        print("\n✗ Some checks failed.")
        if flake8_result != 0:
            print("  - flake8 failed")
        if black_result != 0:
            print("  - black failed")
        if isort_result != 0:
            print("  - isort failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
