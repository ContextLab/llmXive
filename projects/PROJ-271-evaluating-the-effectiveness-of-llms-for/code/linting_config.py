import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CODE_DIR = PROJECT_ROOT / "code"

def run_flake8_check() -> bool:
    """
    Run flake8 linter on the code directory.
    
    Returns:
        True if checks pass, False if issues found or error occurs.
    """
    try:
        result = subprocess.run(
            [sys.executable, "-m", "flake8", str(CODE_DIR)],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print("Flake8 found issues:")
            print(result.stdout)
            print(result.stderr)
            return False
        print("Flake8 check passed.")
        return True
    except FileNotFoundError:
        print("Error: flake8 not found. Please install it: pip install flake8")
        return False
    except Exception as e:
        print(f"Error running flake8: {e}")
        return False

def run_black_format(check_only: bool = True) -> bool:
    """
    Run black formatter on the code directory.
    
    Args:
        check_only: If True, only check formatting without modifying files.
                   If False, reformat files in place.
    
    Returns:
        True if formatting is correct (or fixed), False if errors occur.
    """
    try:
        cmd = [sys.executable, "-m", "black"]
        if check_only:
            cmd.append("--check")
        cmd.append(str(CODE_DIR))
        
        result = subprocess.run(
            cmd,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            if check_only:
                print("Black formatting check failed. Run 'python -m black code' to fix.")
                print(result.stdout)
                print(result.stderr)
            else:
                print("Black formatting applied.")
                print(result.stdout)
            return False
        
        if check_only:
            print("Black formatting check passed.")
        else:
            print("Black formatting applied successfully.")
        return True
    except FileNotFoundError:
        print("Error: black not found. Please install it: pip install black")
        return False
    except Exception as e:
        print(f"Error running black: {e}")
        return False

def run_all_checks(fix: bool = False) -> bool:
    """
    Run all linting and formatting checks.
    
    Args:
        fix: If True, attempt to fix formatting issues with black.
            If False, only check for issues.
    
    Returns:
        True if all checks pass (or fixes applied), False otherwise.
    """
    print("Running linting and formatting checks...")
    print("-" * 50)
    
    flake8_ok = run_flake8_check()
    print("-" * 50)
    
    black_ok = run_black_format(check_only=not fix)
    print("-" * 50)
    
    if flake8_ok and black_ok:
        print("All checks passed!")
        return True
    
    if fix and not black_ok:
        print("Attempting to fix formatting issues...")
        run_black_format(check_only=False)
        # Re-check after fixing
        black_ok = run_black_format(check_only=True)
    
    if flake8_ok and black_ok:
        print("All checks passed after fixes!")
        return True
    
    print("Some checks failed. Please review the output above.")
    return False

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run linting and formatting checks")
    parser.add_argument("--fix", action="store_true", help="Attempt to fix formatting issues")
    args = parser.parse_args()
    
    success = run_all_checks(fix=args.fix)
    sys.exit(0 if success else 1)
