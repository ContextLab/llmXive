"""
Unit tests for the download module (T002).

These tests verify that the checksum function computes a SHA256 hash
correctly and that the checksum manifest line formatting is as expected.
They do **not** trigger the full dataset download (which would require
network access and large files); instead they operate on a tiny temporary
file.
"""

import hashlib
import os
import tempfile

import pytest

from download import compute_sha256, append_checksum_record, CHECKSUMS_FILE

def test_compute_sha256_known_content():
    # Known content and its SHA256 hash (computed externally)
    content = b"llmxive test content"
    expected_hash = hashlib.sha256(content).hexdigest()

    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        result_hash = compute_sha256(Path(tmp_path))
        assert result_hash == expected_hash
    finally:
        os.remove(tmp_path)

def test_append_checksum_record_creates_manifest(tmp_path):
    # Ensure a clean manifest file in a temporary directory
    manifest_path = tmp_path / "sha256_manifest.txt"
    # Patch the module-level constant to point to our temp file
    original_manifest = CHECKSUMS_FILE
    try:
        # Monkey‑patch the constant
        download.CHECKSUMS_FILE = manifest_path

        # Append a dummy record
        append_checksum_record("dummy_key", "dummy_file.csv", "abc123def456")
        # Verify file content
        content = manifest_path.read_text().strip()
        assert content == "dummy_key,dummy_file.csv,abc123def456"
    finally:
        # Restore original constant
        download.CHECKSUMS_FILE = original_manifest