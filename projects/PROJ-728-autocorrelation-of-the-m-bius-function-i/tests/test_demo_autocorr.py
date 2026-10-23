"""
Unit test for the demo_autocorr script (task T005).
Verifies that the script runs without error and produces a CSV
with the expected format and a value matching the reference.
"""

import csv
from pathlib import Path

import pytest

# Import the main function directly for testing.
from demo_autocorr import main as demo_main

@pytest.mark.parametrize("output_path", [Path("data/processed/demo_autocorr.csv")])
def test_demo_autocorr_produces_file(output_path: Path):
    # Ensure any previous artifact is removed.
    if output_path.is_file():
        output_path.unlink()

    # Run the demo script.
    demo_main()

    # Verify the file now exists.
    assert output_path.is_file(), f"{output_path} was not created"

    # Verify CSV header and one data row.
    with output_path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = list(reader)

    assert rows[0] == [
        "interval_start",
        "interval_length",
        "lag",
        "autocorrelation",
    ], "CSV header is incorrect"

    # Exactly one data row expected.
    assert len(rows) == 2, "CSV should contain exactly one data row"

    # Validate the numeric values have the required precision.
    data_row = rows[1]
    assert int(data_row[0]) > 0, "interval_start must be positive"
    assert int(data_row[1]) == 1000, "interval_length must be 1000"
    assert int(data_row[2]) == 1, "lag must be 1"

    # Autocorrelation value should match the reference within tolerance.
    autocorr = float(data_row[3])
    assert abs(autocorr + 0.047047047047) < 1e-9, "autocorrelation value mismatch"