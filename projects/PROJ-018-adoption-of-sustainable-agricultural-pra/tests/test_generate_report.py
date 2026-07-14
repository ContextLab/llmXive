"""Basic sanity test for the report generation script.

The test runs the script on whatever data is present in the repository and
checks that a PDF file is created at the expected location.
"""
import os
from pathlib import Path

import pytest

# Import the main function from the script
from code._05_generate_report import main as generate_report_main  # type: ignore

@pytest.mark.parametrize("output_path", [Path("results/report.pdf")])
def test_report_is_created(tmp_path, monkeypatch, output_path):
    # Ensure a clean environment – delete the file if it exists
    if output_path.is_file():
        output_path.unlink()

    # Run the report generation
    generate_report_main()

    # Verify that the PDF was written
    assert output_path.is_file(), f"Report PDF not found at {output_path}"

# The test deliberately does not assert on content because the report
# depends on upstream data that may vary between runs. The existence of
# the file is sufficient to confirm that the script executed without
# raising an exception.