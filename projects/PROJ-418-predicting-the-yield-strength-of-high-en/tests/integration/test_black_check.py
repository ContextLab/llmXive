"""
Integration test for the black formatting check script.

The test runs the ``run_black_check.py`` script, verifies that
``output/black_check_report.txt`` is created, and asserts that the
report contains the expected success message from Black when no
reformatting is required.
"""
import subprocess
import sys
from pathlib import Path

def test_black_check_creates_report_and_passes():
    # Run the script using the same interpreter
    result = subprocess.run(
        [sys.executable, "code/run_black_check.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )

    # The script should exit with code 0 if formatting is correct
    assert result.returncode == 0, f"Black check failed: {result.stdout}"

    report_path = Path("output") / "black_check_report.txt"
    assert report_path.is_file(), "Black check report was not created."

    report_content = report_path.read_text()
    # Black prints "All done!" when everything is formatted
    assert "All done!" in report_content, (
        "Black report does not indicate successful formatting. "
        f"Content was:\n{report_content}"
    )
