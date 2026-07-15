"""
Linting and formatting configuration utilities for the project.

This module provides functions to run linting checks (flake8, pylint)
and code formatting (black, isort) across the project.
"""
import subprocess
import sys
import os
import argparse
from pathlib import Path
from typing import List, Optional, Tuple


def run_command(cmd: List[str], cwd: Optional[str] = None) -> Tuple[int, str, str]:
    """
    Run a shell command and return exit code, stdout, and stderr.
    
    Args:
        cmd: Command and arguments as a list
        cwd: Working directory (default: current directory)
        
    Returns:
        Tuple of (exit_code, stdout, stderr)
    """
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd or os.getcwd(),
            capture_output=True,
            text=True,
            check=False
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return -1, "", str(e)


def check_linting(tool: str = "flake8", path: str = ".") -> int:
    """
    Run a linting tool on the specified path.
    
    Args:
        tool: Linting tool to run ('flake8' or 'pylint')
        path: Path to lint (default: current directory)
        
    Returns:
        Exit code from the linting tool
    """
    if tool == "flake8":
        cmd = ["python", "-m", "flake8", path]
    elif tool == "pylint":
        cmd = ["python", "-m", "pylint", path]
    else:
        print(f"Unknown linting tool: {tool}")
        return 1
        
    exit_code, stdout, stderr = run_command(cmd)
    
    if stdout:
        print(stdout)
    if stderr:
        print(stderr, file=sys.stderr)
        
    return exit_code


def format_code(tool: str = "black", path: str = ".") -> int:
    """
    Format code using the specified tool.
    
    Args:
        tool: Formatting tool ('black' or 'isort')
        path: Path to format (default: current directory)
        
    Returns:
        Exit code from the formatting tool
    """
    if tool == "black":
        cmd = ["python", "-m", "black", path]
    elif tool == "isort":
        cmd = ["python", "-m", "isort", path]
    else:
        print(f"Unknown formatting tool: {tool}")
        return 1
        
    exit_code, stdout, stderr = run_command(cmd)
    
    if stdout:
        print(stdout)
    if stderr:
        print(stderr, file=sys.stderr)
        
    return exit_code


def main():
    """Main entry point for the linting configuration CLI."""
    parser = argparse.ArgumentParser(
        description="Run linting and formatting tools on the project."
    )
    parser.add_argument(
        "action",
        choices=["lint", "format", "check"],
        help="Action to perform: lint (check only), format (fix), or check (lint + format check)"
    )
    parser.add_argument(
        "--tool",
        choices=["flake8", "pylint", "black", "isort", "all"],
        default="all",
        help="Tool(s) to use (default: all)"
    )
    parser.add_argument(
        "--path",
        default=".",
        help="Path to process (default: current directory)"
    )
    
    args = parser.parse_args()
    
    exit_code = 0
    
    if args.action in ["lint", "check"]:
        lint_tools = []
        if args.tool in ["flake8", "all"]:
            lint_tools.append("flake8")
        if args.tool in ["pylint", "all"]:
            lint_tools.append("pylint")
            
        for tool in lint_tools:
            print(f"Running {tool} on {args.path}...")
            code = check_linting(tool, args.path)
            if code != 0:
                exit_code = code
                print(f"{tool} failed with exit code {code}")
    
    if args.action in ["format", "check"]:
        format_tools = []
        if args.tool in ["black", "all"]:
            format_tools.append("black")
        if args.tool in ["isort", "all"]:
            format_tools.append("isort")
            
        for tool in format_tools:
            print(f"Running {tool} on {args.path}...")
            code = format_code(tool, args.path)
            if code != 0:
                exit_code = code
                print(f"{tool} failed with exit code {code}")
    
    if exit_code == 0:
        print("All checks passed!")
    else:
        print("Some checks failed. Please fix the issues above.")
        
    sys.exit(exit_code)


if __name__ == "__main__":
    main()