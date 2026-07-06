"""
T036: Run the full tests/ suite and ensure all tests pass.

This script discovers and executes all pytest tests in the `tests/` directory.
It exits with code 0 if all tests pass, and non-zero otherwise.
"""
import sys
import subprocess
from pathlib import Path

def main():
    project_root = Path(__file__).resolve().parent.parent
    tests_dir = project_root / "tests"

    if not tests_dir.exists():
        print(f"Error: Tests directory not found at {tests_dir}", file=sys.stderr)
        sys.exit(1)

    print(f"Running pytest suite in {tests_dir}...")
    
    # Run pytest with verbose output, failing fast on error if desired, 
    # but here we want to see all results.
    # We use the standard pytest invocation.
    cmd = [
        sys.executable, "-m", "pytest",
        str(tests_dir),
        "-v",
        "--tb=short",
        "--color=yes"
    ]

    try:
        result = subprocess.run(cmd, cwd=project_root)
        if result.returncode == 0:
            print("\n✅ All tests passed successfully.")
        else:
            print(f"\n❌ Test suite failed with exit code {result.returncode}.")
        sys.exit(result.returncode)
    except FileNotFoundError:
        print("Error: pytest not found. Please ensure it is installed in the environment.", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nTest suite interrupted by user.", file=sys.stderr)
        sys.exit(130)

if __name__ == "__main__":
    main()