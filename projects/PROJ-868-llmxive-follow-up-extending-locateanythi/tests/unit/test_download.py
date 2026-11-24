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
    return tmp_path_factory.mktemp("raw")

def test_download_and_checksum(tmp_path, monkeypatch):
    # Mock the RAW_DATA_DIR to point to a temporary location
    monkeypatch.setattr("code.data.download.RAW_DATA_DIR", tmp_path)

    # Download each dataset
    download_vrsbench(tmp_path / "vrsbench.parquet")
    download_coco_val(tmp_path / "coco_val.parquet")
    download_refcoco_plus(tmp_path / "refcoco_plus.parquet")

    # Ensure files exist
    for name in ["vrsbench.parquet", "coco_val.parquet", "refcoco_plus.parquet"]:
        assert (tmp_path / name).exists()

    # Test that the checksum logic itself is correct
    for file_path in tmp_path.iterdir():
        expected = sha256_of_file(file_path)
        verify_checksum(file_path, expected)

    # Test that a mismatched hash raises an AssertionError
    with pytest.raises(AssertionError):
        verify_checksum(tmp_path / "vrsbench.parquet", "deadbeef" * 8)