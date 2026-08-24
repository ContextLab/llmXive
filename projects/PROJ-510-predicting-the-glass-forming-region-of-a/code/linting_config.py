import os
import subprocess
import sys
from typing import List, Optional

def run_flake8(check_path: str = ".") -> int:
    """Run flake8 linter on the specified path."""
    cmd = [sys.executable, "-m", "flake8", check_path]
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except FileNotFoundError:
        print("Error: flake8 is not installed. Run: pip install flake8")
        return 1

def run_black(check_path: str = ".", fix: bool = False) -> int:
    """Run black formatter on the specified path."""
    cmd = [sys.executable, "-m", "black"]
    if not fix:
        cmd.append("--check")
    cmd.append(check_path)
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except FileNotFoundError:
        print("Error: black is not installed. Run: pip install black")
        return 1

def run_isort(check_path: str = ".", fix: bool = False) -> int:
    """Run isort import sorter on the specified path."""
    cmd = [sys.executable, "-m", "isort"]
    if not fix:
        cmd.append("--check-only")
    cmd.append(check_path)
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except FileNotFoundError:
        print("Error: isort is not installed. Run: pip install isort")
        return 1

def run_all_checks() -> int:
    """Run all linting and formatting checks."""
    exit_code = 0
    
    print("Running flake8...")
    if run_flake8() != 0:
        exit_code = 1
    
    print("Running black...")
    if run_black() != 0:
        exit_code = 1
    
    print("Running isort...")
    if run_isort() != 0:
        exit_code = 1
    
    return exit_code

def fix_all() -> int:
    """Automatically fix formatting issues with black and isort."""
    exit_code = 0

    print("Fixing with isort...")
    if run_isort(fix=True) != 0:
        exit_code = 1
    
    print("Fixing with black...")
    if run_black(fix=True) != 0:
        exit_code = 1
    
    if exit_code == 0:
        print("All formatting fixes applied.")
    else:
        print("Some fixes could not be applied automatically.")
    
    return exit_code

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--fix":
        sys.exit(fix_all())
    else:
        sys.exit(run_all_checks())
