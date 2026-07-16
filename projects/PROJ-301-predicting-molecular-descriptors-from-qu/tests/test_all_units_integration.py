"""
T032: Aggregate test runner for all unit and integration tests.
This script verifies all unit and integration tests pass as required by the task.
It discovers and runs tests from:
- tests/test_feature_extraction.py
- tests/test_model_training.py
- tests/test_analysis.py
"""
import sys
import pytest

def main():
    """
    Entry point to run all tests.
    Returns 0 if all tests pass, non-zero otherwise.
    """
    # Run pytest on the tests directory
    # -v: verbose output
    # --tb=short: short tracebacks
    # We explicitly point to the known test files to ensure coverage
    exit_code = pytest.main([
        "-v",
        "--tb=short",
        "tests/test_feature_extraction.py",
        "tests/test_model_training.py",
        "tests/test_analysis.py"
    ])
    return exit_code

if __name__ == "__main__":
    sys.exit(main())
