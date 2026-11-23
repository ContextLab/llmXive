"""
Unit tests for the exact int64 cross‑validation (Constitution VI).

The test suite imports the ``cross_validate_autocorrelation`` module
and runs its ``main`` function on the *real* Möbius data generated
by the earlier tasks.  The function performs the exhaustive check
for all windows and lags; if any discrepancy is found it raises an
exception, which causes the test to fail.

The test does **not** assert a particular numeric value for the
maximum relative error – it only verifies that the script runs to
completion and writes the expected entries into
``data/processed/pipeline_status.json``.
"""

import json
from pathlib import Path

import pytest

# Import the script (it registers a ``main`` function).
from cross_validate_autocorrelation import main as cross_validate_main

PIPELINE_STATUS = Path("data/processed/pipeline_status.json")

@pytest.mark.usefixtures("tmp_path_factory")
def test_cross_validation_completes():
    # Ensure a clean status file before running.
    if PIPELINE_STATUS.is_file():
        PIPELINE_STATUS.unlink()

    # Run the cross‑validation; any exception propagates as a test failure.
    cross_validate_main()

    # After successful run the JSON file must exist and contain the expected keys.
    assert PIPELINE_STATUS.is_file(), "pipeline_status.json was not created"

    with PIPELINE_STATUS.open("r", encoding="utf-8") as f:
        status = json.load(f)

    assert "autocorrelation_crosscheck" in status, "Missing crosscheck section"
    cross = status["autocorrelation_crosscheck"]
    assert isinstance(cross.get("n_pairs_checked"), int) and cross["n_pairs_checked"] > 0
    assert isinstance(cross.get("max_relative_error"), float)
    # The relative error should be within the prescribed tolerance.
    assert cross["max_relative_error"] < 1e-9, "Relative error exceeds tolerance"