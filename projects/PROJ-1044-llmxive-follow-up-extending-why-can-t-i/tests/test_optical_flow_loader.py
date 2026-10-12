"""Unit tests for the optical-flow feature loader (T004)."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from src.data.optical_flow_loader import (
    _load_manifest,
    _sha256_of_file,
    copy_or_symlink,
    main,
)


def _write_npy(path: Path, payload: bytes = b"\x93NUMPY fake-free test bytes") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def test_sha256_of_file(tmp_path: Path) -> None:
    f = tmp_path / "a.npy"
    f.write_bytes(b"hello")
    assert _sha256_of_file(f) == hashlib.sha256(b"hello").hexdigest()


def test_load_manifest_missing_returns_empty(tmp_path: Path) -> None:
    assert _load_manifest(tmp_path / "nope.csv") == {}


def test_load_manifest_parses_lines(tmp_path: Path) -> None:
    m = tmp_path / "manifest.csv"
    m.write_text("flow_features/a.npy,abc123\n# comment\n\nflow_features/b.npy,def456\n")
    got = _load_manifest(m)
    assert got == {Path("flow_features/a.npy"): "abc123", Path("flow_features/b.npy"): "def456"}


def test_copy_files_and_verify_checksum(tmp_path: Path) -> None:
    src = tmp_path / "bundle" / "flow_features"
    _write_npy(src / "v1.npy", b"one")
    _write_npy(src / "v2.npy", b"two")
    dst = tmp_path / "out"

    manifest = {
        Path("flow_features/v1.npy"): hashlib.sha256(b"one").hexdigest(),
        Path("flow_features/v2.npy"): hashlib.sha256(b"two").hexdigest(),
    }
    n = copy_or_symlink(src, dst, manifest=manifest)
    assert n == 2
    assert (dst / "v1.npy").read_bytes() == b"one"
    assert (dst / "v2.npy").read_bytes() == b"two"


def test_checksum_mismatch_raises(tmp_path: Path) -> None:
    src = tmp_path / "bundle" / "flow_features"
    _write_npy(src / "v1.npy", b"one")
    dst = tmp_path / "out"
    manifest = {Path("flow_features/v1.npy"): "0" * 64}
    with pytest.raises(ValueError):
        copy_or_symlink(src, dst, manifest=manifest)


def test_missing_source_is_graceful(tmp_path: Path) -> None:
    dst = tmp_path / "out"
    n = copy_or_symlink(tmp_path / "does_not_exist", dst)
    assert n == 0
    assert dst.is_dir()
    assert list(dst.glob("*.npy")) == []


def test_symlink_mode(tmp_path: Path) -> None:
    src = tmp_path / "bundle" / "flow_features"
    _write_npy(src / "v1.npy", b"one")
    dst = tmp_path / "out"
    n = copy_or_symlink(src, dst, use_symlink=True)
    assert n == 1
    assert (dst / "v1.npy").is_symlink()
    assert (dst / "v1.npy").read_bytes() == b"one"


def test_main_exit_zero_with_missing_default_source(tmp_path: Path, monkeypatch) -> None:
    # main() with a non-existent source must exit 0 (graceful, no fabrication).
    rc = main(["--source", str(tmp_path / "missing_bundle")])
    assert rc == 0