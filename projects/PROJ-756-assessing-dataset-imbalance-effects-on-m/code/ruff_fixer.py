"""
T044a: Ruff Linting Fixer Script.

This script runs 'ruff check' on all Python files in the 'code/' directory.
If errors are found, it attempts to auto-fix them using 'ruff check --fix'.
It reports the final status and ensures the codebase is clean or explains why it cannot be fixed automatically.

Usage:
    python code/ruff_fixer.py
"""
import os
import sys
import subprocess
from pathlib import Path

def run_command(cmd: list[str], check: bool = False) -> tuple[int, str, str]:
    """Run a shell command and return (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            cwd=Path(__file__).parent.parent
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return -1, "", str(e)

def main():
    project_root = Path(__file__).parent.parent
    code_dir = project_root / "code"

    if not code_dir.exists():
        print(f"Error: Directory '{code_dir}' does not exist.")
        sys.exit(1)

    print("=== T044a: Running Ruff Linting ===")
    print(f"Target directory: {code_dir}")

    # Step 1: Check for ruff installation
    rc, stdout, stderr = run_command(["ruff", "--version"])
    if rc != 0:
        print("Error: 'ruff' is not installed or not in PATH.")
        print("Please install it via: pip install ruff")
        sys.exit(1)
    
    print(f"Ruff version: {stdout.strip()}")

    # Step 2: Initial Check
    print("\n--- Initial Check ---")
    cmd_check = ["ruff", "check", str(code_dir)]
    rc, stdout, stderr = run_command(cmd_check)

    if rc == 0:
        print("✅ No linting errors found. Code is clean.")
        sys.exit(0)

    print("❌ Linting errors found. Attempting auto-fix...")
    print(stdout)

    # Step 3: Attempt Auto-Fix
    print("\n--- Attempting Auto-Fix ---")
    cmd_fix = ["ruff", "check", "--fix", str(code_dir)]
    rc_fix, stdout_fix, stderr_fix = run_command(cmd_fix)

    if rc_fix != 0:
        print("⚠️  Auto-fix encountered issues or returned non-zero exit code.")
        if stderr_fix:
            print(f"Error output: {stderr_fix}")
        # Even if rc_fix != 0, ruff might have fixed some. Let's check again.

    # Step 4: Final Verification
    print("\n--- Final Verification ---")
    rc_final, stdout_final, stderr_final = run_command(cmd_check)

    if rc_final == 0:
        print("✅ All linting errors have been fixed successfully.")
        sys.exit(0)
    else:
        print("❌ Linting errors remain after auto-fix. Manual intervention required.")
        print("Remaining issues:")
        print(stdout_final)
        
        # Analyze specific remaining issues to provide better feedback
        if "I001" in stdout_final:
            print("\nNote: I001 (import sorting) often requires manual review if auto-sort breaks logic.")
        if "F" in stdout_final or "E" in stdout_final:
            print("\nNote: F (Pyflakes) and E (Pycodestyle) errors often require logic changes.")
        
        sys.exit(1)

if __name__ == "__main__":
    main()