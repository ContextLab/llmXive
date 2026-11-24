"""Unit tests for T006a: verify_checksum.py"""
import hashlib
import json
import os
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from data.verify_checksum import (
    compute_sha256,
    load_manifest,
    verify_directory_integrity,
)


@pytest.fixture
def raw_dir(tmp_path):
    d = tmp_path / "raw"
    d.mkdir()
    return d


def _write_file(d, name, content=b"hello world"):
    p = d / name
    p.write_bytes(content)
    return p


def _write_manifest(d, entries):
    m = d / "sampled_manifest.json"
    m.write_text(json.dumps(entries))
    return m


def test_compute_sha256_matches_hashlib(tmp_path):
    p = tmp_path / "f.bin"
    p.write_bytes(b"abc")
    assert compute_sha256(p) == hashlib.sha256(b"abc").hexdigest()


def test_load_manifest_missing_raises(raw_dir):
    with pytest.raises(FileNotFoundError):
        load_manifest(raw_dir / "sampled_manifest.json")


def test_load_manifest_malformed_raises(raw_dir):
    (raw_dir / "sampled_manifest.json").write_text(json.dumps({"not": "a list"}))
    with pytest.raises(ValueError):
        load_manifest(raw_dir / "sampled_manifest.json")


def test_load_manifest_empty_raises(raw_dir):
    (raw_dir / "sampled_manifest.json").write_text("[]")
    with pytest.raises(ValueError):
        load_manifest(raw_dir / "sampled_manifest.json")


def test_verify_ok(raw_dir):
    p = _write_file(raw_dir, "sampled_scenes.jsonl", b"scene data")
    manifest = [{"file": "sampled_scenes.jsonl", "sha256": compute_sha256(p)}]
    _write_manifest(raw_dir, manifest)
    assert verify_directory_integrity(raw_dir, manifest) is True


def test_verify_mismatch_fails(raw_dir):
    p = _write_file(raw_dir, "sampled_scenes.jsonl", b"scene data")
    manifest = [{"file": "sampled_scenes.jsonl", "sha256": "0" * 64}]
    _write_manifest(raw_dir, manifest)
    assert verify_directory_integrity(raw_dir, manifest) is False


def test_verify_missing_file_fails(raw_dir):
    manifest = [{"file": "ghost.jsonl", "sha256": "0" * 64}]
    _write_manifest(raw_dir, manifest)
    assert verify_directory_integrity(raw_dir, manifest) is False


def test_verify_no_files_found_fails(tmp_path):
    d = tmp_path / "empty"
    d.mkdir()
    manifest = [{"file": "ghost.jsonl", "sha256": "0" * 64}]
    assert verify_directory_integrity(d, manifest) is False