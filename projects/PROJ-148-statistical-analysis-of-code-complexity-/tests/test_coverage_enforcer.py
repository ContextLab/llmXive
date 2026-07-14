"""
Test and enforcement script for T039: Run full test suite and enforce coverage >= 85%.

This module provides a function to run the test suite with coverage and assert
that the coverage meets the 85% threshold. It also serves as the entry point
for the task implementation.
"""
import subprocess
import sys
from pathlib import Path

import pytest


def run_tests_with_coverage(coverage_threshold: float = 0.85) -> bool:
    """
    Runs the pytest suite with coverage measurement and enforces the threshold.

    Args:
        coverage_threshold: Minimum required coverage ratio (default 0.85).

    Returns:
        True if coverage >= threshold and tests pass, False otherwise.
    """
    project_root = Path(__file__).resolve().parent.parent
    tests_dir = project_root / "tests"
    code_dir = project_root / "code"

    # Build the pytest command
    # -v: verbose
    # --cov: measure coverage for the 'code' directory
    # --cov-report=term-missing: show missing lines in terminal
    # --cov-fail-under: enforce threshold (pytest-cov feature)
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        str(tests_dir),
        "-v",
        "--cov=code",
        "--cov-report=term-missing",
        f"--cov-fail-under={int(coverage_threshold * 100)}",
    ]

    print(f"Running test suite with coverage enforcement (threshold: {coverage_threshold*100}%)...")
    print(f"Command: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            cwd=project_root,
            check=True,
            capture_output=False,
            text=True,
        )
        return True
    except subprocess.CalledProcessError as e:
        # If pytest fails due to coverage threshold or test failure, it returns non-zero
        print(f"\nTest suite failed or coverage threshold not met.")
        print(f"Return code: {e.returncode}")
        return False


def main() -> int:
    """Entry point for the task script."""
    success = run_tests_with_coverage(coverage_threshold=0.85)
    if success:
        print("\n✅ All tests passed and coverage >= 85% enforced.")
        return 0
    else:
        print("\n❌ Test suite failed or coverage < 85%.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
