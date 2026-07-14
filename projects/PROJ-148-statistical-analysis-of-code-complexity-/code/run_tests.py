from __future__ import annotations

import sys
import subprocess
from pathlib import Path
from typing import Tuple

def run_tests_and_coverage(project_root: Path, min_coverage: float = 0.85) -> Tuple[bool, str, str]:
    """
    Runs the full test suite using pytest with coverage enforcement.
    
    Args:
        project_root: The root directory of the project.
        min_coverage: The minimum required coverage percentage (0.0 to 1.0).
    
    Returns:
        A tuple of (success, stdout, stderr).
        success is True if tests pass AND coverage >= min_coverage.
    """
    tests_dir = project_root / "tests"
    if not tests_dir.exists():
        return False, "", "Tests directory not found."

    # Construct the pytest command
    # --cov=code: Run coverage on the code directory
    # --cov-report=term-missing: Show missing lines in terminal
    # --cov-fail-under: Enforce the minimum coverage percentage
    # -v: Verbose output
    cmd = [
        sys.executable, "-m", "pytest",
        str(tests_dir),
        "--cov=code",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov",
        f"--cov-fail-under={min_coverage * 100}",
        "-v"
    ]

    try:
        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Test execution timed out."
    except Exception as e:
        return False, "", str(e)

def main() -> int:
    """Entry point for running tests and checking coverage."""
    project_root = Path(__file__).resolve().parent.parent
    
    print("Running full test suite with coverage enforcement (>= 85%)...")
    success, stdout, stderr = run_tests_and_coverage(project_root, min_coverage=0.85)
    
    print(stdout)
    if stderr:
        print(stderr, file=sys.stderr)
    
    if success:
        print("\n[SUCCESS] All tests passed and coverage requirement met.")
        return 0
    else:
        print("\n[FAILURE] Tests failed or coverage requirement not met.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
