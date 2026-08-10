"""
Linting and formatting configuration runner for PROJ-799.

This module provides utilities to run flake8 and black checks 
specifically scoped to the code/ directory of the project.
"""
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CODE_DIR = PROJECT_ROOT / "code"

def run_flake8(verbose: bool = False) -> int:
    """
    Run flake8 on the code/ directory.
    
    Args:
        verbose: If True, print command being executed.
        
    Returns:
        Exit code from flake8 (0 for success, non-zero for errors).
    """
    config_path = PROJECT_ROOT / ".flake8"
    cmd = [
        sys.executable, "-m", "flake8",
        str(CODE_DIR),
        f"--config={config_path}"
    ]
    
    if verbose:
        print(f"Running: {' '.join(cmd)}")
        
    try:
        result = subprocess.run(cmd, cwd=PROJECT_ROOT)
        return result.returncode
    except FileNotFoundError:
        print("Error: flake8 not found. Please install it via pip install flake8.")
        return 1

def run_black(check: bool = True, verbose: bool = False) -> int:
    """
    Run black on the code/ directory.
    
    Args:
        check: If True, run in check-only mode (no files modified).
        verbose: If True, print command being executed.
        
    Returns:
        Exit code from black (0 for success, non-zero for errors).
    """
    config_path = PROJECT_ROOT / "pyproject.toml"
    cmd = [
        sys.executable, "-m", "black",
        str(CODE_DIR),
        f"--config={config_path}"
    ]
    
    if check:
        cmd.append("--check")
        
    if verbose:
        print(f"Running: {' '.join(cmd)}")
        
    try:
        result = subprocess.run(cmd, cwd=PROJECT_ROOT)
        return result.returncode
    except FileNotFoundError:
        print("Error: black not found. Please install it via pip install black.")
        return 1

def run_all_checks(fix: bool = False, verbose: bool = False) -> int:
    """
    Run all linting and formatting checks.
    
    Args:
        fix: If True, run black in fix mode (default False, runs --check).
        verbose: If True, print command details.
        
    Returns:
        Combined exit code (0 if all pass, non-zero otherwise).
    """
    print("Running linting and formatting checks for PROJ-799...")
    print(f"Target directory: {CODE_DIR}")
    print("-" * 40)
    
    # Run flake8
    print("1. Running flake8...")
    flake8_code = run_flake8(verbose=verbose)
    if flake8_code == 0:
        print("   ✓ flake8 passed")
    else:
        print("   ✗ flake8 failed")
        
    # Run black
    print("2. Running black...")
    black_mode = "check" if not fix else "format"
    black_code = run_black(check=not fix, verbose=verbose)
    if black_code == 0:
        print(f"   ✓ black ({black_mode}) passed")
    else:
        print(f"   ✗ black ({black_mode}) failed")
        
    print("-" * 40)
    if flake8_code == 0 and black_code == 0:
        print("All checks passed!")
        return 0
    else:
        print("Some checks failed.")
        return 1

def main():
    """Entry point for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Run linting and formatting checks for PROJ-799."
    )
    parser.add_argument(
        "--fix", 
        action="store_true", 
        help="Apply black formatting fixes (default: check only)"
    )
    parser.add_argument(
        "--verbose", 
        action="store_true", 
        help="Print detailed command output"
    )
    
    args = parser.parse_args()
    
    exit_code = run_all_checks(fix=args.fix, verbose=args.verbose)
    sys.exit(exit_code)

if __name__ == "__main__":
    main()