"""
Script to run pytest on all unit and integration tests and generate a summary report.
This script executes pytest with specific flags to ensure verbose output and
generates a JSON report for automated parsing.
"""
import subprocess
import sys
import os
import json
from pathlib import Path

def main():
    # Ensure we are in the project root
    project_root = Path(__file__).resolve().parent.parent.parent
    os.chdir(project_root)

    # Define the output directory for reports
    results_dir = project_root / "data" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    report_path = results_dir / "pytest_results.json"
    summary_path = results_dir / "pytest_summary.txt"

    # Construct the pytest command
    # -v: verbose
    # --tb=short: short traceback format
    # --json-report: generate JSON report (requires pytest-json-report plugin)
    # --json-report-file: specify output file
    # --cov: optional coverage if installed, but we focus on pass rate first
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/unit",
        "tests/integration",
        "-v",
        "--tb=short",
        "--json-report",
        f"--json-report-file={report_path}"
    ]

    print(f"Running pytest from: {project_root}")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 80)

    try:
        # Run pytest
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False  # Don't raise exception on non-zero exit, we handle it
        )

        # Print output
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)

        # Parse the JSON report if it exists
        if report_path.exists():
            with open(report_path, 'r') as f:
                report_data = json.load(f)

            total = report_data.get("totals", {}).get("collected", 0)
            passed = report_data.get("totals", {}).get("passed", 0)
            failed = report_data.get("totals", {}).get("failed", 0)
            errors = report_data.get("totals", {}).get("error", 0)
            skipped = report_data.get("totals", {}).get("skipped", 0)

            pass_rate = (passed / total * 100) if total > 0 else 0.0

            summary = {
                "total_tests": total,
                "passed": passed,
                "failed": failed,
                "errors": errors,
                "skipped": skipped,
                "pass_rate_percent": round(pass_rate, 2),
                "status": "PASSED" if failed == 0 and errors == 0 else "FAILED"
            }

            # Write summary to text file
            with open(summary_path, 'w') as f:
                f.write(f"Pytest Execution Summary\n")
                f.write(f"========================\n")
                f.write(f"Total Tests: {total}\n")
                f.write(f"Passed: {passed}\n")
                f.write(f"Failed: {failed}\n")
                f.write(f"Errors: {errors}\n")
                f.write(f"Skipped: {skipped}\n")
                f.write(f"Pass Rate: {summary['pass_rate_percent']}%\n")
                f.write(f"Overall Status: {summary['status']}\n")

            print("-" * 80)
            print(f"Report saved to: {report_path}")
            print(f"Summary saved to: {summary_path}")
            print(f"Pass Rate: {summary['pass_rate_percent']}%")

            # Return exit code based on success
            if summary['status'] == "PASSED":
                return 0
            else:
                return 1
        else:
            print("ERROR: JSON report was not generated.")
            return 1

    except Exception as e:
        print(f"ERROR: Failed to run pytest: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
