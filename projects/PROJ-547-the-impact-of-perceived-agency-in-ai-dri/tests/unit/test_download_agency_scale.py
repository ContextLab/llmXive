"""Unit test for the agency scale download script."""

import hashlib
from pathlib import Path

import pytest

from code.data_acquisition.download_agency_scale import (
    DEST_FILE,
    EXPECTED_SHA256,
    compute_sha256,
)

@pytest.fixture(scope="module")
def downloaded_file(tmp_path_factory):
    """Run the download script once and provide the resulting file path."""
    # Use a temporary directory to avoid polluting the repository data folder.
    temp_dir = tmp_path_factory.mktemp("data_external")
    dest = temp_dir / DEST_FILE.name

    # Monkey‑patch the destination path inside the module.
    import importlib

    mod = importlib.import_module(
        "code.data_acquisition.download_agency_scale"
    )
    mod.DEST_DIR = temp_dir
    mod.DEST_FILE = dest

    # Execute the main function; it should download the file.
    mod.main()

    return dest

def test_checksum_matches(downloaded_file: Path):
    """Verify that the checksum of the downloaded file matches the expected value."""
    assert downloaded_file.exists()
    actual = compute_sha256(downloaded_file)
    assert actual.lower() == EXPECTED_SHA256.lower()