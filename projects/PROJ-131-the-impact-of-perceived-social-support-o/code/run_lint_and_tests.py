"""
Script to run linting (ruff) and tests (pytest) as part of the final code review (T063).
Generates log files for verification.
"""
import os
import sys
import subprocess
import time
from pathlib import Path

def run_command(cmd: list, description: str, output_file: Path) -> bool:
    """Run a shell command and capture output to a file."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}\n")

    start_time = time.time()
    try:
        with open(output_file, 'w') as f:
            # Run command, capture stdout and stderr
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                check=False # Don't raise exception immediately, we handle it
            )
            f.write(result.stdout)
            if result.stderr: # Should be merged into stdout via stderr=STDOUT
                f.write(result.stderr)

            f.write(f"\n---\nReturn Code: {result.returncode}\n")
            f.write(f"Duration: {time.time() - start_time:.2f}s\n")

        if result.returncode == 0:
            print(f"SUCCESS: {description} completed without errors.")
            return True
        else:
            print(f"FAILURE: {description} failed with return code {result.returncode}.")
            print(f"Check log: {output_file}")
            return False
    except Exception as e:
        print(f"ERROR running {description}: {e}")
        with open(output_file, 'a') as f:
            f.write(f"\nException: {e}\n")
        return False

def main() -> None:
    """Main entry point for lint and test execution."""
    project_root = Path(__file__).parent
    results_dir = project_root.parent / "data" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    lint_log = results_dir / "linting_report.txt"
    test_log = results_dir / "test_report.txt"

    print("Starting Final Code Review (T063)...")

    # 1. Run Linting
    lint_success = run_command(
        ["ruff", "check", "."],
        "Ruff Linting Check",
        lint_log
    )

    # 2. Run Tests
    test_success = run_command(
        [sys.executable, "-m", "pytest", "code/tests", "-v", "--tb=short"],
        "Pytest Unit & Contract Tests",
        test_log
    )

    # Summary
    print("\n" + "="*60)
    print("FINAL CODE REVIEW SUMMARY")
    print("="*60)
    print(f"Linting (ruff): {'PASSED' if lint_success else 'FAILED'}")
    print(f"Tests (pytest): {'PASSED' if test_success else 'FAILED'}")
    print(f"Lint Log: {lint_log}")
    print(f"Test Log: {test_log}")

    if lint_success and test_success:
        print("\nT063 Status: COMPLETED")
        sys.exit(0)
    else:
        print("\nT063 Status: FAILED - See logs for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()