import hashlib
import os
from pathlib import Path
import pytest
from datasets import load_dataset
from llmxive_toolkit import paths

def test_pi_bench_downloaded():
    """
    Verify that the pi-Bench dataset has been downloaded into data/raw.
    """
    raw_dir: Path = paths.data("raw")
    assert raw_dir.is_dir(), f"Raw data directory {raw_dir} does not exist."

    # Check for JSON files
    json_files = list(raw_dir.glob("*.json"))
    assert len(json_files) >= 1, f"Expected at least 1 JSON file in {raw_dir}, found {len(json_files)}."

    # Check checksum manifest
    checksum_file = raw_dir / "checksums.txt"
    assert checksum_file.is_file(), f"Checksum manifest {checksum_file} missing."

    # Verify checksums in manifest match files on disk
    with checksum_file.open("r", encoding="utf-8") as f:
        lines = f.readlines()
        assert len(lines) > 0, "Checksum manifest is empty."
        for line in lines:
            line = line.strip()
            if not line: continue
            try:
                expected_hash, rel_path_str = line.split("  ", 1)
                file_path = raw_dir / rel_path_str
                assert file_path.is_file(), f"File {rel_path_str} listed in manifest not found."
                
                h = hashlib.sha256()
                with file_path.open("rb") as fb:
                    for chunk in iter(lambda: fb.read(8192), b""):
                        h.update(chunk)
                assert h.hexdigest() == expected_hash, f"Hash mismatch for {rel_path_str}"
            except ValueError:
                pytest.fail(f"Malformed line in checksum manifest: {line}")

    # Verify loadable via datasets
    # Note: The stubbed datasets library supports the 'json' format for local files.
    try:
        dataset = load_dataset("json", data_files=str(raw_dir / "*.json"), trust_remote_code=True)
        assert dataset is not None
    except Exception as e:
        pytest.fail(f"Failed to load downloaded files via datasets.load_dataset: {e}")