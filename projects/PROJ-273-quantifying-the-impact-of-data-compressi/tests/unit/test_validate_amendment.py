"""
Unit test for the amendment‑validation script.

The test simply imports the ``validate_amendment`` function, executes it,
and checks that the expected report file is created and contains a
pass/fail marker.  Because the repository already contains real
``amendment_draft.md`` and ``plan.md`` files, the test runs on actual data
and does not rely on any fabricated input.
"""

import os
from pathlib import Path

# Import the function under test
from code.validate_amendment import validate_amendment

def test_validate_amendment_creates_report(tmp_path: Path):
    """
    Ensure that ``validate_amendment`` writes a report file and returns a
    boolean indicating success.
    """
    # Run the validation routine
    result = validate_amendment()

    # Determine the expected report location (relative to the repository root)
    repo_root = Path(__file__).resolve().parents[2]  # tests/unit/ -> repo root
    report_path = repo_root / "data" / "validation" / "amendment_validation_report.txt"

    # The report must exist
    assert report_path.is_file(), f"Report file not found at {report_path}"

    # The file should contain either the ✅ or ❌ marker
    content = report_path.read_text(encoding="utf-8")
    assert "✅ Validation Passed" in content or "❌ Validation Failed" in content

    # The function's boolean result should match the marker in the report
    if "✅ Validation Passed" in content:
        assert result is True
    else:
        assert result is False

# The test function is deliberately simple; its purpose is to guarantee that
# the script performs a real I/O operation and returns a meaningful status.