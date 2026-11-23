"""
Integration test for the Devign dataset downloader.

The test runs the downloader's ``main`` function and checks that:
1. The CSV file ``data/raw/devign/devign.csv`` exists.
2. The checksum file ``data/checksums.json`` exists.
3. The checksum mapping contains an entry for the CSV file.
"""
import json
from pathlib import Path

import pytest

from code.download_devign import main, CSV_DEST, CHECKSUMS_PATH

@pytest.mark.timeout(600)
def test_download_and_checksum(tmp_path, monkeypatch):
    """
    Run the downloader and verify output artifacts.

    The test is allowed up to 10 minutes because downloading the zip may take
    a few seconds on a fresh runner.  The ``tmp_path`` fixture is not used
    directly; the downloader writes to the project‑relative ``data/`` directory,
    which is safe in the isolated CI environment.
    """
    # Ensure a clean start: remove any existing artifacts if present.
    if CSV_DEST.is_file():
        CSV_DEST.unlink()
    if CHECKSUMS_PATH.is_file():
        CHECKSUMS_PATH.unlink()

    # Execute the download workflow.
    main()

    # Verify that the CSV was created.
    assert CSV_DEST.is_file(), f"Expected CSV at {CSV_DEST} but it does not exist."

    # Verify that the checksums file was created and contains the CSV entry.
    assert CHECKSUMS_PATH.is_file(), "checksums.json was not created."

    checksums = json.loads(CHECKSUMS_PATH.read_text(encoding="utf-8"))
    csv_key = str(CSV_DEST)
    assert csv_key in checksums, f"Checksum entry for {csv_key} missing in checksums.json."

    # Verify that the recorded checksum matches the actual file checksum.
    from code.download_devign import compute_sha256

    actual_checksum = compute_sha256(CSV_DEST)
    assert checksums[csv_key] == actual_checksum, "Recorded checksum does not match actual file checksum."