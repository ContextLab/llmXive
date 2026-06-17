"""Unit test for the validation status report generator.

The test simply runs the ``validation_status`` script and checks that
the expected markdown file is created and contains a markdown table with
at least one row (the header row plus the first validation component).
"""

import subprocess
from pathlib import Path

def test_validation_status_report_is_created(tmp_path: Path) -> None:
    # Ensure a clean state: remove any existing report
    report_path = Path("docs/reproducibility/validation_status.md")
    if report_path.is_file():
        report_path.unlink()

    # Run the script
    result = subprocess.run(
        ["python", "code/reproducibility/validation_status.py"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Script failed: {result.stderr}"

    # Verify the file now exists
    assert report_path.is_file(), "validation_status.md was not created"

    # Basic sanity check: file contains a markdown table header
    content = report_path.read_text()
    assert "| Validation component | Status |" in content
    # At least one component row should be present
    lines = [ln for ln in content.splitlines() if ln.startswith("|") and "PASS" in ln or "FAIL" in ln or "UNKNOWN" in ln]
    assert len(lines) >= 2, "Expected at least one validation component row in the report"