import subprocess
import sys
from pathlib import Path

def run_flake8_check() -> bool:
    """
    Run flake8 on the project root.
    
    Returns:
        True if linting passes (exit code 0), False otherwise.
    """
    try:
        result = subprocess.run(
            [sys.executable, "-m", "flake8", "code", "tests"],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode != 0:
            print("Flake8 found issues:")
            print(result.stdout)
            print(result.stderr)
            return False
        print("Flake8 check passed.")
        return True
    except FileNotFoundError:
        print("Error: flake8 not found. Please install it via pip.")
        return False
    except Exception as e:
        print(f"Error running flake8: {e}")
        return False

def run_black_format(check_only: bool = True) -> bool:
    """
    Run black on the project root.
    
    Args:
        check_only: If True, only check formatting (no writes). 
                    If False, format files in place.
    
    Returns:
        True if formatting is correct (or applied successfully), False otherwise.
    """
    try:
        cmd = [sys.executable, "-m", "black", "--check"] if check_only else [sys.executable, "-m", "black"]
        result = subprocess.run(
            cmd + ["code", "tests"],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode != 0:
            if check_only:
                print("Black formatting check failed. Run with check_only=False to fix.")
                print(result.stdout)
                print(result.stderr)
            else:
                print("Black formatting applied.")
                print(result.stdout)
            return False if check_only else True
        print("Black formatting check passed.")
        return True
    except FileNotFoundError:
        print("Error: black not found. Please install it via pip.")
        return False
    except Exception as e:
        print(f"Error running black: {e}")
        return False

def run_all_checks(fix: bool = False) -> bool:
    """
    Run all linting and formatting checks.
    
    Args:
        fix: If True, run black in fix mode. Does not fix flake8 errors automatically.
    
    Returns:
        True if all checks pass, False otherwise.
    """
    print("Running linting and formatting checks...")
    
    flake8_ok = run_flake8_check()
    black_ok = run_black_format(check_only=not fix)
    
    if not fix and not black_ok:
        print("\nHint: Run with --fix to automatically format code with black.")
    
    all_ok = flake8_ok and black_ok
    if all_ok:
        print("\nAll checks passed!")
    else:
        print("\nSome checks failed.")
    
    return all_ok
