"""
Script to run linter (ruff) and formatter (black) checks and fixes.
This script wraps the command-line tools to ensure consistent project styling.
"""
import subprocess
import sys
from pathlib import Path

def run_ruff_check():
    """Run ruff check on the project."""
    print("Running ruff check...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "check", "."],
            check=True,
            capture_output=True,
            text=True
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        print("Ruff check passed.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Ruff check failed:\n{e.stdout}\n{e.stderr}")
        return False

def run_ruff_fix():
    """Run ruff check with --fix to auto-fix issues."""
    print("Running ruff fix...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "check", "--fix", "."],
            check=True,
            capture_output=True,
            text=True
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        print("Ruff fix completed.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Ruff fix failed (remaining issues):\n{e.stdout}\n{e.stderr}")
        return False

def run_black_check():
    """Run black check (diff mode) on the project."""
    print("Running black check...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "black", "--check", "."],
            check=True,
            capture_output=True,
            text=True
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        print("Black check passed.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Black check failed (run 'black .' to fix):\n{e.stdout}\n{e.stderr}")
        return False

def run_black_format():
    """Run black formatter on the project."""
    print("Running black format...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "black", "."],
            check=True,
            capture_output=True,
            text=True
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        print("Black format completed.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Black format failed:\n{e.stdout}\n{e.stderr}")
        return False

def run_lint_and_format():
    """Run full lint and format cycle: fix ruff, then format black."""
    print("=== Starting Lint and Format Cycle ===")
    
    # 1. Auto-fix ruff issues
    if not run_ruff_fix():
        print("Warning: Ruff could not fix all issues automatically.")
    
    # 2. Format with black
    if not run_black_format():
        print("Warning: Black formatting failed.")
    
    # 3. Final check
    print("\n--- Final Verification ---")
    ruff_ok = run_ruff_check()
    black_ok = run_black_check()

    if ruff_ok and black_ok:
        print("\n=== Lint and Format Cycle: SUCCESS ===")
        return True
    else:
        print("\n=== Lint and Format Cycle: FAILED ===")
        return False

if __name__ == "__main__":
    success = run_lint_and_format()
    sys.exit(0 if success else 1)