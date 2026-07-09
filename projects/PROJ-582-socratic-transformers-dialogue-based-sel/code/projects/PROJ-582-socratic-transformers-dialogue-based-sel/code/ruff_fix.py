"""
Script to run ruff check and black --check, then fix any violations.
This implements task T034: Run `ruff check` and `black --check` on all `src/` and `tests/` files; fix any linting/formatting errors to achieve zero violations.
"""
import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, cwd=None):
    """Run a shell command and return the result."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    return result.returncode

def main():
    project_root = Path(__file__).parent
    src_dir = project_root / "src"
    tests_dir = project_root / "tests"

    if not src_dir.exists() or not tests_dir.exists():
        print(f"Error: Project directories not found at {project_root}")
        sys.exit(1)

    print(f"Checking code in {project_root}...")

    # Step 1: Run ruff check
    print("\n--- Running ruff check ---")
    ruff_check_code = run_command(["ruff", "check", str(src_dir), str(tests_dir)])

    # Step 2: Run black check
    print("\n--- Running black --check ---")
    black_check_code = run_command(["black", "--check", str(src_dir), str(tests_dir)])

    if ruff_check_code == 0 and black_check_code == 0:
        print("\n✅ All linting and formatting checks passed.")
        sys.exit(0)

    print("\n--- Found violations. Attempting to fix... ---")

    # Step 3: Fix with ruff
    print("\n--- Running ruff check --fix ---")
    ruff_fix_code = run_command(["ruff", "check", "--fix", str(src_dir), str(tests_dir)])

    # Step 4: Format with black
    print("\n--- Running black ---")
    black_format_code = run_command(["black", str(src_dir), str(tests_dir)])

    # Step 5: Re-check to ensure zero violations
    print("\n--- Re-running ruff check ---")
    ruff_check_code = run_command(["ruff", "check", str(src_dir), str(tests_dir)])

    print("\n--- Re-running black --check ---")
    black_check_code = run_command(["black", "--check", str(src_dir), str(tests_dir)])

    if ruff_check_code == 0 and black_check_code == 0:
        print("\n✅ All violations fixed. Zero linting/formatting errors remaining.")
        sys.exit(0)
    else:
        print("\n❌ Failed to fix all violations automatically.")
        if ruff_check_code != 0:
            print("   Remaining ruff errors detected.")
        if black_check_code != 0:
            print("   Remaining black formatting errors detected.")
        sys.exit(1)

if __name__ == "__main__":
    main()
