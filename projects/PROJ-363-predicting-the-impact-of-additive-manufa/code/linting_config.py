"""
Configuration and execution logic for linting (ruff/flake8) and formatting (black).
"""
import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd: list[str], description: str) -> bool:
    """
    Execute a shell command and print output.
    Returns True if successful, False otherwise.
    """
    print(f"Running: {description}...")
    try:
        result = subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=Path(__file__).parent
        )
        if result.stdout:
            print(result.stdout)
        print(f"✅ {description} completed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed with code {e.returncode}.")
        if e.stdout:
            print(e.stdout)
        return False
    except FileNotFoundError:
        print(f"❌ Command not found. Please ensure {' '.join(cmd[:2])} is installed.")
        return False

def check_linting() -> bool:
    """
    Run linters (ruff check and flake8) without fixing.
    Returns True if no issues found.
    """
    success = True
    # Try ruff first
    if run_command(["ruff", "check", "."], "Ruff Check"):
        pass
    else:
        # Fallback to flake8 if ruff not found or fails configuration
        if not run_command(["flake8", "."], "Flake8 Check"):
            success = False
    return success

def check_formatting() -> bool:
    """
    Run formatter (black) in check mode.
    Returns True if formatting is correct.
    """
    return run_command(["black", "--check", "."], "Black Check")

def fix_linting() -> bool:
    """
    Run linters with auto-fix enabled (ruff fix).
    """
    # Ruff can fix some issues automatically
    return run_command(["ruff", "check", ".", "--fix"], "Ruff Fix")

def fix_formatting() -> bool:
    """
    Run formatter (black) to fix formatting issues.
    """
    return run_command(["black", "."], "Black Format")

def main():
    """
    Main entry point for linting and formatting tasks.
    Usage:
      python code/linting_config.py check   -> Check only
      python code/linting_config.py fix     -> Fix issues
    """
    if len(sys.argv) < 2:
        print("Usage: python code/linting_config.py [check|fix]")
        sys.exit(1)

    mode = sys.argv[1].lower()

    if mode == "check":
        lint_ok = check_linting()
        fmt_ok = check_formatting()
        if lint_ok and fmt_ok:
            print("\n🎉 All checks passed!")
            sys.exit(0)
        else:
            print("\n⚠️ Issues found. Run 'python code/linting_config.py fix' to attempt auto-fixes.")
            sys.exit(1)
    elif mode == "fix":
        print("Attempting to fix issues...")
        fix_linting()
        fix_formatting()
        print("\nFixes applied. Please run 'check' again to verify.")
    else:
        print(f"Unknown mode: {mode}")
        sys.exit(1)

if __name__ == "__main__":
    main()