"""
Main entry point for running tests.

Usage:
    python -m tests
"""
import pytest
import sys
import os

def main():
    """Run all tests in the tests directory."""
    # Get the directory containing this file
    test_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(test_dir)
    
    # Add project root to path
    sys.path.insert(0, project_root)
    
    # Run pytest with verbose output
    exit_code = pytest.main([
        test_dir,
        "-v",
        "--tb=short",
        "--strict-markers"
    ])
    
    return exit_code

if __name__ == "__main__":
    sys.exit(main())