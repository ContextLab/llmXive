"""Test that the data‑model validation script runs successfully.

The script should exit with status code ``0`` and produce a validation
report that states all required entities are present.
"""

import subprocess
import sys
from pathlib import Path


def _project_root() -> Path:
    """Return the repository root (two levels up from this test file)."""
    return Path(__file__).resolve().parents[2]


def test_verify_data_model_script():
    """Execute ``code/verify_data_model.py`` and check its output."""
    script_path = _project_root() / "code" / "verify_data_model.py"
    # Run the script in a subprocess so we can inspect the exit code.
    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
    )
    # The script must exit cleanly.
    assert result.returncode == 0, (
        f"Verification script failed (exit {result.returncode}).\\n"
        f"stderr: {result.stderr}"
    )

    # Verify that the validation report was created and contains the success line.
    report_path = _project_root() / "data" / "validation_report.txt"
    assert report_path.is_file(), "validation_report.txt was not created."
    report_content = report_path.read_text(encoding="utf-8")
    assert "All expected entities are present" in report_content, (
        "Report does not indicate successful validation.\\n"
        f"Report content: {report_content}"
    )