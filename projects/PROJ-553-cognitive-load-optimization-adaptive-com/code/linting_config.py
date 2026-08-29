"""
Linting and Formatting Configuration Utilities.

This module provides functions to configure and run linting (ruff/flake8)
and formatting (black) tools for the project.
"""
from pathlib import Path
import subprocess
import sys
from typing import Optional

# Project root is assumed to be the parent of the 'code' directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent

def get_ruff_command(check: bool = True) -> list[str]:
    """
    Generate the ruff command.
    
    Args:
        check: If True, run in check-only mode (no fixes). If False, run fixes.
    
    Returns:
        List of command arguments.
    """
    cmd = ["ruff"]
    if check:
        cmd.append("check")
        cmd.append("--exit-non-zero-on-fix")
    else:
        cmd.append("check")
        cmd.append("--fix")
    cmd.append(str(PROJECT_ROOT))
    return cmd

def get_black_command(check: bool = True) -> list[str]:
    """
    Generate the black command.
    
    Args:
        check: If True, run in check-only mode. If False, format files.
    
    Returns:
        List of command arguments.
    """
    cmd = ["black"]
    if check:
        cmd.append("--check")
        cmd.append("--diff")
    cmd.append(str(PROJECT_ROOT))
    return cmd

def get_format_check_command() -> list[str]:
    """
    Get the command to check formatting (black).
    
    Returns:
        List of command arguments.
    """
    return get_black_command(check=True)

def get_lint_check_command() -> list[str]:
    """
    Get the command to check linting (ruff).
    
    Returns:
        List of command arguments.
    """
    return get_ruff_command(check=True)

def run_formatter(check: bool = True) -> int:
    """
    Run the formatter (black).
    
    Args:
        check: If True, check only. If False, apply fixes.
    
    Returns:
        Exit code (0 for success, non-zero for failure).
    """
    cmd = get_black_command(check=check)
    print(f"Running formatter: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, cwd=PROJECT_ROOT)
        return result.returncode
    except FileNotFoundError:
        print("Error: 'black' not found. Please install it via pip.", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error running formatter: {e}", file=sys.stderr)
        return 1

def run_linter(check: bool = True) -> int:
    """
    Run the linter (ruff).
    
    Args:
        check: If True, check only. If False, apply fixes.
    
    Returns:
        Exit code (0 for success, non-zero for failure).
    """
    cmd = get_ruff_command(check=check)
    print(f"Running linter: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, cwd=PROJECT_ROOT)
        return result.returncode
    except FileNotFoundError:
        print("Error: 'ruff' not found. Please install it via pip.", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error running linter: {e}", file=sys.stderr)
        return 1

def main() -> None:
    """
    Main entry point for running linting and formatting checks.
    
    This function runs both the linter and the formatter in check mode.
    If either fails, it exits with a non-zero status code.
    """
    print("Running Linting and Formatting Checks...")
    print("-" * 40)
    
    lint_exit = run_linter(check=True)
    if lint_exit != 0:
        print("Linting failed. Please fix the issues above.")
    
    print("-" * 40)
    
    format_exit = run_formatter(check=True)
    if format_exit != 0:
        print("Formatting check failed. Please run 'black .' to fix.")
    
    if lint_exit != 0 or format_exit != 0:
        sys.exit(1)
    else:
        print("All checks passed.")
        sys.exit(0)

if __name__ == "__main__":
    main()
