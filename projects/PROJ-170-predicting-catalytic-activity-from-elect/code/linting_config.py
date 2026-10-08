"""
Linting and Formatting Configuration Module.

Provides functions to ensure linting configuration exists and to run
black and ruff checks/formats on the project.
"""
import os
import sys
import subprocess
from pathlib import Path
from config import get_project_root

def ensure_linting_config():
    """
    Ensure that pyproject.toml and .ruff.toml exist in the project root.
    
    Returns:
        bool: True if configs exist, False otherwise.
    """
    project_root = get_project_root()
    
    pyproject_path = project_root / "pyproject.toml"
    ruff_path = project_root / ".ruff.toml"
    
    if not pyproject_path.exists():
        print(f"Error: {pyproject_path} not found.")
        return False
        
    if not ruff_path.exists():
        print(f"Error: {ruff_path} not found.")
        return False
        
    return True

def run_black_check():
    """
    Run black check on the project.
    
    Returns:
        bool: True if formatting is correct, False otherwise.
    """
    try:
        result = subprocess.run(
            ["black", "--check", "."],
            cwd=get_project_root(),
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("Black check passed: Code is formatted correctly.")
            return True
        else:
            print("Black check failed:")
            print(result.stdout)
            print(result.stderr)
            return False
    except FileNotFoundError:
        print("Error: 'black' command not found. Please install it via pip.")
        return False

def run_ruff_check():
    """
    Run ruff check on the project using .ruff.toml config.
    
    Returns:
        bool: True if linting passes, False otherwise.
    """
    try:
        result = subprocess.run(
            ["ruff", "check", "--config=.ruff.toml", "."],
            cwd=get_project_root(),
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("Ruff check passed: No linting issues found.")
            return True
        else:
            print("Ruff check failed:")
            print(result.stdout)
            print(result.stderr)
            return False
    except FileNotFoundError:
        print("Error: 'ruff' command not found. Please install it via pip.")
        return False

def run_black_format():
    """
    Run black format on the project.
    
    Returns:
        bool: True if formatting was successful.
    """
    try:
        result = subprocess.run(
            ["black", "."],
            cwd=get_project_root(),
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("Black format completed successfully.")
            return True
        else:
            print("Black format failed:")
            print(result.stderr)
            return False
    except FileNotFoundError:
        print("Error: 'black' command not found. Please install it via pip.")
        return False

def run_ruff_fix():
    """
    Run ruff fix on the project using .ruff.toml config.
    
    Returns:
        bool: True if fixing was successful.
    """
    try:
        result = subprocess.run(
            ["ruff", "check", "--fix", "--config=.ruff.toml", "."],
            cwd=get_project_root(),
            capture_output=True,
            text=True
        )
        if result.returncode == 0 or result.returncode == 1:
            # Return code 1 means fixes were made
            print("Ruff fix completed.")
            return True
        else:
            print("Ruff fix failed:")
            print(result.stderr)
            return False
    except FileNotFoundError:
        print("Error: 'ruff' command not found. Please install it via pip.")
        return False

def main():
    """
    Main function to run linting and formatting checks.
    """
    print("Checking linting configuration...")
    if not ensure_linting_config():
        sys.exit(1)
        
    print("Running Black check...")
    black_ok = run_black_check()
    
    print("Running Ruff check...")
    ruff_ok = run_ruff_check()
    
    if black_ok and ruff_ok:
        print("\nAll checks passed successfully.")
        sys.exit(0)
    else:
        print("\nSome checks failed. Run 'black .' and 'ruff check --fix' to fix issues.")
        sys.exit(1)

if __name__ == "__main__":
    main()
