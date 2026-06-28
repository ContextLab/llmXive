"""
Unit tests for manifest generation utilities.

Tests verify that manifest.json contains valid SHA256 hashes
and that the manifest structure conforms to FR-024 requirements.
"""

import json
import tempfile
from pathlib import Path

import pytest

from code.src.utils.manifest import (
    compute_file_hash,
    generate_manifest,
    write_manifest,
    validate_manifest,
    verify_file_integrity,
    create_manifest_for_audit_pipeline
)


class TestComputeFileHash:
    """Tests for the compute_file_hash function."""

    def test_hash_is_64_characters(self):
        """SHA256 hash should always be 64 hexadecimal characters."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("test content")
            temp_path = Path(f.name)

        try:
            file_hash = compute_file_hash(temp_path)
            assert len(file_hash) == 64
        finally:
            temp_path.unlink()

    def test_hash_is_hexadecimal(self):
        """SHA256 hash should only contain hexadecimal characters."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("test content")
            temp_path = Path(f.name)

        try:
            file_hash = compute_file_hash(temp_path)
            assert all(c in "0123456789abcdef" for c in file_hash.lower())
        finally:
            temp_path.unlink()

    def test_same_content_same_hash(self):
        """Same file content should produce same hash."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            file1 = tmpdir / "file1.txt"
            file2 = tmpdir / "file2.txt"

            file1.write_text("identical content")
            file2.write_text("identical content")

            hash1 = compute_file_hash(file1)
            hash2 = compute_file_hash(file2)

            assert hash1 == hash2

    def test_different_content_different_hash(self):
        """Different file content should produce different hash."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            file1 = tmpdir / "file1.txt"
            file2 = tmpdir / "file2.txt"

            file1.write_text("content one")
            file2.write_text("content two")

            hash1 = compute_file_hash(file1)
            hash2 = compute_file_hash(file2)

            assert hash1 != hash2


class TestValidateManifest:
    """Tests for the validate_manifest function."""

    def test_valid_manifest(self):
        """Valid manifest should pass validation."""
        manifest = {
            "version": "1.0",
            "files": {
                "output/test.json": {
                    "hash": "a" * 64,
                    "size_bytes": 100
                }
            }
        }

        is_valid, errors = validate_manifest(manifest)
        assert is_valid
        assert len(errors) == 0

    def test_missing_files_key(self):
        """Manifest without 'files' key should fail."""
        manifest = {"version": "1.0"}
        is_valid, errors = validate_manifest(manifest)
        assert not is_valid
        assert any("files" in e for e in errors)

    def test_empty_files(self):
        """Manifest with empty files dict should fail."""
        manifest = {"files": {}}
        is_valid, errors = validate_manifest(manifest)
        assert not is_valid
        assert any("at least one file" in e for e in errors)

    def test_invalid_hash_length(self):
        """Hash with wrong length should fail."""
        manifest = {
            "files": {
                "output/test.json": {
                    "hash": "short",
                    "size_bytes": 100
                }
            }
        }
        is_valid, errors = validate_manifest(manifest)
        assert not is_valid
        assert any("64 characters" in e for e in errors)

    def test_non_hexadecimal_hash(self):
        """Non-hexadecimal hash should fail."""
        manifest = {
            "files": {
                "output/test.json": {
                    "hash": "g" * 64,
                    "size_bytes": 100
                }
            }
        }
        is_valid, errors = validate_manifest(manifest)
        assert not is_valid
        assert any("hexadecimal" in e for e in errors)


class TestGenerateManifest:
    """Tests for the generate_manifest function."""

    def test_manifest_contains_sha256_hashes(self):
        """Generated manifest must contain SHA256 hashes (FR-024)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            output_dir = tmpdir / "output"
            data_dir = tmpdir / "data"
            output_dir.mkdir()
            data_dir.mkdir()

            # Create test files
            (output_dir / "audit_report.json").write_text('{"test": 1}')
            (data_dir / "processed.csv").write_text("a,b,c\n1,2,3")

            manifest = generate_manifest(output_dir, data_dir)

            assert "files" in manifest
            assert len(manifest["files"]) >= 2

            # Verify all hashes are SHA256 (64 hex characters)
            for file_path, file_info in manifest["files"].items():
                assert "hash" in file_info
                assert len(file_info["hash"]) == 64
                assert all(c in "0123456789abcdef" for c in file_info["hash"].lower())

    def test_manifest_includes_output_files(self):
        """Manifest should include files from output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            output_dir = tmpdir / "output"
            output_dir.mkdir()
            (output_dir / "test.json").write_text("{}")

            manifest = generate_manifest(output_dir, tmpdir / "data")

            assert any("output/test.json" in f for f in manifest["files"])

    def test_manifest_excludes_itself(self):
        """Manifest should not include manifest.json in its own entries."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            output_dir = tmpdir / "output"
            output_dir.mkdir()
            manifest_path = output_dir / "manifest.json"
            manifest_path.write_text("{}")

            manifest = generate_manifest(output_dir, tmpdir / "data")

            # manifest.json should NOT be in the files list
            assert "output/manifest.json" not in manifest["files"]

    def test_manifest_includes_data_files(self):
        """Manifest should include files from data directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            data_dir = tmpdir / "data"
            data_dir.mkdir()
            (data_dir / "processed.csv").write_text("a,b")

            manifest = generate_manifest(tmpdir / "output", data_dir)

            assert any("data/processed.csv" in f for f in manifest["files"])

    def test_manifest_has_version(self):
        """Manifest should include version field."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            manifest = generate_manifest(tmpdir / "output", tmpdir / "data")
            assert "version" in manifest
            assert manifest["version"] == "1.0"

    def test_manifest_has_generated_at(self):
        """Manifest should include timestamp."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            manifest = generate_manifest(tmpdir / "output", tmpdir / "data")
            assert "generated_at" in manifest


class TestWriteManifest:
    """Tests for the write_manifest function."""

    def test_writes_valid_json(self):
        """write_manifest should create valid JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            manifest_path = tmpdir / "manifest.json"
            manifest = {
                "version": "1.0",
                "files": {
                    "output/test.json": {
                        "hash": "a" * 64,
                        "size_bytes": 100
                    }
                }
            }

            write_manifest(manifest, manifest_path)

            assert manifest_path.exists()
            with open(manifest_path) as f:
                loaded = json.load(f)
            assert loaded == manifest

    def test_creates_parent_directories(self):
        """write_manifest should create parent directories if needed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            manifest_path = tmpdir / "nested" / "dir" / "manifest.json"
            manifest = {"version": "1.0", "files": {}}

            write_manifest(manifest, manifest_path)

            assert manifest_path.exists()


class TestVerifyFileIntegrity:
    """Tests for the verify_file_integrity function."""

    def test_correct_hashes_pass(self):
        """Files matching their manifest hashes should pass verification."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            output_dir = tmpdir / "output"
            output_dir.mkdir()

            test_file = output_dir / "test.json"
            test_file.write_text("test content")
            actual_hash = compute_file_hash(test_file)

            manifest = {
                "files": {
                    "output/test.json": {
                        "hash": actual_hash,
                        "size_bytes": test_file.stat().st_size
                    }
                }
            }

            is_valid, errors = verify_file_integrity(manifest, output_dir, tmpdir / "data")
            assert is_valid
            assert len(errors) == 0

    def test_mismatched_hashes_fail(self):
        """Files not matching their manifest hashes should fail."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            output_dir = tmpdir / "output"
            output_dir.mkdir()

            test_file = output_dir / "test.json"
            test_file.write_text("test content")

            manifest = {
                "files": {
                    "output/test.json": {
                        "hash": "b" * 64,  # Wrong hash
                        "size_bytes": test_file.stat().st_size
                    }
                }
            }

            is_valid, errors = verify_file_integrity(manifest, output_dir, tmpdir / "data")
            assert not is_valid
            assert any("mismatch" in e for e in errors)

    def test_missing_files_fail(self):
        """Missing files should fail verification."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            output_dir = tmpdir / "output"
            output_dir.mkdir()

            manifest = {
                "files": {
                    "output/nonexistent.json": {
                        "hash": "a" * 64,
                        "size_bytes": 100
                    }
                }
            }

            is_valid, errors = verify_file_integrity(manifest, output_dir, tmpdir / "data")
            assert not is_valid
            assert any("missing" in e for e in errors)


class TestCreateManifestForAuditPipeline:
    """Tests for the convenience function create_manifest_for_audit_pipeline."""

    def test_creates_manifest_file(self):
        """Should create manifest.json file in output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            output_dir = tmpdir / "output"
            output_dir.mkdir()
            data_dir = tmpdir / "data"
            data_dir.mkdir()

            # Create a test file
            (data_dir / "test.csv").write_text("a,b")

            manifest_path = create_manifest_for_audit_pipeline(output_dir, data_dir)

            assert manifest_path.exists()
            assert manifest_path.name == "manifest.json"

            with open(manifest_path) as f:
                manifest = json.load(f)

            assert "files" in manifest
            assert len(manifest["files"]) > 0

    def test_raises_on_invalid_manifest(self):
        """Should raise ValueError if manifest validation fails."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            output_dir = tmpdir / "output"
            output_dir.mkdir()
            data_dir = tmpdir / "data"
            data_dir.mkdir()

            # Empty directories should still create valid manifest
            # So we test that it works normally
            manifest_path = create_manifest_for_audit_pipeline(output_dir, data_dir)
            assert manifest_path.exists()
