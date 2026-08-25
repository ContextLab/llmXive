"""
Script to run all tests in the project.
"""
import subprocess
import sys
import os
from pathlib import Path

def main():
    """Run all pytest tests."""
    project_root = Path(__file__).parent.parent
    tests_dir = project_root / "tests"
    
    # Ensure code/ is in path
    code_dir = project_root / "code"
    if str(code_dir) not in sys.path:
        sys.path.insert(0, str(code_dir))
    
    # Run pytest
    print(f"Running all tests from {tests_dir}...")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(tests_dir), "-v", "--tb=short"],
        cwd=str(project_root),
        capture_output=False
    )
    
    if result.returncode != 0:
        print("Some tests failed!")
        sys.exit(result.returncode)
    else:
        print("All tests passed!")
        sys.exit(0)

if __name__ == "__main__":
    main()
