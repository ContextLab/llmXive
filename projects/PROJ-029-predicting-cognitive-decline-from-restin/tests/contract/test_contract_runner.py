"""
Contract Test Runner.
This module aggregates contract tests and provides a simple entry point
to run all schema validations.
"""
import pytest
import sys
from pathlib import Path

# Add the tests directory to the path if running as a script
# This ensures relative imports work if necessary
if __name__ == "__main__":
    # Run all contract tests
    # In a CI environment, pytest would be invoked directly
    # This script serves as a convenient wrapper
    exit_code = pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-k", "contract"
    ])
    sys.exit(exit_code)