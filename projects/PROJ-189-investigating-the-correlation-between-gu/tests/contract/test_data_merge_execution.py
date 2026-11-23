"""
Execution script to run contract tests for the merged dataframe schema.

This script is designed to be run directly to verify the output of the
data ingestion pipeline (T012-T018) before proceeding to subsequent tasks.

Usage:
    python tests/contract/test_data_merge_execution.py
"""
import sys
import subprocess
import os
from pathlib import Path

# Ensure we are in the project root or adjust paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
os.chdir(PROJECT_ROOT)

def run_tests():
    """Run the contract tests using pytest."""
    test_file = PROJECT_ROOT / "tests" / "contract" / "test_data_merge.py"
    
    if not test_file.exists():
        print("ERROR: Test file not found. Please ensure test_data_merge.py exists.")
        sys.exit(1)

    print(f"Running contract tests for merged dataframe schema: {test_file}")
    
    # Run pytest with verbose output
    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(test_file), "-v", "--tb=long"],
        cwd=PROJECT_ROOT
    )
    
    if result.returncode == 0:
        print("\n✅ All contract tests PASSED.")
        print("The merged dataframe satisfies the schema requirements.")
    else:
        print("\n❌ Contract tests FAILED.")
        print("Please review the errors above and fix the data ingestion pipeline.")
    
    return result.returncode

if __name__ == "__main__":
    sys.exit(run_tests())