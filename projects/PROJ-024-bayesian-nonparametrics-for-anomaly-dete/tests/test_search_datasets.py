"""
Test for the dataset search script (T020).

This test runs the ``code/src/data/search_datasets.py`` script's ``main``
function and verifies that it completes without raising an exception.
Depending on network availability, the script may download one or both
verified datasets, or it may fall back to generating a *Validation
Deferred* report.  The test therefore accepts either outcome:

* At least one of the expected raw files exists under ``data/raw/``.
* Or the deferred report ``data/processed/results/validation_deferred.md``
  exists and contains the required heading.

The test does not mock network calls – it exercises the real download
logic, satisfying the requirement for real‑world data handling.
"""

import pathlib
import importlib

from llmxive_toolkit import paths

def test_search_datasets_execution(tmp_path, monkeypatch):
    """
    Run the search script and check for expected outputs.

    The script writes its outputs via ``paths.data`` which creates the
    appropriate directories under the project root.  No cleanup is
    required because the artefacts are part of the project's data
    directory.
    """
    # Import the module fresh to avoid side‑effects from previous imports
    search_module = importlib.import_module(
        "code.src.data.search_datasets"
    )
    # Execute the main routine
    search_module.main()

    # Expected raw filenames
    expected_raw_files = {
        "nab_realTraffic_1.csv",
        "physionet_mitdb_100.csv",
    }

    raw_dir = paths.data("raw")
    raw_files = {p.name for p in raw_dir.iterdir() if p.is_file()}

    # Check if any expected raw file was downloaded
    downloaded = expected_raw_files.intersection(raw_files)

    # Path to the deferred report
    deferred_report = paths.data(
        "processed",
        "results",
        "validation_deferred.md",
    )

    # Assert that either we have at least one downloaded file or a deferred report
    assert downloaded or deferred_report.exists(), (
        "Search script produced neither a dataset nor a deferred report."
    )

    # If the deferred report exists, verify its content
    if deferred_report.exists():
        content = deferred_report.read_text(encoding="utf-8")
        assert "# Validation Deferred Report" in content, (
            "Deferred report missing required heading."
        )
