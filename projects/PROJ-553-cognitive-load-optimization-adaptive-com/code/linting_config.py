"""
Configuration utilities for linting and formatting tools.
Provides command-line arguments and configuration paths for ruff and black.
"""
from pathlib import Path
import subprocess
import sys

def get_ruff_command(check: bool = False) -> list:
    """
    Returns the ruff command list.
    
    Args:
        check: If True, run in check-only mode (no fixes applied).
    
    Returns:
        List of command parts to be executed via subprocess.
    """
    cmd = ["ruff", "check"]
    if check:
        cmd.append("--fix=false")
    else:
        # Default behavior: attempt to fix if possible
        cmd.append("--fix")
    return cmd

def get_black_command(check: bool = False) -> list:
    """
    Returns the black command list.
    
    Args:
        check: If True, run in check-only mode.
    
    Returns:
        List of command parts to be executed via subprocess.
    """
    cmd = ["black"]
    if check:
        cmd.append("--check")
        cmd.append("--diff")
    return cmd

def get_format_check_command() -> list:
    """
    Returns the combined format check command sequence.
    Typically runs black --check followed by ruff check.
    
    Returns:
        List of lists, where each inner list is a command to run.
    """
    return [get_black_command(check=True), get_ruff_command(check=True)]

def get_lint_check_command() -> list:
    """
    Returns the lint check command sequence.
    Primarily relies on ruff for linting.
    
    Returns:
        List of command parts for ruff check.
    """
    return get_ruff_command(check=True)

def run_formatter(check_only: bool = False) -> bool:
    """
    Executes the formatter (black) on the project.
    
    Args:
        check_only: If True, only verify formatting without modifying files.
    
    Returns:
        True if formatting is correct (or fixed), False if errors remain.
    """
    cmd = get_black_command(check=check_only)
    try:
        result = subprocess.run(cmd, check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError:
        return False

def run_linter(check_only: bool = True) -> bool:
    """
    Executes the linter (ruff) on the project.
    
    Args:
        check_only: Ignored for ruff in this context, but kept for API consistency.
    
    Returns:
        True if no linting errors found, False otherwise.
    """
    cmd = get_lint_check_command()
    try:
        result = subprocess.run(cmd, check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError:
        return False

def main():
    """
    Entry point for manual linting/formatting verification.
    """
    print("Running Linting and Formatting checks...")
    
    print("\n1. Checking Black formatting...")
    if run_formatter(check_only=True):
        print("   [PASS] Code is properly formatted.")
    else:
        print("   [FAIL] Code needs formatting. Run 'black .' to fix.")
        return 1

    print("\n2. Checking Ruff linting...")
    if run_linter(check_only=True):
        print("   [PASS] No linting errors found.")
    else:
        print("   [FAIL] Linting errors found. Run 'ruff check .' to see details.")
        return 1

    print("\nAll checks passed!")
    return 0

if __name__ == "__main__":
    sys.exit(main())