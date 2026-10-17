"""
Unit test for the data download & checksum script.

The test verifies that:
  1. The script creates a `checksums.json` file.
  2. The manifest contains at least one entry for each expected dataset.
  3. Each listed shard file exists and its checksum matches the recorded value.
"""
import json
from pathlib import Path

import pytest
from llmxive_toolkit import paths


@pytest.fixture(scope="module")
def run_download():
    """Run the download script once for the test suite."""
    from code.data.download import main

    # Ensure a clean state
    raw_dir = paths.data("raw")
    if raw_dir.exists():
        for p in raw_dir.iterdir():
            p.unlink()
    raw_dir.mkdir(parents=True, exist_ok=True)

    # Execute the script (it will raise on failure)
    main()


def test_checksums_file_exists(run_download):
    checksums_path = paths.data("raw", "checksums.json")
    assert checksums_path.is_file(), "checksums.json was not created"


def test_manifest_structure(run_download):
    checksums_path = paths.data("raw", "checksums.json")
    with checksums_path.open() as f:
        manifest = json.load(f)

    # Expect entries for both datasets
    datasets = {entry["dataset"] for entry in manifest}
    assert "bigbench/hard" in datasets
    assert "bigbench/ethics" in datasets

    # Each entry must contain required keys
    required_keys = {"dataset", "shard_index", "filename", "checksum"}
    for entry in manifest:
        assert required_keys.issubset(entry.keys()), f"Missing keys in {entry}"


def test_shard_files_match_checksums(run_download):
    checksums_path = paths.data("raw", "checksums.json")
    with checksums_path.open() as f:
        manifest = json.load(f)

    for entry in manifest:
        shard_path = Path(entry["filename"])
        assert shard_path.is_file(), f"Shard file missing: {shard_path}"
        # Re‑compute checksum and compare
        with shard_path.open("rb") as f_shard:
            data = f_shard.read()
            import hashlib

            computed = hashlib.sha256(data).hexdigest()
        assert (
            computed == entry["checksum"]
        ), f"Checksum mismatch for {shard_path}"