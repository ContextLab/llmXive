"""
Runner script to execute prevalence unit tests and verify CI width constraint.
This script ensures that tests pass and the CI width constraint (<= 0.10) is met.
"""
import sys
import pytest
from pathlib import Path

# Add the code directory to the path
code_dir = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

def main():
    """Run prevalence unit tests."""
    test_file = Path(__file__).parent / "test_prevalence.py"

    if not test_file.exists():
        print(f"ERROR: Test file not found: {test_file}")
        return 1

    # Run pytest with verbose output
    exit_code = pytest.main([
        str(test_file),
        "-v",
        "--tb=short"
    ])

    if exit_code == 0:
        print("SUCCESS: All prevalence tests passed, including CI width constraint.")
    else:
        print(f"FAILURE: {exit_code} test(s) failed.")

    return exit_code

if __name__ == "__main__":
    sys.exit(main())