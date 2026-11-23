"""
tests/unit/test_download_gwtc.py

Unit tests for the GWTC download script.
"""
import json
from pathlib import Path
import h5py
import pytest
from llmxive_toolkit import paths

@pytest.fixture(scope="module")
def downloaded_files():
    # Execute the download logic.
    from src.data.download import download_all
    download_all()
    return {
        "gwtc1": paths.data("raw", "gwtc1.h5"),
        "gwtc2": paths.data("raw", "gwtc2.h5"),
        "checksums": paths.data("raw", "checksums.json"),
    }

def test_files_exist(downloaded_files):
    assert downloaded_files["gwtc1"].exists(), "gwtc1.h5 was not created"
    assert downloaded_files["gwtc2"].exists(), "gwtc2.h5 was not created"
    assert downloaded_files["checksums"].exists(), "checksums.json missing"

def test_files_are_hdf5(downloaded_files):
    for key in ("gwtc1", "gwtc2"):
        path = downloaded_files[key]
        # h5py will raise an OSError if the file is not a valid HDF5 container
        with h5py.File(path, "r"):
            pass

def test_checksum_matches(downloaded_files):
    with open(downloaded_files["checksums"], "r", encoding="utf-8") as f:
        manifest = json.load(f)

    from src.utils.checksum import compute_file_hash

    for key, filename in (("gwtc1", "gwtc1.h5"), ("gwtc2", "gwtc2.h5")):
        path = downloaded_files[key]
        computed = compute_file_hash(str(path))
        recorded = manifest.get(filename)
        assert recorded is not None, f"No checksum entry for {filename}"
        assert computed == recorded, f"Checksum mismatch for {filename}: {computed} != {recorded}"