"""
Runner script to execute contract tests for merged dataframe schema.

This script is invoked to execute T045 and verify the merged dataframe schema.
"""
import sys
import subprocess
from pathlib import Path

def main():
    """Execute contract tests for merged dataframe schema."""
    project_root = Path(__file__).parent.parent
    tests_dir = project_root / "tests" / "contract"
    
    print("Executing contract tests for merged dataframe schema (T045)...")
    print(f"Test directory: {tests_dir}")
    
    # Run pytest on the test file
    result = subprocess.run(
        [
            sys.executable, "-m", "pytest",
            str(tests_dir / "test_data_merge.py"),
            "-v",
            "--tb=short",
            "--capture=no"
        ],
        cwd=project_root,
        capture_output=False
    )
    
    if result.returncode == 0:
        print("\n✓ Contract tests for merged dataframe schema PASSED (T045)")
        return 0
    else:
        print("\n✗ Contract tests for merged dataframe schema FAILED (T045)")
        return 1

if __name__ == "__main__":
    sys.exit(main())