"""
Task T039: Run pytest suite to ensure all unit and integration tests pass.

This module provides a wrapper script to execute the full test suite.
It verifies that all unit and integration tests defined in the project pass.
"""
import subprocess
import sys
import os

def run_test_suite():
    """
    Executes the pytest suite against the project's test directory.
    
    Returns:
        int: 0 if all tests pass, 1 otherwise.
    """
    # Determine the project root (assuming this file is in tests/ or code/tests/)
    # Based on path conventions: tests/ at repository root
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    test_dir = os.path.join(project_root, "tests")
    
    if not os.path.exists(test_dir):
        print(f"Error: Test directory not found at {test_dir}")
        return 1
    
    # Construct the pytest command
    # -v: verbose output
    # --tb=short: short traceback format
    # --strict-markers: treat unknown markers as errors (good practice)
    # -x: stop on first failure (optional, but good for CI)
    # We remove -x to ensure all tests run and we see the full report
    cmd = [
        sys.executable, "-m", "pytest",
        test_dir,
        "-v",
        "--tb=short",
        "--strict-markers"
    ]
    
    print(f"Running test suite in: {test_dir}")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 60)
    
    try:
        result = subprocess.run(
            cmd,
            cwd=project_root,
            stdout=sys.stdout,
            stderr=sys.stderr,
            check=False
        )
        
        if result.returncode == 0:
            print("-" * 60)
            print("SUCCESS: All tests passed.")
            return 0
        else:
            print("-" * 60)
            print(f"FAILURE: Tests failed with exit code {result.returncode}")
            return 1
            
    except FileNotFoundError:
        print("Error: pytest not found. Please install it via 'pip install pytest'.")
        return 1
    except Exception as e:
        print(f"Error running test suite: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(run_test_suite())