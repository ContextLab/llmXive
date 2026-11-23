"""
Integration test for the PII scanner (T052).

The test simply invokes the scanner script and checks that the expected
output CSV file is created and contains the correct header row.  No real
PII is required in the sample data – the repository ships only a tiny
``data/raw/github-code-sample.csv`` which is a real snippet from the
``codeparrot/github-code`` dataset.
"""

import csv
from pathlib import Path

import pytest

# Import the scanner's entry point – this also triggers logging configuration.
from pii_scanner import main as run_scanner  # type: ignore


@pytest.fixture(scope="module")
def data_root() -> Path:
    """Root of the project's data directory."""
    from config import get_data_root

    return get_data_root()


def test_pii_scan_creates_output(data_root: Path, tmp_path: Path):
    """
    Run the scanner and verify that ``pii_findings.csv`` exists and has the
    correct header columns.
    """
    # Ensure a clean state
    output_file = data_root / "pii_findings.csv"
    if output_file.exists():
        output_file.unlink()

    # Execute the scanner
    run_scanner()

    # The file must now exist
    assert output_file.is_file(), "PII findings CSV was not created"

    # Validate header structure
    with open(output_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        expected_fields = [
            "file_path",
            "line_number",
            "pii_type",
            "matched_text",
            "timestamp",
        ]
        assert reader.fieldnames == expected_fields, "CSV header mismatch"

    # The test does not enforce any findings – an empty file is acceptable.
    # It only guarantees that the scanner runs without error and respects the
    # contract defined in ``code/pii_scanner.py``.

# The test suite will automatically discover this file via pytest's default
# discovery rules. No additional configuration is required.