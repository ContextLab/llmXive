"""
Test suite for the strict data loader (code/data_loader.py).

The test runs the loader, then verifies that:
  * The raw CSV file exists.
  * The checksum file exists.
  * The checksum recorded in the file matches the actual SHA‑256 hash
    of the downloaded CSV.
"""
import hashlib
from pathlib import Path

import pytest

from llmxive_toolkit import paths
from code import data_loader

@pytest.mark.timeout(300)
def test_data_loader_execution(tmp_path, monkeypatch):
    """
    Execute the data loader and validate its outputs.
    """
    # Ensure the default data directories point inside the temporary directory
    # to avoid contaminating the repository data folder during the test run.
    # Monkey‑patch the paths.data function to redirect output.
    original_data = paths.data

    def redirected_data(*parts: str) -> Path:
        # Create a sub‑directory under the temporary path for each call.
        return Path(tmp_path, *parts)

    monkeypatch.setattr(paths, "data", redirected_data)

    # Run the loader
    data_loader.main()

    # Resolve the expected locations
    raw_csv = redirected_data("raw", "am_raw_data.csv")
    checksum_file = redirected_data("checksums", "am_raw_data.sha256")

    # Verify files exist
    assert raw_csv.is_file(), f"Raw CSV not found at {raw_csv}"
    assert checksum_file.is_file(), f"Checksum file not found at {checksum_file}"

    # Compute SHA‑256 of the CSV and compare to the stored checksum
    sha256 = hashlib.sha256()
    with open(raw_csv, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    computed_hash = sha256.hexdigest()

    stored_hash = checksum_file.read_text().strip()
    assert computed_hash == stored_hash, "Checksum mismatch between stored and computed hash."