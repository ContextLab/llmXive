"""
Run the full test suite for the cognitive decline prediction pipeline.
This script executes all pytest tests and generates a summary report.
"""
import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime

def main():
    """Run the full test suite and generate a summary report."""
    project_root = Path(__file__).parent.parent
    tests_dir = project_root / "tests"
    artifacts_dir = project_root / "data" / "artifacts"
    
    # Ensure artifacts directory exists
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    
    # Build pytest command
    pytest_cmd = [
        sys.executable, "-m", "pytest",
        str(tests_dir),
        "-v",
        "--tb=short",
        "--json-report",
        f"--json-report-file={artifacts_dir / 'test_results.json'}",
        "--cov=code",
        f"--cov-report=term-missing",
        f"--cov-report=html:{artifacts_dir / 'coverage_html'}",
        f"--cov-report=xml:{artifacts_dir / 'coverage.xml'}"
    ]
    
    print(f"Running test suite from: {tests_dir}")
    print(f"Command: {' '.join(pytest_cmd)}")
    print("-" * 80)
    
    # Run pytest
    result = subprocess.run(pytest_cmd)
    
    # Generate summary report
    summary_path = artifacts_dir / "test_summary.json"
    timestamp = datetime.utcnow().isoformat() + "Z"
    
    summary = {
        "timestamp": timestamp,
        "test_directory": str(tests_dir),
        "pytest_exit_code": result.returncode,
        "status": "passed" if result.returncode == 0 else "failed",
        "report_files": {
            "json_report": str(artifacts_dir / "test_results.json"),
            "coverage_html": str(artifacts_dir / "coverage_html"),
            "coverage_xml": str(artifacts_dir / "coverage.xml"),
            "summary": str(summary_path)
        }
    }
    
    # Try to extract detailed stats from the JSON report
    json_report_path = artifacts_dir / "test_results.json"
    if json_report_path.exists():
        try:
            with open(json_report_path, "r") as f:
                report_data = json.load(f)
            
            summary["total_tests"] = report_data.get("tests", []) and len(report_data["tests"])
            summary["passed"] = sum(1 for t in report_data.get("tests", []) if t["outcome"] == "passed")
            summary["failed"] = sum(1 for t in report_data.get("tests", []) if t["outcome"] == "failed")
            summary["skipped"] = sum(1 for t in report_data.get("tests", []) if t["outcome"] == "skipped")
            summary["errors"] = sum(1 for t in report_data.get("tests", []) if t.get("error"))
            
            if report_data.get("tests"):
                summary["duration_seconds"] = report_data.get("duration", 0)
        except Exception as e:
            summary["parse_error"] = str(e)
    
    # Write summary
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    
    print("-" * 80)
    print(f"Test summary written to: {summary_path}")
    print(f"Overall status: {summary['status'].upper()}")
    
    if result.returncode == 0:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed or errors occurred.")
        print("Check the detailed reports in data/artifacts/")
    
    return result.returncode

if __name__ == "__main__":
    sys.exit(main())