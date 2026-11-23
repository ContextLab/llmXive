"""
Test runner for the llmXive Antibiotic Resistance Pipeline.
Executes the full pytest suite and ensures all contract tests pass.
"""
import sys
import subprocess
import argparse
from pathlib import Path

def run_pytest_suite():
    """Run the full pytest suite with JUnit XML output."""
    project_root = Path(__file__).parent.parent
    tests_dir = project_root / "tests"
    junit_output = project_root / "data" / "pytest_results.xml"

    # Ensure data directory exists for output
    junit_output.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable, "-m", "pytest",
        str(tests_dir),
        "-v",
        "--tb=short",
        f"--junit-xml={junit_output}",
        "-x",  # Stop on first failure
    ]

    print(f"Running tests with command: {' '.join(cmd)}")
    result = subprocess.run(cmd)

    if result.returncode == 0:
        print(f"\n✓ All tests passed. Results saved to {junit_output}")
    else:
        print(f"\n✗ Test suite failed with exit code {result.returncode}")
        print(f"Check {junit_output} for details.")

    return result.returncode

def main():
    parser = argparse.ArgumentParser(description="Run full test suite for llmXive pipeline.")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output (passed to pytest)")
    args = parser.parse_args()

    exit_code = run_pytest_suite()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
