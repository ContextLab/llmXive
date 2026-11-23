"""Unit tests for code/checksum_manager.py (T005b)."""

import sys
from pathlib import Path

CODE_DIR = Path(__file__).resolve().parents[2] / "code"
sys.path.insert(0, str(CODE_DIR))

from checksum_manager import calculate_sha256, generate_dataset_checksums  # noqa: E402


def test_calculate_sha256_known_vector(tmp_path):
    # SHA-256 of the empty file and of "hello\n" are well-known vectors.
    empty = tmp_path / "empty.bin"
    empty.write_bytes(b"")
    assert calculate_sha256(empty) == (
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    )

    hello = tmp_path / "hello.txt"
    hello.write_bytes(b"hello\n")
    assert calculate_sha256(hello) == (
        "5891b5b522d5df086d0ff0b110fbd9d21bb4fc7163af34d08286a2e846f6be03"
    )

def test_calculate_sha256_missing_file_raises(tmp_path):
    import pytest

    with pytest.raises(FileNotFoundError):
        calculate_sha256(tmp_path / "nope.bin")

def test_generate_dataset_checksums_real_files(tmp_path):
    # Uses real files written to disk (test fixtures, not fabricated data).
    (tmp_path / "a.dat").write_bytes(b"\x00\x01\x02")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "b.dat").write_bytes(b"\xff" * 10)

    checksums = generate_dataset_checksums(tmp_path)

    assert set(checksums.keys()) == {"a.dat", "sub/b.dat"}
    assert all(len(v) == 64 for v in checksums.values())
    # Checksums are deterministic.
    again = generate_dataset_checksums(tmp_path)
    assert checksums == again

def test_generate_dataset_checksums_empty_dir_raises(tmp_path):
    import pytest

    with pytest.raises(RuntimeError):
        generate_dataset_checksums(tmp_path)