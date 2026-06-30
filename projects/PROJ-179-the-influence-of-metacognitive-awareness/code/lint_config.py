"""
Configuration and helper utilities for linting and formatting tools.

This module defines the standard configuration for flake8 and black
used across the project to ensure code quality and consistency.
"""

import os
import subprocess
import sys

# Project root relative to this file's location
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Flake8 configuration
FLAKE8_CONFIG = {
    "max-line-length": 88,
    "extend-ignore": [
        "E203",  # Whitespace before ':', conflicts with Black
        "W503",  # Line break before binary operator, conflicts with Black
    ],
    "exclude": [
        ".git",
        "__pycache__",
        "build",
        "dist",
        ".eggs",
        "*.egg-info",
        "data",  # Excluding data directories from linting
        "venv",
        ".venv",
    ],
    "per-file-ignores": {
        # Allow higher line length in test files for readability
        "tests/*": "E501",
        # Allow unused imports in __init__.py for API surface exposure
        "**/__init__.py": "F401",
    },
}

# Black configuration
BLACK_CONFIG = {
    "line-length": 88,
    "target-version": ["py38", "py39", "py10", "py11"],
    "exclude": r"""
        (
            /.git
            | /__pycache__
            | /build
            | /dist
            | /.eggs
            | \.egg-info
            | /data
            | /venv
            | /\.venv
        )/
    """,
}

def run_flake8(path=None):
    """
    Run flake8 on the specified path or the project root.
    
    Args:
        path (str, optional): Specific path to check. Defaults to PROJECT_ROOT.
        
    Returns:
        int: Exit code from flake8 (0 if clean, non-zero if issues found).
    """
    target = path if path else PROJECT_ROOT
    cmd = [
        sys.executable, "-m", "flake8",
        f"--max-line-length={FLAKE8_CONFIG['max-line-length']}",
        f"--extend-ignore={','.join(FLAKE8_CONFIG['extend-ignore'])}",
        "--exclude=" + ",".join(FLAKE8_CONFIG["exclude"]),
        target
    ]
    
    try:
        result = subprocess.run(cmd, cwd=PROJECT_ROOT)
        return result.returncode
    except FileNotFoundError:
        print("Error: flake8 not found. Please install it via 'pip install flake8'.")
        return 1
    except Exception as e:
        print(f"Error running flake8: {e}")
        return 1

def run_black(path=None, check_only=False):
    """
    Run black on the specified path or the project root.
    
    Args:
        path (str, optional): Specific path to format. Defaults to PROJECT_ROOT.
        check_only (bool): If True, run in 'check' mode (no modification).
        
    Returns:
        int: Exit code from black (0 if clean/formatted, non-zero if issues).
    """
    target = path if path else PROJECT_ROOT
    cmd = [
        sys.executable, "-m", "black",
        f"--line-length={BLACK_CONFIG['line-length']}",
    ]
    
    if check_only:
        cmd.append("--check")
        cmd.append("--diff")
    
    # Add target path
    cmd.append(target)
    
    try:
        result = subprocess.run(cmd, cwd=PROJECT_ROOT)
        return result.returncode
    except FileNotFoundError:
        print("Error: black not found. Please install it via 'pip install black'.")
        return 1
    except Exception as e:
        print(f"Error running black: {e}")
        return 1

def run_isort(path=None):
    """
    Run isort to sort imports.
    
    Args:
        path (str, optional): Specific path to format. Defaults to PROJECT_ROOT.
        
    Returns:
        int: Exit code from isort.
    """
    target = path if path else PROJECT_ROOT
    cmd = [
        sys.executable, "-m", "isort",
        "--profile", "black",
        "--line-length", "88",
        target
    ]
    
    try:
        result = subprocess.run(cmd, cwd=PROJECT_ROOT)
        return result.returncode
    except FileNotFoundError:
        print("Error: isort not found. Please install it via 'pip install isort'.")
        return 1
    except Exception as e:
        print(f"Error running isort: {e}")
        return 1

def run_all_checks(path=None):
    """
    Run all linting and formatting checks.
    
    Args:
        path (str, optional): Specific path to check.
        
    Returns:
        bool: True if all checks pass, False otherwise.
    """
    print("Running flake8...")
    flake8_code = run_flake8(path)
    
    print("\nRunning black (check mode)...")
    black_code = run_black(path, check_only=True)
    
    print("\nRunning isort (check mode)...")
    isort_code = run_isort(path)
    
    if flake8_code == 0 and black_code == 0 and isort_code == 0:
        print("\n✓ All checks passed!")
        return True
    else:
        print("\n✗ Some checks failed. Please fix the issues above.")
        return False

if __name__ == "__main__":
    # Default to running checks on the whole project
    success = run_all_checks()
    sys.exit(0 if success else 1)
