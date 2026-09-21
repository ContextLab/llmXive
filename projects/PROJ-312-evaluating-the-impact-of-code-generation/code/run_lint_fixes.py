import subprocess
import sys
import os
from pathlib import Path

def main():
    """
    Run ruff --fix on the codebase to ensure zero linting errors.
    This script executes ruff on the 'code/' directory relative to the project root.
    """
    project_root = Path(__file__).resolve().parent.parent
    code_dir = project_root / "code"

    if not code_dir.exists():
        print(f"Error: Code directory not found at {code_dir}")
        sys.exit(1)

    print(f"Running ruff check --fix on {code_dir}...")
    
    # Run ruff check with --fix to automatically fix issues
    result = subprocess.run(
        ["ruff", "check", "--fix", str(code_dir)],
        cwd=project_root,
        capture_output=False,
        text=True
    )

    if result.returncode != 0:
        # If ruff returns non-zero after --fix, there are remaining errors
        print("\nRuff found remaining linting errors that could not be auto-fixed.")
        print("Please fix them manually or check ruff configuration.")
        sys.exit(1)
    
    print("\nRuff check passed: No linting errors remaining.")

    # Run ruff format check to ensure formatting is correct (as per T039b context)
    # Although T039a is specifically --fix, ensuring format compliance is good practice
    print("Running ruff format check...")
    result_format = subprocess.run(
        ["ruff", "format", "--check", str(code_dir)],
        cwd=project_root,
        capture_output=False,
        text=True
    )

    if result_format.returncode != 0:
        print("\nRuff format check failed. Run 'ruff format' to fix formatting.")
        # We do not exit here for T039a specifically, as T039a is about --fix (linting),
        # but we log the status. T039b would handle the strict check.
    
    return 0

if __name__ == "__main__":
    sys.exit(main())