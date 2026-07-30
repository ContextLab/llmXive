"""
T038: Run pytest suite to ensure all unit and integration tests pass.

This script discovers and runs the full test suite defined in the project.
It serves as the executable entry point for the verification task.
"""
import sys
import subprocess
import argparse
from pathlib import Path

def run_pytest_suite(verbosity: int = 2, fail_fast: bool = False) -> int:
    """
    Execute the pytest suite against the project's test directory.

    Args:
        verbosity: Pytest verbosity level (-v count).
        fail_fast: If True, stop after the first failure.

    Returns:
        Exit code: 0 for success, non-zero for failure.
    """
    project_root = Path(__file__).parent.parent
    test_dir = project_root / "tests"

    if not test_dir.exists():
        print(f"Error: Test directory not found at {test_dir}")
        return 1

    cmd = [
        sys.executable, "-m", "pytest",
        str(test_dir),
        "-v",
        "--tb=short",
        "--color=yes"
    ]

    if fail_fast:
        cmd.append("-x")

    if verbosity > 2:
        cmd.extend(["-" + "v" * (verbosity - 1)])
    elif verbosity == 1:
        cmd.append("-q")
    elif verbosity == 0:
        cmd.append("-q")
        cmd.append("--disable-warnings")

    print(f"Running command: {' '.join(cmd)}")
    print(f"Working directory: {project_root}")

    try:
        result = subprocess.run(
            cmd,
            cwd=project_root,
            text=True,
            check=False  # We handle the return code explicitly
        )
        return result.returncode
    except FileNotFoundError:
        print("Error: pytest not found. Ensure 'pytest' is installed.")
        return 1
    except KeyboardInterrupt:
        print("\nTest suite interrupted.")
        return 130

def main():
    parser = argparse.ArgumentParser(
        description="Run the full pytest suite for the project."
    )
    parser.add_argument(
        "-v", "--verbose",
        type=int,
        default=2,
        help="Verbosity level (0=quiet, 1=normal, 2=verbose, 3=very verbose)"
    )
    parser.add_argument(
        "-x", "--fail-fast",
        action="store_true",
        help="Stop running tests after the first failure."
    )

    args = parser.parse_args()

    exit_code = run_pytest_suite(
        verbosity=args.verbose,
        fail_fast=args.fail_fast
    )

    if exit_code == 0:
        print("\n" + "="*60)
        print("SUCCESS: All tests passed.")
        print("="*60)
    else:
        print("\n" + "="*60)
        print(f"FAILURE: Tests failed with exit code {exit_code}")
        print("="*60)

    sys.exit(exit_code)

if __name__ == "__main__":
    main()