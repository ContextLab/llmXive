"""Unit tests for code/utils/checksums.py (T007)."""
import hashlib
import json
import sys
from pathlib import Path

import pytest

CODE_DIR = Path(__file__).resolve().parent.parent / "code"
sys.path.insert(0, str(CODE_DIR))

from utils.checksums import (  # noqa: E402
    batch_update_state_files,
    compute_directory_checksums,
    compute_sha256,
    iter_files,
    load_state_file,
    update_state_file,
    verify_file_integrity,
    verify_manifest,
    write_manifest,
)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@pytest.fixture
def sample_tree(tmp_path):
    (tmp_path / "sub").mkdir()
    (tmp_path / "a.txt").write_bytes(b"hello world\n")
    (tmp_path / "sub" / "b.bin").write_bytes(b"\x00\x01\x02" * 1000)
    return tmp_path


def test_compute_sha256_matches_hashlib(sample_tree):
    fp = sample_tree / "a.txt"
    assert compute_sha256(fp) == _sha256_bytes(b"hello world\n")


def test_compute_sha256_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        compute_sha256(tmp_path / "nope.txt")


def test_compute_sha256_large_file_streaming(tmp_path):
    fp = tmp_path / "big.bin"
    data = bytes(range(256)) * 4096  # 1 MiB, spans multiple chunks
    fp.write_bytes(data)
    assert compute_sha256(fp) == _sha256_bytes(data)


def test_compute_directory_checksums_recursive(sample_tree):
    cs = compute_directory_checksums(sample_tree)
    assert set(cs.keys()) == {"a.txt", "sub/b.bin"} or set(cs.keys()) == {
        str(sample_tree / "a.txt"),
        str(sample_tree / "sub" / "b.bin"),
    }
    assert cs[list(cs)[0]]


def test_compute_directory_checksums_relative_to(sample_tree):
    cs = compute_directory_checksums(sample_tree, relative_to=sample_tree)
    assert set(cs.keys()) == {"a.txt", "sub/b.bin"}
    assert cs["a.txt"] == _sha256_bytes(b"hello world\n")


def test_compute_directory_checksums_non_recursive(sample_tree):
    cs = compute_directory_checksums(sample_tree, recursive=False)
    assert set(cs.keys()) == {"a.txt"}


def test_iter_files_excludes_pycache(sample_tree):
    (sample_tree / "__pycache__").mkdir()
    (sample_tree / "__pycache__" / "x.pyc").write_bytes(b"junk")
    files = iter_files(sample_tree)
    names = {f.name for f in files}
    assert "x.pyc" not in names
    assert {"a.txt", "b.bin"} <= names


def test_verify_file_integrity(sample_tree):
    fp = sample_tree / "a.txt"
    good = _sha256_bytes(b"hello world\n")
    assert verify_file_integrity(fp, good)
    assert not verify_file_integrity(fp, "0" * 64)
    assert not verify_file_integrity(sample_tree / "missing.txt", good)


def test_state_file_roundtrip(tmp_path):
    state = {"data/raw": {"checksums": {"f.nii.gz": "abc"}}}
    sp = tmp_path / "state.json"
    update_state_file({}, state, save=True, state_path=sp)
    loaded = load_state_file(sp)
    assert loaded == {"data/raw": {"checksums": {"f.nii.gz": "abc"}}}


def test_load_state_file_missing_returns_empty(tmp_path):
    assert load_state_file(tmp_path / "absent.json") == {}


def test_load_state_file_corrupt_raises(tmp_path):
    sp = tmp_path / "bad.json"
    sp.write_text("{not json")
    with pytest.raises(ValueError):
        load_state_file(sp)


def test_update_state_file_requires_path_when_saving():
    with pytest.raises(ValueError):
        update_state_file({}, {"d": {"f": "h"}}, save=True, state_path=None)


def test_batch_update_state_files(tmp_path):
    s1 = tmp_path / "s1.json"
    s2 = tmp_path / "s2.json"
    results = batch_update_state_files(
        [s1, s2], {"dir": {"file.txt": "deadbeef"}}
    )
    assert results[str(s1)] is True and results[str(s2)] is True
    assert load_state_file(s1)["dir"]["checksums"]["file.txt"] == "deadbeef"


def test_write_manifest_and_verify(sample_tree):
    manifest = tmp_path / "checksums.txt"
    entries = write_manifest([sample_tree], manifest, root=tmp_path)
    assert manifest.exists()
    assert json.loads(manifest.read_text()) == entries
    assert set(entries) == {"a.txt", "sub/b.bin"}

    results = verify_manifest(manifest, root=tmp_path)
    assert all(results.values())

    # Tamper with a file -> verification fails
    (sample_tree / "a.txt").write_bytes(b"tampered")
    results = verify_manifest(manifest, root=tmp_path)
    assert results["a.txt"] is False
    assert results["sub/b.bin"] is True