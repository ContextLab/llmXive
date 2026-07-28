"""
T033: Code cleanup and refactoring script.

This script automates the execution of `ruff check` and `black --check`
on the `code/` and `tests/` directories. If violations are found, it
attempts to automatically fix them using `ruff --fix` and `black`.

It reports the final status to ensure the task requirement (exit code 0)
is met before marking the task complete.
"""
import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description):
    """Run a shell command and report status."""
    print(f"--- {description} ---")
    print(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            check=False
        )
        
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        
        if result.returncode != 0:
            print(f"❌ {description} failed with exit code {result.returncode}")
            return False
        else:
            print(f"✅ {description} passed")
            return True
            
    except FileNotFoundError:
        print(f"❌ Error: Command not found. Is it installed? {cmd[0]}")
        return False
    except Exception as e:
        print(f"❌ Error running command: {e}")
        return False

def main():
    project_root = Path(__file__).parent.parent
    code_dir = project_root / "code"
    tests_dir = project_root / "tests"
    
    if not code_dir.exists() or not tests_dir.exists():
        print("❌ Error: 'code' or 'tests' directory not found in project root.")
        sys.exit(1)

    print("Starting T033: Code Cleanup and Refactoring...")
    
    # Step 1: Attempt automatic fixes first
    print("\n1. Attempting automatic fixes...")
    
    # Fix with Ruff
    ruff_fix_cmd = [
        sys.executable, "-m", "ruff", "check", 
        str(code_dir), str(tests_dir), 
        "--fix"
    ]
    run_command(ruff_fix_cmd, "Ruff Fix")
    
    # Fix with Black
    black_fix_cmd = [
        sys.executable, "-m", "black", 
        str(code_dir), str(tests_dir)
    ]
    run_command(black_fix_cmd, "Black Fix")
    
    # Step 2: Verify clean state
    print("\n2. Verifying clean state...")
    
    ruff_check_cmd = [
        sys.executable, "-m", "ruff", "check", 
        str(code_dir), str(tests_dir)
    ]
    ruff_ok = run_command(ruff_check_cmd, "Ruff Check")
    
    black_check_cmd = [
        sys.executable, "-m", "black", "--check", 
        str(code_dir), str(tests_dir)
    ]
    black_ok = run_command(black_check_cmd, "Black Check")
    
    if ruff_ok and black_ok:
        print("\n✅ T033 COMPLETED: All linting and formatting checks passed.")
        sys.exit(0)
    else:
        print("\n❌ T033 FAILED: Linting or formatting issues remain.")
        print("Please manually resolve any remaining errors reported above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
