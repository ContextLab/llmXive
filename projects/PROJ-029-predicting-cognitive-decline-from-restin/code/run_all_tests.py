"""
Test suite runner for the llmXive automated science pipeline.
Executes all tests in the tests/ directory and produces a summary report.
"""
import sys
import subprocess
import json
import os
from pathlib import Path
from datetime import datetime

def run_tests():
    """
    Runs the pytest suite located in the tests/ directory.
    Returns a dictionary containing the exit code, stdout, stderr, and summary.
    """
    project_root = Path(__file__).parent.parent
    tests_dir = project_root / "tests"
    output_log = project_root / "data" / "artifacts" / "test_results.json"
    
    # Ensure output directory exists
    output_log.parent.mkdir(parents=True, exist_ok=True)

    if not tests_dir.exists():
        return {
            "status": "error",
            "message": "Tests directory not found",
            "exit_code": 1
        }

    # Construct pytest command
    # -v: verbose
    # --tb=short: short traceback
    # --json-report: generate JSON report (requires pytest-json-report plugin)
    # If pytest-json-report is not available, we fallback to parsing standard output
    cmd = [
        sys.executable, "-m", "pytest",
        str(tests_dir),
        "-v",
        "--tb=short",
        "--color=yes"
    ]

    print(f"Running tests from: {tests_dir}")
    print(f"Command: {' '.join(cmd)}")

    try:
        # Run subprocess and capture output
        result = subprocess.run(
            cmd,
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout for full suite
        )

        exit_code = result.returncode
        stdout = result.stdout
        stderr = result.stderr

        # Parse basic stats from stdout if possible
        # Expected format: "X passed, Y failed, Z skipped in T.TTs"
        summary = {
            "timestamp": datetime.now().isoformat(),
            "exit_code": exit_code,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "total": 0,
            "log_path": str(output_log)
        }

        # Simple regex-free parsing of the final line
        # Look for patterns like "X passed"
        for line in stdout.split('\n'):
            if 'passed' in line:
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == 'passed':
                        summary['passed'] = int(parts[i-1])
                    if part == 'failed':
                        summary['failed'] = int(parts[i-1])
                    if part == 'skipped':
                        summary['skipped'] = int(parts[i-1])
                # Total is usually sum or explicitly stated
                # We'll calculate total as passed + failed + skipped + errors
                summary['total'] = summary['passed'] + summary['failed'] + summary['skipped']
                break

        # Write detailed log
        log_entry = {
            "summary": summary,
            "stdout": stdout,
            "stderr": stderr
        }

        with open(output_log, 'w') as f:
            json.dump(log_entry, f, indent=2)

        print(f"\n--- Test Summary ---")
        print(f"Passed: {summary['passed']}")
        print(f"Failed: {summary['failed']}")
        print(f"Skipped: {summary['skipped']}")
        print(f"Total: {summary['total']}")
        print(f"Exit Code: {exit_code}")
        print(f"Log saved to: {output_log}")

        return {
            "status": "success" if exit_code == 0 else "failure",
            "exit_code": exit_code,
            "summary": summary
        }

    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "message": "Test suite timed out after 600 seconds",
            "exit_code": 1
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "exit_code": 1
        }

def main():
    """
    Entry point for the test runner.
    """
    result = run_tests()
    
    if result["status"] == "success":
        print("\nAll tests passed.")
        sys.exit(0)
    elif result["status"] == "failure":
        print("\nSome tests failed. See data/artifacts/test_results.json for details.")
        sys.exit(1)
    else:
        print(f"\nError running tests: {result['message']}")
        sys.exit(1)

if __name__ == "__main__":
    main()