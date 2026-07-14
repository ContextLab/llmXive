"""
Script to run the full pytest suite for the llmXive research project.
This script executes all unit and integration tests and generates a summary report.
"""
import subprocess
import sys
import os
import json
from datetime import datetime

def run_pytest_suite():
    """Run pytest with verbose output and generate a JSON summary."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    tests_dir = os.path.join(project_root, "tests")
    
    # Ensure tests directory exists
    if not os.path.exists(tests_dir):
        print(f"Error: Tests directory not found at {tests_dir}")
        return False

    # Construct pytest command
    # -v: verbose
    # --tb=short: short traceback
    # --json-report: generate JSON report (requires pytest-json-report)
    # --json-report-file: specify output file
    # We also capture stdout/stderr for a text summary
    cmd = [
        sys.executable, "-m", "pytest",
        tests_dir,
        "-v",
        "--tb=short",
        "--json-report",
        "--json-report-file=tests/pytest_report.json",
        "--junit-xml=tests/pytest_results.xml"
    ]

    print(f"Running tests from: {tests_dir}")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 80)

    try:
        # Run pytest
        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=False, # Stream output to console
            text=True
        )

        # Check if pytest-json-report was installed, if not, try without it
        if result.returncode != 0 and "No module named 'pytest_json_report'" in result.stderr:
            print("Installing pytest-json-report...")
            subprocess.run([sys.executable, "-m", "pip", "install", "pytest-json-report"], cwd=project_root)
            print("Retrying with JSON report...")
            result = subprocess.run(
                cmd,
                cwd=project_root,
                capture_output=False,
                text=True
            )

        # Generate a simple text summary if JSON report generation failed or wasn't requested
        if result.returncode != 0 and not os.path.exists(os.path.join(project_root, "tests", "pytest_report.json")):
            # Fallback: just run without json report but still capture status
            print("\n--- Running without JSON report (fallback) ---")
            fallback_cmd = [
                sys.executable, "-m", "pytest",
                tests_dir,
                "-v",
                "--tb=short"
            ]
            subprocess.run(fallback_cmd, cwd=project_root)
            result = subprocess.run(fallback_cmd, cwd=project_root, capture_output=True, text=True)

        # Save a summary of the run
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        summary = {
            "run_timestamp": timestamp,
            "exit_code": result.returncode,
            "tests_directory": tests_dir,
            "status": "PASSED" if result.returncode == 0 else "FAILED"
        }

        summary_path = os.path.join(project_root, "tests", f"test_run_summary_{timestamp}.json")
        with open(summary_path, "w") as f:
            json.dump(summary, f, indent=2)

        print("-" * 80)
        print(f"Test run completed with exit code: {result.returncode}")
        print(f"Summary saved to: {summary_path}")
        
        # If JSON report exists, print a snippet
        json_report_path = os.path.join(project_root, "tests", "pytest_report.json")
        if os.path.exists(json_report_path):
            print(f"Detailed JSON report saved to: {json_report_path}")
            with open(json_report_path, "r") as f:
                report_data = json.load(f)
                print(f"Total tests: {report_data.get('collected', 0)}")
                print(f"Passed: {report_data.get('passed', 0)}")
                print(f"Failed: {report_data.get('failed', 0)}")
                print(f"Skipped: {report_data.get('skipped', 0)}")
                if report_data.get('errors', 0) > 0:
                    print(f"Errors: {report_data.get('errors', 0)}")

        return result.returncode == 0

    except Exception as e:
        print(f"Error running pytest: {e}")
        return False

if __name__ == "__main__":
    success = run_pytest_suite()
    sys.exit(0 if success else 1)
