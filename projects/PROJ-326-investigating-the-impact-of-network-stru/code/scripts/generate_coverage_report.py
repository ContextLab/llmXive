"""
Script to run pytest with coverage and generate reports.

This script executes the test suite and generates:
- A terminal summary (text)
- An HTML report in `code/htmlcov/`
- An XML report (Cobertura format) in `code/coverage.xml`

Usage:
    python code/scripts/generate_coverage_report.py
"""
import argparse
import sys
import subprocess
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(
        description="Run pytest with coverage and generate reports."
    )
    parser.add_argument(
        "--cov-fail-under",
        type=int,
        default=0,
        help="Minimum coverage percentage required to pass (default: 0)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output from pytest",
    )
    args = parser.parse_args()

    # Determine project root relative to this script
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent
    code_dir = project_root / "code"
    tests_dir = code_dir / "tests"
    src_dir = code_dir / "src"

    if not tests_dir.exists():
        print(f"Error: Tests directory not found at {tests_dir}", file=sys.stderr)
        sys.exit(1)

    if not src_dir.exists():
        print(f"Error: Source directory not found at {src_dir}", file=sys.stderr)
        sys.exit(1)

    # Build pytest command
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        str(tests_dir),
        f"--cov={src_dir}",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov",
        "--cov-report=xml:coverage.xml",
        f"--cov-fail-under={args.cov_fail_under}",
    ]

    if args.verbose:
        cmd.append("-v")

    print(f"Running coverage analysis from: {code_dir}")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 40)

    # Execute pytest
    result = subprocess.run(cmd, cwd=code_dir)

    if result.returncode == 0:
        print("-" * 40)
        print("Coverage report generated successfully.")
        print(f"  - HTML report: {code_dir / 'htmlcov' / 'index.html'}")
        print(f"  - XML report:  {code_dir / 'coverage.xml'}")
    else:
        print("-" * 40)
        print("Coverage check failed or tests did not pass.", file=sys.stderr)
    
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()