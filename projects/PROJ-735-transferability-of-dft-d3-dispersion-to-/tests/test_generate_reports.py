import subprocess
import sys
from pathlib import Path

def test_generate_reports_runs_successfully():
    """
    Ensure that the report generation script runs without error and
    produces a benchmark report containing the Calibration Procedure section.
    """
    repo_root = Path(__file__).resolve().parents[2]
    script_path = repo_root / "code" / "generate_reports.py"

    # Run the script
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Script failed: {result.stderr}"

    # Verify benchmark report exists and contains the expected header
    report_path = repo_root / "docs" / "benchmark_report.md"
    assert report_path.is_file(), "Benchmark report was not created"

    content = report_path.read_text()
    assert "## 4. Calibration Procedure" in content, "Calibration Procedure section missing"