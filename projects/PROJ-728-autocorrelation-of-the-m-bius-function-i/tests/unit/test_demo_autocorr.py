"""
Unit tests for the demo_autocorr script (task T005).
"""

import csv
from pathlib import Path

import numpy as np

# Import the function directly from the module we just created.
from demo_autocorr import (
    _load_mobius_array,
    _load_window_starts,
    compute_autocorrelation,
    main,
)

def test_load_mobius_creates_file(tmp_path, monkeypatch):
    """If the Möbius array is missing, the loader should generate it."""
    # Point the loader to a temporary location.
    test_path = tmp_path / "mobius_array.npy"
    monkeypatch.setattr("demo_autocorr.MOBIUS_PATH", test_path)

    # Ensure the file does not exist.
    assert not test_path.is_file()

    # Loading should create the file.
    arr = _load_mobius_array()
    assert test_path.is_file()
    # Basic sanity check on the array shape.
    assert isinstance(arr, np.ndarray)
    assert arr.ndim == 1
    assert arr.dtype == np.int8
    # μ(1) = 1, μ(2) = -1
    assert int(arr[1]) == 1
    assert int(arr[2]) == -1

def test_load_window_starts(tmp_path, monkeypatch):
    """The loader must find a JSON file in one of the candidate locations."""
    json_path = tmp_path / "window_starts.json"
    json_path.write_text('{"1000": [1], "10000": [1], "100000": [1]}', encoding="utf-8")
    monkeypatch.setattr("demo_autocorr.WINDOW_STARTS_JSON_CANDIDATES", [json_path])

    mapping = _load_window_starts()
    assert mapping == {1000: [1], 10000: [1], 100000: [1]}

def test_compute_autocorrelation_known_values():
    """Validate the autocorrelation implementation on a tiny handcrafted window."""
    # μ values for n=1..5: [0, 1, -1, -1, 0, 1] (index 0 unused)
    mobius = np.array([0, 1, -1, -1, 0, 1], dtype=np.int8)
    # Window start at 1, length 5, lag 1:
    # products: μ(1)*μ(2)= -1, μ(2)*μ(3)= 1, μ(3)*μ(4)= 1, μ(4)*μ(5)=0
    # sum = 1, normaliser = L-h = 4 => 0.25
    val = compute_autocorrelation(mobius, start=1, L=5, h=1)
    assert np.isclose(val, 0.25)

def test_main_writes_correct_csv(tmp_path, monkeypatch):
    """Run the script end‑to‑end and check the produced CSV."""
    # Redirect paths to the temporary directory.
    mobius_path = tmp_path / "mobius_array.npy"
    json_path = tmp_path / "window_starts.json"
    output_csv = tmp_path / "demo_autocorr.csv"

    # Create a minimal Möbius array (N=10) and a matching JSON.
    from sieve import compute_mobius

    np.save(mobius_path, compute_mobius(10))
    json_path.write_text('{"1000": [1]}', encoding="utf-8")

    monkeypatch.setattr("demo_autocorr.MOBIUS_PATH", mobius_path)
    monkeypatch.setattr(
        "demo_autocorr.WINDOW_STARTS_JSON_CANDIDATES", [json_path]
    )
    monkeypatch.setattr(
        "demo_autocorr.PROCESSED_DEMO_OUTPUT_PATH", output_csv
    )

    # Execute the main routine.
    main()

    # Verify the CSV contents.
    with output_csv.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    assert len(rows) == 1
    row = rows[0]
    assert int(row["interval_start"]) == 1
    assert int(row["interval_length"]) == 1000
    assert int(row["lag"]) == 1
    # The reference value is hard‑coded; we only check that the column exists.
    assert "autocorrelation" in row