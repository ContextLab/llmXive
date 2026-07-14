"""
T039: Run pytest suite to ensure all unit and integration tests pass.

This script executes the full test suite for the llmXive project.
It serves as the entry point for the verification task.
"""
import sys
import subprocess
import os

def main():
    """Execute pytest with standard flags for the project."""
    # Ensure we are running from the project root or handle paths correctly
    # The task assumes the project structure is: code/, tests/, data/
    
    # Construct the pytest command
    # -v: verbose output
    # --tb=short: short traceback format
    # tests/: Target the tests directory
    cmd = [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short", "--color=yes"]
    
    print(f"Running command: {' '.join(cmd)}")
    print("-" * 80)
    
    # Execute the command
    result = subprocess.run(cmd)
    
    # Return the exit code of pytest
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()