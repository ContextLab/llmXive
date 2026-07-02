"""
Script to run pytest with coverage on src/ and tests/ and generate a report.
This implements task T043a: Run `pytest --cov` on `src/` and `tests/`.
"""
import subprocess
import sys
import os
from pathlib import Path

def main():
    # Ensure we are in the project root
    project_root = Path(__file__).resolve().parent.parent
    os.chdir(project_root)

    print(f"Running coverage from: {project_root}")

    # Construct the pytest command
    # --cov=src: coverage for src directory
    # --cov=tests: coverage for tests directory
    # --cov-report=term-missing: show missing lines in terminal
    # --cov-report=html: generate HTML report in htmlcov/
    # --cov-report=xml: generate XML report for CI integration
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/",
        "--cov=src",
        "--cov=tests",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov",
        "--cov-report=xml:coverage.xml",
        "-v"
    ]

    print(f"Executing: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True)
        print("\n✓ Coverage run completed successfully.")
        print("Reports generated in: htmlcov/, coverage.xml")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Coverage run failed with exit code {e.returncode}")
        print("Note: Test failures do not necessarily mean coverage failed,")
        print("but the coverage report will only reflect the lines executed before failure.")
        # Return 0 if we just want the coverage data even if tests fail, 
        # but typically we want to know if tests pass. 
        # For this task, we want to ensure the command runs and generates a report.
        # Let's re-run with --continue-on-collection-errors or just accept the partial run if tests fail.
        # However, standard practice is to let it fail if tests fail. 
        # The task is to "Run pytest --cov". If tests fail, the run technically happened.
        # But to be safe and ensure a report exists even with failures, we might catch it.
        # Let's try to run again with --tb=no to just get coverage if the first run failed on test logic.
        # Actually, the requirement is to run it. If tests fail, that's a separate issue.
        # We will return the error code to indicate the run didn't complete cleanly.
        return e.returncode
    except FileNotFoundError:
        print("Error: pytest or coverage not found. Ensure requirements are installed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
