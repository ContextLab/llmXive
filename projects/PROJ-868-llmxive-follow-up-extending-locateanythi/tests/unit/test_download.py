import hashlib
from pathlib import Path

import pytest

from code.data.download import (
    RAW_DATA_DIR,
    download_vrsbench,
    download_coco_val,
    download_refcoco_plus,
    sha256_of_file,
    verify_checksum,
)

@pytest.fixture(scope="module")
def raw_dir(tmp_path_factory):
    # Use a temporary directory for isolation
    return tmp_path_factory.mktemp("raw")

def test_download_and_checksum(tmp_path, monkeypatch):
    # Monkey‑patch the RAW_DATA_DIR to point to a temporary location
    monkeypatch.setattr("code.data.download.RAW_DATA_DIR", tmp_path)

    # Download each dataset (this will hit the real HuggingFace hub)
    download_vrsbench(tmp_path / "vrsbench.parquet")
    download_coco_val(tmp_path / "coco_val.parquet")
    download_refcoco_plus(tmp_path / "refcoco_plus.parquet")

    # Ensure files exist
    for name in ["vrsbench.parquet", "coco_val.parquet", "refcoco_plus.parquet"]:
        assert (tmp_path / name).exists()

    # Compute SHA‑256 hashes and verify that the verification function works
    for file_path in tmp_path.iterdir():
        # This will raise if the hash does not match (we use the same hash)
        expected = sha256_of_file(file_path)
        verify_checksum(file_path, expected)

    # Also test that a mismatched hash raises an AssertionError
    with pytest.raises(AssertionError):
        verify_checksum(tmp_path / "vrsbench.parquet", "deadbeef" * 8)