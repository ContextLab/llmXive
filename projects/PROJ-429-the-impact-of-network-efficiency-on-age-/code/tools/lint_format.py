"""
Linting and Formatting Tools for the llmXive Pipeline.

This module provides command-line utilities to run ruff (linting) and black (formatting)
on the project codebase. It ensures consistent code style and catches common errors.

Usage:
    python code/tools/lint_format.py --lint
    python code/tools/lint_format.py --format
    python code/tools/lint_format.py --all
"""
import argparse
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], description: str) -> bool:
    """Run a shell command and report status."""
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            check=False,
            capture_output=False,
            text=True
        )
        if result.returncode == 0:
            print(f"✓ {description} passed.")
            return True
        else:
            print(f"✗ {description} failed.")
            return False
    except FileNotFoundError:
        print(f"✗ {description} command not found. Please ensure tools are installed.")
        return False
    except Exception as e:
        print(f"✗ {description} error: {e}")
        return False


def check_dependencies() -> bool:
    """Check if ruff and black are installed."""
    print("Checking dependencies...")
    missing = []
    
    try:
        subprocess.run(["ruff", "--version"], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        missing.append("ruff")
    except FileNotFoundError:
        missing.append("ruff")
        
    try:
        subprocess.run(["black", "--version"], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        missing.append("black")
    except FileNotFoundError:
        missing.append("black")
        
    if missing:
        print(f"Missing tools: {', '.join(missing)}")
        print("Install them via: pip install ruff black")
        return False
        
    print("All dependencies found.")
    return True


def run_lint() -> bool:
    """Run ruff linter on the code directory."""
    code_dir = Path(__file__).parent.parent
    cmd = ["ruff", "check", str(code_dir), "--config", "pyproject.toml"]
    return run_command(cmd, "Linting (ruff)")


def run_format() -> bool:
    """Run black formatter on the code directory."""
    code_dir = Path(__file__).parent.parent
    cmd = ["black", str(code_dir), "--config", "pyproject.toml"]
    return run_command(cmd, "Formatting (black)")


def main():
    parser = argparse.ArgumentParser(description="Run linting and formatting tools.")
    parser.add_argument(
        "--lint",
        action="store_true",
        help="Run linting only."
    )
    parser.add_argument(
        "--format",
        action="store_true",
        help="Run formatting only."
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run both linting and formatting."
    )
    
    args = parser.parse_args()
    
    if not (args.lint or args.format or args.all):
        parser.print_help()
        sys.exit(1)
        
    if not check_dependencies():
        sys.exit(1)
        
    success = True
    
    if args.lint or args.all:
        if not run_lint():
            success = False
            
    if args.format or args.all:
        if not run_format():
            success = False
            
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
