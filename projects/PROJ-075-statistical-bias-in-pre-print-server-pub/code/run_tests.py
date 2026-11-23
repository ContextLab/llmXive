import subprocess
import sys
import os
from pathlib import Path

def run_pytest():
    """
    Executes the full pytest suite on the project's test directory.
    Ensures all tests pass. If any test fails, raises a RuntimeError
    with the failure output.
    """
    project_root = Path(__file__).parent.parent
    tests_dir = project_root / "tests"
    
    if not tests_dir.exists():
        raise RuntimeError(f"Tests directory not found at {tests_dir}")

    # Construct the pytest command
    # -v: verbose output
    # --tb=short: short traceback format
    # --color=yes: ensure color output for readability
    cmd = [
        sys.executable, "-m", "pytest",
        str(tests_dir),
        "-v",
        "--tb=short",
        "--color=yes"
    ]

    print(f"Running pytest from {project_root}...")
    print(f"Command: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=False, # Stream output to console for immediate feedback
            text=True
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"Pytest failed with return code {result.returncode}. "
                "See output above for details."
            )
        
        print("\n✅ All tests passed successfully.")
        return True

    except FileNotFoundError:
        raise RuntimeError("Pytest executable not found. Ensure pytest is installed.")
    except Exception as e:
        raise RuntimeError(f"Error running test suite: {str(e)}")

if __name__ == "__main__":
    run_pytest()
