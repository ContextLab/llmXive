"""
Unit tests for the demo_autocorr script.
"""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

# Import the functions from the script
from demo_autocorr import (
    load_mobius_array,
    load_window_starts,
    compute_autocorrelation,
    OUTPUT_CSV,
    REFERENCE_AUTOCORR,
)

def test_load_mobius_array_exists():
    """The Möbius array must exist for the demo."""
    arr = load_mobius_array()
    assert isinstance(arr, np.ndarray)
    # Basic sanity: values should be in {-1,0,1}
    assert set(np.unique(arr)).issubset({-1, 0, 1})

def test_load_window_starts_structure():
    """Window starts JSON must be parsable and contain L=1000."""
    mapping = load_window_starts()
    assert isinstance(mapping, dict)
    assert 1000 in mapping
    assert isinstance(mapping[1000], list)
    assert len(mapping[1000]) >= 1

def test_compute_autocorrelation_matches_reference():
    """The computed autocorrelation for the demo window must match the reference."""
    mobius = load_mobius_array()
    starts = load_window_starts()
    demo_start = starts[1000][0]
    val = compute_autocorrelation(mobius, demo_start, 1000, 1)
    assert np.isclose(val, REFERENCE_AUTOCORR, atol=1e-9)

def test_demo_csv_written(tmp_path, monkeypatch):
    """Running main() should produce the CSV with the correct header and values."""
    # Redirect the output path to a temporary location
    temp_csv = tmp_path / "demo_autocorr.csv"
    monkeypatch.setattr("demo_autocorr.OUTPUT_CSV", temp_csv)

    # Execute the script's main function
    from demo_autocorr import main as demo_main
    demo_main()

    # Verify the file exists and has the expected format
    assert temp_csv.is_file()
    with temp_csv.open("r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        row = next(reader)

    assert header == ["interval_start", "interval_length", "lag", "autocorrelation"]
    # The row should contain four entries and the autocorrelation should match the reference
    assert len(row) == 4
    assert int(row[0]) == load_window_starts()[1000][0]
    assert int(row[1]) == 1000
    assert int(row[2]) == 1
    assert np.isclose(float(row[3]), REFERENCE_AUTOCORR, atol=1e-9)