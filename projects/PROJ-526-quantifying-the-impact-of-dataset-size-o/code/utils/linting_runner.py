"""
Utility module to run linting and formatting checks.
This module executes black and flake8 against the project codebase.
"""
import subprocess
import sys
from pathlib import Path
from typing import Tuple, Optional
from code.linting_config import get_black_config, get_flake8_config


def run_black_check(project_root: Optional[Path] = None) -> Tuple[bool, str]:
    """
    Run black check in 'check' mode (no write) on the project.
    
    Args:
        project_root: Path to the project root. Defaults to current working directory.
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    if project_root is None:
        project_root = Path.cwd()
        
    black_config = get_black_config()
    code_dir = project_root / "code"
    tests_dir = project_root / "tests"
    
    if not code_dir.exists() or not tests_dir.exists():
        return False, "Code or tests directory not found."

    cmd = [
        sys.executable, "-m", "black",
        "--config", str(project_root / "pyproject.toml"),
        "--check",
        "--diff",
        str(code_dir),
        str(tests_dir)
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            return True, "All files are formatted correctly with Black."
        else:
            return False, f"Black check failed:\n{result.stdout}\n{result.stderr}"
            
    except FileNotFoundError:
        return False, "Black is not installed. Please run: pip install black"
    except Exception as e:
        return False, f"Error running Black: {str(e)}"


def run_flake8_check(project_root: Optional[Path] = None) -> Tuple[bool, str]:
    """
    Run flake8 check on the project.
    
    Args:
        project_root: Path to the project root. Defaults to current working directory.
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    if project_root is None:
        project_root = Path.cwd()
        
    flake8_config = get_flake8_config()
    code_dir = project_root / "code"
    tests_dir = project_root / "tests"
    
    if not code_dir.exists() or not tests_dir.exists():
        return False, "Code or tests directory not found."

    cmd = [
        sys.executable, "-m", "flake8",
        "--config", str(project_root / ".flake8"),
        str(code_dir),
        str(tests_dir)
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            return True, "All files pass flake8 linting."
        else:
            return False, f"Flake8 check failed:\n{result.stdout}\n{result.stderr}"
            
    except FileNotFoundError:
        return False, "Flake8 is not installed. Please run: pip install flake8"
    except Exception as e:
        return False, f"Error running Flake8: {str(e)}"


def main() -> int:
    """
    Main entry point to run all linting checks.
    Returns 0 if all checks pass, 1 otherwise.
    """
    project_root = Path.cwd()
    
    print("Running linting checks...")
    print("-" * 40)
    
    # Run Black
    black_success, black_msg = run_black_check(project_root)
    if black_success:
        print(f"[PASS] Black: {black_msg}")
    else:
        print(f"[FAIL] Black: {black_msg}")
        
    # Run Flake8
    flake8_success, flake8_msg = run_flake8_check(project_root)
    if flake8_success:
        print(f"[PASS] Flake8: {flake8_msg}")
    else:
        print(f"[FAIL] Flake8: {flake8_msg}")
        
    print("-" * 40)
    
    if black_success and flake8_success:
        print("All linting checks passed!")
        return 0
    else:
        print("One or more linting checks failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
