import hashlib
from pathlib import Path

import pytest
from llmxive_toolkit import paths

@pytest.mark.parametrize("expected_min_files", [1])
def test_pi_bench_downloaded(expected_min_files: int):
    """
    Verify that the π‑Bench dataset has been downloaded into ``data/raw``.
    The test checks:
    1. The raw directory exists.
    2. At least ``expected_min_files`` files are present (the dataset contains many files).
    3. A checksum manifest (checksums.txt) exists and its entries match the actual file contents.
    """
    raw_dir: Path = paths.data("raw")
    assert raw_dir.is_dir(), f"Raw data directory {raw_dir} does not exist."

    # Count all files (excluding directories) inside the raw directory
    all_files = [p for p in raw_dir.rglob("*") if p.is_file()]
    assert len(all_files) >= expected_min_files, (
        f"Expected at least {expected_min_files} files in {raw_dir}, "
        f"found {len(all_files)}."
    )

    checksum_file = raw_dir / "checksums.txt"
    assert checksum_file.is_file(), f"Checksum manifest {checksum_file} missing."

    # Load checksum manifest and verify each entry
    with checksum_file.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
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
                f"Checksum mismatch for {rel_path_str}: "
                f"expected {expected_hash}, got {actual_hash}"
            )
