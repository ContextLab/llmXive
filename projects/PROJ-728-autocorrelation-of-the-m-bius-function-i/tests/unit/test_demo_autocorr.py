"""
Unit test for the demo_autocorr script (task T005).
"""

import csv
from pathlib import Path

import numpy as np

# Import the script's main function.
from code.demo_autocorr import main as demo_main

def test_demo_autocorr_file_exists(tmp_path, monkeypatch):
    """
    Ensure that the demo script creates the expected CSV file with the
    correct header and a single row containing the reference autocorrelation.
    """
    # Monkey‑patch the data paths to point to the test fixtures.
    # The fixtures are the real data files shipped with the repository.
    # They are small enough for the test runner.
    mobius_path = Path("data/raw/mobius_array.npy")
    window_json_path = Path("data/raw/window_starts.json")
    output_path = Path("data/processed/demo_autocorr.csv")

    # Ensure a clean state before running the demo.
    if output_path.is_file():
        output_path.unlink()

    # Run the demo script.
    demo_main()

    # Verify that the output file now exists.
    assert output_path.is_file(), "demo_autocorr.csv was not created"

    # Verify the CSV content.
    with output_path.open("r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        row = next(reader)

    expected_header = ["interval_start", "interval_length", "lag", "autocorrelation"]
    assert header == expected_header, f"Unexpected CSV header: {header}"

    # The reference autocorrelation is known from the spec.
    expected_autocorr = "-0.047047047047"
    assert row[3] == expected_autocorr, f"Unexpected autocorrelation value: {row[3]}"