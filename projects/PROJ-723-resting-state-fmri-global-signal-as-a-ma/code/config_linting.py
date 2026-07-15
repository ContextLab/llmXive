"""
Linting and formatting configuration helpers.
Wraps ruff and black commands.
"""
import subprocess
import sys
from pathlib import Path

def run_ruff_check(path: str = ".") -> int:
    """Run ruff check on the given path."""
    try:
        result = subprocess.run(
            ["ruff", "check", path],
            capture_output=True,
            text=True,
            check=False
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return result.returncode
    except FileNotFoundError:
        print("Error: 'ruff' not found. Please install it via 'pip install ruff'.")
        return 1

def run_ruff_fix(path: str = ".") -> int:
    """Run ruff check with fix option."""
    try:
        result = subprocess.run(
            ["ruff", "check", "--fix", path],
            capture_output=True,
            text=True,
            check=False
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return result.returncode
    except FileNotFoundError:
        print("Error: 'ruff' not found.")
        return 1

def run_black_check(path: str = ".") -> int:
    """Run black check on the given path."""
    try:
        result = subprocess.run(
            ["black", "--check", path],
            capture_output=True,
            text=True,
            check=False
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return result.returncode
    except FileNotFoundError:
        print("Error: 'black' not found. Please install it via 'pip install black'.")
        return 1

def run_black_format(path: str = ".") -> int:
    """Run black format on the given path."""
    try:
        result = subprocess.run(
            ["black", path],
            capture_output=True,
            text=True,
            check=False
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return result.returncode
    except FileNotFoundError:
        print("Error: 'black' not found.")
        return 1

def run_lint_and_format(path: str = ".") -> bool:
    """Run both linter and formatter, fixing issues where possible."""
    print("Running ruff fix...")
    ruff_code = run_ruff_fix(path)
    
    print("Running black format...")
    black_code = run_black_format(path)
    
    return ruff_code == 0 and black_code == 0
