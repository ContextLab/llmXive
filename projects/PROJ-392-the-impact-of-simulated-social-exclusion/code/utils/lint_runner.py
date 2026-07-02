"""
Utility module to run linters and formatters programmatically.
"""
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

def run_flake8(paths: List[str] = None) -> Tuple[int, str]:
    """
    Run flake8 on the specified paths.
    Returns (exit_code, output).
    """
    cmd = [sys.executable, "-m", "flake8"]
    if paths:
        cmd.extend(paths)
    else:
        cmd.append("code")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )
        return result.returncode, result.stdout + result.stderr
    except FileNotFoundError:
        return 1, "flake8 is not installed. Run 'python code/setup_linting.py' first."

def run_black(paths: List[str] = None, check_only: bool = False) -> Tuple[int, str]:
    """
    Run black on the specified paths.
    If check_only is True, only check formatting without modifying files.
    Returns (exit_code, output).
    """
    cmd = [sys.executable, "-m", "black"]
    if check_only:
        cmd.append("--check")
    if paths:
        cmd.extend(paths)
    else:
        cmd.append("code")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )
        return result.returncode, result.stdout + result.stderr
    except FileNotFoundError:
        return 1, "black is not installed. Run 'python code/setup_linting.py' first."

def run_isort(paths: List[str] = None, check_only: bool = False) -> Tuple[int, str]:
    """
    Run isort on the specified paths.
    If check_only is True, only check sorting without modifying files.
    Returns (exit_code, output).
    """
    cmd = [sys.executable, "-m", "isort"]
    if check_only:
        cmd.append("--check-only")
    if paths:
        cmd.extend(paths)
    else:
        cmd.append("code")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )
        return result.returncode, result.stdout + result.stderr
    except FileNotFoundError:
        return 1, "isort is not installed. Run 'python code/setup_linting.py' first."

def run_all_checks() -> bool:
    """
    Run all linters and formatters in check mode.
    Returns True if all checks pass, False otherwise.
    """
    print("Running flake8...")
    code, output = run_flake8()
    if code != 0:
        print("flake8 failed:")
        print(output)
        return False
    print("flake8 passed.")

    print("Running isort (check)...")
    code, output = run_isort(check_only=True)
    if code != 0:
        print("isort failed:")
        print(output)
        return False
    print("isort passed.")

    print("Running black (check)...")
    code, output = run_black(check_only=True)
    if code != 0:
        print("black failed:")
        print(output)
        return False
    print("black passed.")

    return True

def format_all() -> bool:
    """
    Run formatters to fix code.
    Returns True if formatting was successful.
    """
    print("Running isort...")
    code, output = run_isort()
    if code != 0:
        print("isort failed:")
        print(output)
        return False
    print("isort completed.")

    print("Running black...")
    code, output = run_black()
    if code != 0:
        print("black failed:")
        print(output)
        return False
    print("black completed.")

    return True

def main():
    """Main entry point for lint runner."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run linters and formatters")
    parser.add_argument("--check", action="store_true", help="Run checks only")
    parser.add_argument("--fix", action="store_true", help="Fix code formatting")
    parser.add_argument("--flake8-only", action="store_true", help="Run only flake8")
    parser.add_argument("--black-only", action="store_true", help="Run only black")
    parser.add_argument("--isort-only", action="store_true", help="Run only isort")
    parser.add_argument("paths", nargs="*", help="Paths to check/format (default: code/)")
    
    args = parser.parse_args()
    
    paths = args.paths if args.paths else None
    
    if args.check:
        success = run_all_checks()
        sys.exit(0 if success else 1)
    elif args.fix:
        success = format_all()
        sys.exit(0 if success else 1)
    elif args.flake8_only:
        code, output = run_flake8(paths)
        print(output)
        sys.exit(code)
    elif args.black_only:
        code, output = run_black(paths)
        print(output)
        sys.exit(code)
    elif args.isort_only:
        code, output = run_isort(paths)
        print(output)
        sys.exit(code)
    else:
        # Default: run checks
        success = run_all_checks()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()