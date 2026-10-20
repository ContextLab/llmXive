import hashlib
from pathlib import Path
import pytest
from datasets import load_dataset
from llmxive_toolkit import paths

def test_pi_bench_downloaded():
    """
    Verify that the π‑Bench dataset has been downloaded into ``data/raw``.
    The test checks:
    1. The raw directory exists.
    2. At least one file is present.
    3. A checksum manifest (checksums.txt) exists and its entries match.
    4. The data can be loaded via datasets.load_dataset.
    """
    raw_dir: Path = paths.data("raw")
    assert raw_dir.is_dir(), f"Raw data directory {raw_dir} does not exist."

    # Count all files (excluding directories) inside the raw directory
    all_files = [p for p in raw_dir.rglob("*") if p.is_file()]
    assert len(all_files) >= 1, (
        f"Expected at least 1 file in {raw_dir}, found {len(all_files)}."
    )

    checksum_file = raw_dir / "checksums.txt"
    assert checksum_file.is_file(), f"Checksum manifest {checksum_file} missing."

    # Load checksum manifest and verify each entry
    with checksum_file.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                expected_hash, rel_path_str = line.split("  ", 1)
                file_path = raw_dir / rel_path_str
                assert file_path.is_file(), f"File listed in checksum manifest not found: {file_path}"
                
                # Compute actual hash
                h = hashlib.sha256()
                with file_path.open("rb") as fb:
                    for chunk in iter(lambda: fb.read(8192), b""):
                        h.update(chunk)
                actual_hash = h.hexdigest()
                assert actual_hash == expected_hash, (
                    f"Checksum mismatch for {rel_path_str}: expected {expected_hash}, got {actual_hash}"
                )
            except ValueError:
                pytest.fail(f"Malformed line in checksum manifest: {line}")

    # Verification: assert successful load via datasets using local JSON files
    # This avoids relying on the Hub's dataset loader which may be misconfigured
    try:
        # Search for any JSON files in the raw directory
        json_files = list(raw_dir.rglob("*.json"))
        if not json_files:
            pytest.fail("No JSON files found in data/raw for verification.")
        
        dataset = load_dataset("json", data_files=str(raw_dir / "**/*.json"), recursive=True)
        assert dataset is not None
    except Exception as e:
        pytest.fail(f"Failed to load downloaded pi-bench files via datasets.load_dataset: {e}")