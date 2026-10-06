"""
Script to run ruff static analysis and formatting on the codebase.

This script executes `ruff check --fix` to fix all reported issues
and `ruff format` to ensure consistent code style.

Usage:
    python code/scripts/run_ruff_check.py
"""
import subprocess
import sys
import os
from pathlib import Path
import json
from datetime import datetime


def run_ruff_check(code_dir: Path) -> bool:
    """
    Run ruff check --fix on the code directory.
    
    Args:
        code_dir: Path to the code directory to check.
        
    Returns:
        True if ruff check --fix completed successfully (exit code 0),
        False otherwise.
    """
    print(f"Running ruff check --fix on {code_dir}...")
    
    try:
        result = subprocess.run(
            ["ruff", "check", "--fix", str(code_dir)],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.stdout:
            print("Ruff check output:")
            print(result.stdout)
        
        if result.stderr:
            print("Ruff check errors:")
            print(result.stderr)
        
        if result.returncode == 0:
            print("✓ Ruff check passed: No issues found or all issues fixed.")
            return True
        else:
            print(f"✗ Ruff check failed with exit code {result.returncode}")
            print("Some issues could not be fixed automatically. Please fix manually.")
            return False
            
    except subprocess.TimeoutExpired:
        print("✗ Ruff check timed out after 5 minutes")
        return False
    except FileNotFoundError:
        print("✗ Ruff is not installed. Please install it via: pip install ruff")
        return False
    except Exception as e:
        print(f"✗ Error running ruff check: {e}")
        return False


def run_ruff_format(code_dir: Path) -> bool:
    """
    Run ruff format on the code directory.
    
    Args:
        code_dir: Path to the code directory to format.
        
    Returns:
        True if ruff format completed successfully (exit code 0),
        False otherwise.
    """
    print(f"Running ruff format on {code_dir}...")
    
    try:
        result = subprocess.run(
            ["ruff", "format", str(code_dir)],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.stdout:
            print("Ruff format output:")
            print(result.stdout)
        
        if result.stderr:
            print("Ruff format errors:")
            print(result.stderr)
        
        if result.returncode == 0:
            print("✓ Ruff format completed successfully.")
            return True
        else:
            print(f"✗ Ruff format failed with exit code {result.returncode}")
            return False
            
    except subprocess.TimeoutExpired:
        print("✗ Ruff format timed out after 5 minutes")
        return False
    except FileNotFoundError:
        print("✗ Ruff is not installed. Please install it via: pip install ruff")
        return False
    except Exception as e:
        print(f"✗ Error running ruff format: {e}")
        return False


def main():
    """Main entry point for the ruff check script."""
    # Determine the code directory (relative to this script)
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent
    code_dir = project_root / "code"
    
    if not code_dir.exists():
        print(f"✗ Code directory not found: {code_dir}")
        sys.exit(1)
    
    print("=" * 60)
    print("Running Static Analysis and Formatting")
    print("=" * 60)
    
    # Run ruff check --fix
    check_success = run_ruff_check(code_dir)
    
    # Run ruff format
    format_success = run_ruff_format(code_dir)
    
    print("=" * 60)
    print("Summary:")
    print(f"  Ruff check --fix: {'PASSED' if check_success else 'FAILED'}")
    print(f"  Ruff format: {'PASSED' if format_success else 'FAILED'}")
    print("=" * 60)
    
    if check_success and format_success:
        print("✓ All static analysis and formatting tasks completed successfully.")
        sys.exit(0)
    else:
        print("✗ Some tasks failed. Please review the output above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
