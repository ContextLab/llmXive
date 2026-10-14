import subprocess
from pathlib import Path

def test_generate_reports():
    """
    End‑to‑end test that the report generation script runs without error
    and produces the expected markdown files with the calibration section.
    """
    # Run the script
    result = subprocess.run(
        ["python", "code/generate_reports.py"],
        cwd=Path(__file__).resolve().parents[2],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Script failed: {result.stderr}"

    # Verify benchmark report exists
    benchmark_path = Path("docs/benchmark_report.md")
    assert benchmark_path.is_file(), "Benchmark report not created"

    # Check that the calibration section contains a scaling factor line
    content = benchmark_path.read_text()
    assert "## 4. Calibration Procedure" in content, "Calibration section missing"
    assert "Scaling factor (s)" in content, "Scaling factor not inserted"
    # Verify that a numeric value appears after the scaling factor label
    import re

    match = re.search(r"Scaling factor \(s\).*?`([\d\.]+)`", content, re.DOTALL)
    assert match, "Scaling factor numeric value not found in report"