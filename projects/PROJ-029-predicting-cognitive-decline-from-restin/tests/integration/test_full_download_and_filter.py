"""Integration test that runs the script end‑to‑end (network call)."""

import os
from pathlib import Path

import pytest

# The integration test may be skipped in CI environments without internet.
@pytest.mark.skipif(
    not os.getenv("RUN_INTEGRATION_TESTS"),
    reason="Integration test requires network access",
)
def test_script_produces_outputs(tmp_path):
    # Monkey‑patch the data directories to a temporary location
    raw_dir = tmp_path / "data" / "raw" / "ds000246"
    processed_dir = tmp_path / "data" / "processed"
    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(processed_dir, exist_ok=True)

    # Patch the module constants
    import importlib
    script = importlib.import_module("code.01_download_and_filter")
    script.RAW_ROOT = raw_dir
    script.PROCESSED_ROOT = processed_dir

    # Run main (will download the real participants.tsv)
    script.main()

    # Check outputs exist
    assert (processed_dir / "eligible_subjects.csv").is_file()
    assert (processed_dir / "excluded_subjects.log").is_file()