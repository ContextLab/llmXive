"""
Unit test for the demo_autocorr script (task T005).
It verifies that the script runs without error and that the produced
CSV contains the expected single row with a value matching the reference.
"""

from pathlib import Path

import numpy as np
import pytest

# Import the script as a module to reuse its helpers.
import sys
sys.path.append(str(Path(__file__).parent.parent / "code"))

import demo_autocorr

@pytest.mark.timeout(300)
def test_demo_autocorr_output(tmp_path, monkeypatch):
    """
    Run the demo_autocorr script in an isolated temporary directory.
    The script should create the output CSV with the correct contents.
    """
    # Redirect the paths used by the script to the temporary directory.
    data_raw = tmp_path / "data" / "raw"
    data_processed = tmp_path / "data" / "processed"
    data_raw.mkdir(parents=True, exist_ok=True)
    data_processed.mkdir(parents=True, exist_ok=True)

    # Create a small Möbius array (N=2000) to keep the test fast.
    # Use the same compute_mobius implementation as the project.
    from sieve import compute_mobius
    mobius_arr = compute_mobius(2000)
    mobius_path = data_raw / "mobius_array.npy"
    np.save(mobius_path, mobius_arr)

    # Create a minimal window index JSON (fallback format).
    window_json_path = data_raw / "window_starts.json"
    window_json_path.write_text('{"1000": [1]}', encoding="utf-8")

    # Monkey‑patch the path constants in the demo module.
    monkeypatch.setattr(demo_autocorr, "MOBIUS_PATH", mobius_path)
    monkeypatch.setattr(demo_autocorr, "WINDOW_INDEX_CSV", Path("/nonexistent"))
    monkeypatch.setattr(demo_autocorr, "WINDOW_INDEX_JSON", window_json_path)
    monkeypatch.setattr(demo_autocorr, "PROCESSED_DEMO_OUTPUT_PATH", data_processed / "demo_autocorr.csv")

    # Run the main function.
    demo_autocorr.main()

    # Verify the output CSV.
    output_path = data_processed / "demo_autocorr.csv"
    assert output_path.is_file(), "Output CSV was not created."

    with output_path.open("r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    # Expect header + one data line.
    assert len(lines) == 2
    header, data_line = lines
    assert header == "interval_start,interval_length,lag,autocorrelation"

    parts = data_line.split(",")
    assert len(parts) == 4
    interval_start, interval_length, lag, autocorr_str = parts
    assert int(interval_start) == 1
    assert int(interval_length) == 1000
    assert int(lag) == 1
    # The reference value is known to high precision.
    expected = demo_autocorr.REFERENCE_AUTOCORR
    assert np.isclose(float(autocorr_str), expected, atol=1e-9)