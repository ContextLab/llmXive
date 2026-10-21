"""
Integration test for the download script.

This test ensures that the download script can:
1. Retrieve data from Wikidata.
2. Write the CSV to the expected location.
3. Compute and store a SHA‑256 checksum.
4. Pass the minimal schema validation.

The test is deliberately lightweight – it does not assert a particular
number of rows (the dataset size may change over time) but checks that
the output files exist and contain the required columns.
"""

import os
from pathlib import Path

import pandas as pd
import pytest

from data.download import (
    RAW_CSV_PATH,
    CHECKSUM_PATH,
    main,
    compute_sha256,
)

@pytest.mark.timeout(300)
def test_download_and_validation(tmp_path, monkeypatch):
    """
    Run the download script in an isolated temporary directory.
    The ``paths`` helper from ``llmxive_toolkit`` resolves paths relative
    to the project root, so we monkey‑patch the project root to the
    temporary directory to avoid polluting the real repository.
    """
    # Redirect the toolkit's root to the temporary directory.
    from llmxive_toolkit import paths as toolkit_paths

    monkeypatch.setattr(toolkit_paths, "root", tmp_path)

    # Re‑compute the derived paths after the root change.
    # (The module-level constants are evaluated at import time, so we
    # need to re‑import the module to pick up the new root.)
    import importlib

    import data.download as download_mod

    importlib.reload(download_mod)

    # Run the main routine – this will hit the live Wikidata endpoint.
    download_mod.main()

    # Verify that the CSV file was written.
    csv_path = download_mod.RAW_CSV_PATH
    assert csv_path.is_file(), f"CSV not found at {csv_path}"

    # Verify that the checksum file was written.
    checksum_path = download_mod.CHECKSUM_PATH
    assert checksum_path.is_file(), f"Checksum not found at {checksum_path}"

    # Load the CSV and ensure required columns are present.
    df = pd.read_csv(csv_path)
    assert "smiles" in df.columns
    assert "refractive_index" in df.columns
    assert len(df) > 0, "CSV is empty – no data was downloaded."

    # Verify that the stored checksum matches the file's actual checksum.
    stored_checksum = checksum_path.read_text().strip()
    actual_checksum = compute_sha256(csv_path)
    assert stored_checksum == actual_checksum, "Checksum mismatch."

    # Clean‑up is handled automatically by the pytest tmp_path fixture.