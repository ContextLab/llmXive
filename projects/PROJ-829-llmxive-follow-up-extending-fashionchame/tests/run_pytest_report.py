"""
Script to run pytest and generate a report.
"""
import subprocess
import sys
import os
from pathlib import Path

def main():
    """Run pytest and generate a summary report."""
    project_root = Path(__file__).parent.parent
    tests_dir = project_root / "tests"
    
    # Ensure code/ is in path
    code_dir = project_root / "code"
    if str(code_dir) not in sys.path:
        sys.path.insert(0, str(code_dir))
    
    # Run pytest with JUnit XML output
    xml_report = project_root / "test-results" / "pytest-results.xml"
    xml_report.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Running tests with report generation...")
    result = subprocess.run(
        [
            sys.executable, "-m", "pytest",
            str(tests_dir),
            "-v",
            "--tb=short",
            f"--junit-xml={xml_report}",
            "--report-log", str(project_root / "test-results" / "report.log")
        ],
        cwd=str(project_root),
        capture_output=False
    )
    
    if result.returncode != 0:
        print(f"Tests completed with failures. Report saved to {xml_report}")
        sys.exit(result.returncode)
    else:
        print(f"All tests passed! Report saved to {xml_report}")
        sys.exit(0)

if __name__ == "__main__":
    main()