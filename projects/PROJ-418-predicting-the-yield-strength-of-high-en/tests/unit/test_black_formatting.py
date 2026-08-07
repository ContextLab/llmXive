"""
Test task T124: Verify that the final codebase passes `black --check`.

This script executes `black --check` on the `code/` directory.
It asserts that no formatting changes are needed (exit code 0).
If the check fails, it prints the output and raises an AssertionError
to cause the pipeline to fail, ensuring strict formatting compliance.
"""
import subprocess
import sys
import os
from pathlib import Path

def run_black_check():
    """Run black --check on the code directory and assert success."""
    project_root = Path(__file__).parent.parent.parent
    code_dir = project_root / "code"
    
    if not code_dir.exists():
        raise FileNotFoundError(f"Code directory not found at {code_dir}")

    # Run black check
    # Using --check to ensure no changes are needed (exit code 0)
    # Using --quiet to reduce noise, though we capture output for error reporting
    result = subprocess.run(
        [sys.executable, "-m", "black", "--check", "--quiet", str(code_dir)],
        cwd=project_root,
        capture_output=True,
        text=True
    )

    # If exit code is 0, formatting is correct
    if result.returncode == 0:
        print("SUCCESS: All Python files in code/ are formatted correctly according to Black.")
        return True
    
    # If exit code is non-zero, formatting issues exist
    error_msg = (
        f"FAILURE: Black formatting check failed.\n"
        f"Return code: {result.returncode}\n"
        f"Stdout:\n{result.stdout}\n"
        f"Stderr:\n{result.stderr}\n"
        f"Please run `black code/` to fix formatting issues."
    )
    print(error_msg)
    raise AssertionError(error_msg)

def main():
    """Entry point for the test script."""
    try:
        run_black_check()
        print("Task T124 verification passed.")
        sys.exit(0)
    except AssertionError as e:
        print(f"Task T124 verification failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error during T124 verification: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()