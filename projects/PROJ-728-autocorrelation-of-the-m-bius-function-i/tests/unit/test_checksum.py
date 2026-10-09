import hashlib
from pathlib import Path

import pytest

# Import the module we just created.
from code.checksum import _sha256_of_file, compute_checksums, MANIFEST_PATH, RAW_DATA_DIR

def test_sha256_of_file(tmp_path: Path):
    # Create a temporary file with known contents.
    data = b"OpenAI"
    file_path = tmp_path / "sample.txt"
    file_path.write_bytes(data)

    expected = hashlib.sha256(data).hexdigest()
    assert _sha256_of_file(file_path) == expected

def test_compute_checksums_creates_manifest(tmp_path: Path, monkeypatch):
    # Set up a temporary raw data directory with two files.
    raw_dir = tmp_path / "data" / "raw"
    raw_dir.mkdir(parents=True)
    file1 = raw_dir / "a.npy"
    file2 = raw_dir / "b.json"
    file1.write_bytes(b"abc")
    file2.write_bytes(b"def")

    # Patch the module-level paths to point to the temporary locations.
    monkeypatch.setattr("code.checksum.RAW_DATA_DIR", raw_dir, raising=False)
    manifest_path = tmp_path / "data" / "checksums" / "manifest.sha256"
    monkeypatch.setattr("code.checksum.MANIFEST_PATH", manifest_path, raising=False)

    # Run the checksum computation.
    compute_checksums()

    # Verify manifest exists and contains two lines.
    assert manifest_path.is_file()
    lines = manifest_path.read_text().strip().splitlines()
    assert len(lines) == 2

    # Verify each line matches the expected format and checksum.
    expected1 = hashlib.sha256(b"abc").hexdigest()
    expected2 = hashlib.sha256(b"def").hexdigest()
    expected_paths = {file1.as_posix(), file2.as_posix()}
    seen_paths = set()
    for line in lines:
        checksum, rel_path = line.split("  ")
        assert checksum in {expected1, expected2}
        seen_paths.add(rel_path)
    assert seen_paths == expected_paths