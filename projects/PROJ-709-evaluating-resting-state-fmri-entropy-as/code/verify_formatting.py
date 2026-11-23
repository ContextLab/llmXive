"""
Verification script for code formatting standards (black and isort).
Runs checks to ensure code/ and tests/ directories comply with formatting rules.
"""
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], description: str) -> bool:
    """
    Run a command and return True if it succeeds (exit code 0), False otherwise.
    Prints the command output for debugging.
    """
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            cwd=Path(__file__).parent.parent
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        
        if result.returncode == 0:
            print(f"✓ {description} passed.")
            return True
        else:
            print(f"✗ {description} failed with exit code {result.returncode}")
            return False
    except Exception as e:
        print(f"✗ {description} failed with exception: {e}")
        return False


def main() -> int:
    """
    Main entry point for formatting verification.
    Runs black --check and isort --check-only on code/ and tests/.
    Returns 0 if all checks pass, 1 otherwise.
    """
    project_root = Path(__file__).parent.parent
    code_dir = project_root / "code"
    tests_dir = project_root / "tests"

    if not code_dir.exists():
        print(f"Error: Directory {code_dir} does not exist.")
        return 1
    if not tests_dir.exists():
        print(f"Error: Directory {tests_dir} does not exist.")
        return 1

    all_passed = True

    # Run black --check
    black_cmd = [
        sys.executable, "-m", "black",
        "--check",
        "--quiet",
        str(code_dir),
        str(tests_dir)
    ]
    if not run_command(black_cmd, "black --check"):
        all_passed = False

    # Run isort --check-only
    isort_cmd = [
        sys.executable, "-m", "isort",
        "--check-only",
        "--quiet",
        str(code_dir),
        str(tests_dir)
    ]
    if not run_command(isort_cmd, "isort --check-only"):
        all_passed = False

    if all_passed:
        print("\n✓ All formatting checks passed.")
        return 0
    else:
        print("\n✗ Some formatting checks failed. Please run 'python code/format_code_runner.py' to fix.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
