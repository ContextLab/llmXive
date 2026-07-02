"""
Configuration and execution scripts for linting (flake8) and formatting (black).

This module provides a unified entry point to run linting and formatting checks
on the project codebase. It ensures consistency with the project's style guide.

Usage:
    python code/lint_config.py check       # Run flake8 checks
    python code/lint_config.py format      # Run black formatting
    python code/lint_config.py fix         # Run black formatting and isort
    python code/lint_config.py all         # Run check, then format
"""

import subprocess
import sys
import os
from pathlib import Path

# Project root is assumed to be the parent of the 'code' directory
PROJECT_ROOT = Path(__file__).parent.parent

# Configuration for flake8
FLAKE8_CONFIG = {
    "max-line-length": 88,
    "extend-ignore": "E203, W503", # Black compatibility
    "exclude": "venv, .git, __pycache__, build, dist",
    "select": "E,W,F,C,N",
}

# Configuration for black
BLACK_CONFIG = {
    "line-length": 88,
    "target-version": ["py311"],
}

def run_command(cmd: list, description: str) -> bool:
    """
    Execute a shell command and report the result.
    
    Args:
        cmd: List of command arguments.
        description: Human-readable description of the action.
        
    Returns:
        True if the command succeeded (exit code 0), False otherwise.
    """
    print(f"Running: {description}...")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            cwd=PROJECT_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False # We handle the exit code manually
        )
        
        if result.returncode == 0:
            print(f"✅ {description}: PASSED")
            return True
        else:
            print(f"❌ {description}: FAILED")
            if result.stdout:
                print(result.stdout)
            return False
            
    except FileNotFoundError:
        print(f"❌ Error: Command not found. Please ensure dependencies are installed.")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during {description}: {e}")
        return False

def check_linting():
    """Run flake8 to check for style and syntax errors."""
    cmd = [
        sys.executable, "-m", "flake8",
        "--max-line-length", str(FLAKE8_CONFIG["max-line-length"]),
        "--extend-ignore", FLAKE8_CONFIG["extend-ignore"],
        "--exclude", FLAKE8_CONFIG["exclude"],
        "--select", FLAKE8_CONFIG["select"],
        "code/", "tests/"
    ]
    return run_command(cmd, "Flake8 Linting")

def run_formatting():
    """Run black to format code."""
    cmd = [
        sys.executable, "-m", "black",
        "--line-length", str(BLACK_CONFIG["line-length"]),
        "--target-version", "py311",
        "--check", # Check only, don't modify files
        "code/", "tests/"
    ]
    return run_command(cmd, "Black Formatting Check")

def fix_formatting():
    """Run black and isort to format code and fix imports."""
    # Run isort first
    isort_cmd = [
        sys.executable, "-m", "isort",
        "--profile", "black",
        "code/", "tests/"
    ]
    print("Running: Auto-formatting imports (isort)...")
    subprocess.run(isort_cmd, cwd=PROJECT_ROOT)
    
    # Run black
    black_cmd = [
        sys.executable, "-m", "black",
        "--line-length", str(BLACK_CONFIG["line-length"]),
        "--target-version", "py311",
        "code/", "tests/"
    ]
    print("Running: Auto-formatting code (black)...")
    subprocess.run(black_cmd, cwd=PROJECT_ROOT)
    
    print("✅ Formatting applied successfully.")

def main():
    """Main entry point for the linting and formatting tool."""
    if len(sys.argv) < 2:
        print("Usage: python code/lint_config.py [check|format|fix|all]")
        sys.exit(1)
        
    action = sys.argv[1].lower()
    
    if action == "check":
        success = True
        if not check_linting():
            success = False
        if not run_formatting():
            success = False
        sys.exit(0 if success else 1)
        
    elif action == "format":
        # Just check if formatting is correct
        sys.exit(0 if run_formatting() else 1)
        
    elif action == "fix":
        fix_formatting()
        sys.exit(0)
        
    elif action == "all":
        print("--- Checking ---")
        check_ok = True
        if not check_linting():
            check_ok = False
        if not run_formatting():
            check_ok = False
        
        if not check_ok:
            print("\n--- Formatting issues found. Applying fixes... ---")
            fix_formatting()
            print("\n--- Re-checking after fix ---")
            # Re-run checks to ensure fixes worked
            final_ok = True
            if not check_linting():
                final_ok = False
            if not run_formatting():
                final_ok = False
            
            if final_ok:
                print("\n✅ All checks passed after formatting.")
                sys.exit(0)
            else:
                print("\n❌ Checks still failing after formatting.")
                sys.exit(1)
        else:
            print("\n✅ All checks passed.")
            sys.exit(0)
    
    else:
        print(f"Unknown action: {action}")
        sys.exit(1)

if __name__ == "__main__":
    main()
