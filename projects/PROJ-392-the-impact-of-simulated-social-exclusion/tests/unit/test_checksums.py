"""
Unit tests for code/utils/checksums.py
"""

import json
import os
import tempfile
from pathlib import Path

import pytest

from code.utils.checksums import (
    compute_file_checksum,
    generate_checksum_manifest,
    verify_checksums,
    verify_single_file,
)


class TestComputeFileChecksum:
    def test_compute_sha256(self, tmp_path):
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")

        checksum = compute_file_checksum(test_file, "sha256")
        assert len(checksum) == 64  # SHA256 produces 64 hex chars
        assert isinstance(checksum, str)

    def test_compute_md5(self, tmp_path):
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")

        checksum = compute_file_checksum(test_file, "md5")
        assert len(checksum) == 32  # MD5 produces 32 hex chars

    def test_file_not_found(self, tmp_path):
        non_existent = tmp_path / "does_not_exist.txt"
        with pytest.raises(FileNotFoundError):
            compute_file_checksum(non_existent)

    def test_invalid_algorithm(self, tmp_path):
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")
        with pytest.raises(ValueError):
            compute_file_checksum(test_file, "invalid_algo")


class TestGenerateChecksumManifest:
    def test_generate_manifest(self, tmp_path):
        # Create test files
        (tmp_path / "file1.txt").write_text("content1")
        (tmp_path / "subdir").mkdir()
        (tmp_path / "subdir" / "file2.txt").write_text("content2")

        manifest = generate_checksum_manifest(tmp_path)

        assert "file1.txt" in manifest
        assert "subdir/file2.txt" in manifest
        assert len(manifest) == 2

    def test_generate_manifest_with_extensions(self, tmp_path):
        (tmp_path / "file1.txt").write_text("content1")
        (tmp_path / "file2.nii.gz").write_text("nifti content")

        manifest = generate_checksum_manifest(tmp_path, extensions=[".nii.gz"])

        assert "file1.txt" not in manifest
        assert "file2.nii.gz" in manifest
        assert len(manifest) == 1

    def test_generate_manifest_to_file(self, tmp_path):
        (tmp_path / "file1.txt").write_text("content1")
        output_path = tmp_path / "manifest.json"

        generate_checksum_manifest(tmp_path, output_path=output_path)

        assert output_path.exists()
        with open(output_path, "r") as f:
            loaded = json.load(f)
        assert "file1.txt" in loaded

    def test_directory_not_found(self, tmp_path):
        non_existent = tmp_path / "does_not_exist"
        with pytest.raises(FileNotFoundError):
            generate_checksum_manifest(non_existent)


class TestVerifyChecksums:
    def test_verify_all_valid(self, tmp_path):
        # Create files and manifest
        (tmp_path / "file1.txt").write_text("content1")
        (tmp_path / "file2.txt").write_text("content2")

        manifest_path = tmp_path / "manifest.json"
        generate_checksum_manifest(tmp_path, output_path=manifest_path)

        all_valid, failed = verify_checksums(tmp_path, manifest_path)

        assert all_valid is True
        assert failed == {}

    def test_verify_missing_file(self, tmp_path):
        (tmp_path / "file1.txt").write_text("content1")

        manifest_path = tmp_path / "manifest.json"
        generate_checksum_manifest(tmp_path, output_path=manifest_path)

        # Delete the file
        (tmp_path / "file1.txt").unlink()

        all_valid, failed = verify_checksums(tmp_path, manifest_path)

        assert all_valid is False
        assert "file1.txt" in failed
        assert failed["file1.txt"] == "missing"

    def test_verify_checksum_mismatch(self, tmp_path):
        (tmp_path / "file1.txt").write_text("content1")

        manifest_path = tmp_path / "manifest.json"
        generate_checksum_manifest(tmp_path, output_path=manifest_path)

        # Modify the file
        (tmp_path / "file1.txt").write_text("modified content")

        all_valid, failed = verify_checksums(tmp_path, manifest_path)

        assert all_valid is False
        assert "file1.txt" in failed
        assert failed["file1.txt"] == "mismatch"

    def test_manifest_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            verify_checksums(tmp_path, tmp_path / "nonexistent.json")


class TestVerifySingleFile:
    def test_verify_match(self, tmp_path):
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello")

        checksum = compute_file_checksum(test_file)
        assert verify_single_file(test_file, checksum) is True

    def test_verify_mismatch(self, tmp_path):
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello")

        wrong_checksum = "a" * 64
        assert verify_single_file(test_file, wrong_checksum) is False

    def test_case_insensitive(self, tmp_path):
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello")

        checksum = compute_file_checksum(test_file)
        assert verify_single_file(test_file, checksum.upper()) is True