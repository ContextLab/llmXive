"""
Unit test for the T002 download & preprocessing pipeline.

The test runs the ``code/main.py`` entry point with the
``download_preprocess`` stage and then checks that the expected
artefacts exist:

* At least one parcellated time‑series CSV under
  ``data/processed/parcellated/``.
* ``data/checksums.txt`` is populated.
* ``data/processed/neuro_features.csv`` exists.
"""

import os
import pathlib

import pytest

from llmxive_toolkit import paths

@pytest.mark.timeout(300)
def test_download_preprocess_runs(tmp_path, monkeypatch):
    # Ensure a clean environment by resetting the project directories.
    # The helper ``paths`` creates directories on demand, so we just
    # invoke the script.
    import subprocess

    # Run the pipeline stage.
    result = subprocess.run(
        ["python", "code/main.py", "--stage", "download_preprocess"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, f"Pipeline failed: {result.stderr}"

    # Check that at least one parcellated CSV exists.
    parcellated_dir = paths.data("processed", "parcellated")
    csv_files = list(parcellated_dir.glob("*.csv"))
    assert csv_files, "No parcellated time‑series CSVs were created."

    # Check that the checksum file exists and is non‑empty.
    checksums_path = paths.data("checksums.txt")
    assert checksums_path.is_file(), "checksums.txt not found."
    assert checksums_path.stat().st_size > 0, "checksums.txt is empty."

    # Check that the neuro_features placeholder CSV exists.
    neuro_features_path = paths.data("processed", "neuro_features.csv")
    assert neuro_features_path.is_file(), "neuro_features.csv not found."