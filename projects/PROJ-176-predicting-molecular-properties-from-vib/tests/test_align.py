"""
Test the ``code/data/align.py`` script.

The test executes the script (which reads the raw parquet files,
performs the inner join, and writes ``data/processed/alignment_report.json``)
and then checks that the JSON file exists and contains the required fields.
"""

import json
from pathlib import Path

import pytest

# Import the script as a module to run its ``main`` function
from importlib import import_module

@pytest.mark.parametrize("script_path", ["code/data/align.py"])
def test_alignment_report_generated(script_path):
    # Ensure a clean state: remove any existing report
    report_path = Path("data/processed/alignment_report.json")
    if report_path.is_file():
        report_path.unlink()

    # Import and run the script's main()
    module = import_module("code.data.align")
    module.main()

    # After execution the report must exist
    assert report_path.is_file(), "alignment_report.json was not created"

    # Load and validate JSON content
    with open(report_path, "r", encoding="utf-8") as f:
        report = json.load(f)

    # Required fields
    assert "matched" in report, "Report missing 'matched' field"
    assert "discarded" in report, "Report missing 'discarded' field"

    # Matched must be an integer >= 129000 (as per verification criteria)
    matched = report["matched"]
    assert isinstance(matched, int), "'matched' should be an integer"
    assert matched >= 129_000, f"Matched molecules {matched} below required threshold"

    # Discarded must be a non‑negative integer
    discarded = report["discarded"]
    assert isinstance(discarded, int) and discarded >= 0, "'discarded' must be a non‑negative integer"