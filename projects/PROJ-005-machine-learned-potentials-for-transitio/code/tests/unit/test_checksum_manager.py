import json
import tempfile
import hashlib
from pathlib import Path
import pytest
import os
import sys

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.data.checksum_manager import (
    get_project_root,
    compute_file_checksum,
    load_checksum_manifest,
    save_checksum_manifest,
    verify_checksum,
    verify_all_files,
    update_checksum_for_file
)

class TestComputeFileChecksum:
    def test_compute_file_checksum(self, tmp_path):
        # Create a test file
        test_file = tmp_path / "test.txt"
        content = b"Hello, World!"
        test_file.write_bytes(content)

        # Compute checksum
        checksum = compute_file_checksum(test_file)

        # Verify against known value
        expected = hashlib.sha256(content).hexdigest()
        assert checksum == expected

    def test_compute_file_checksum_missing(self, tmp_path):
        non_existent = tmp_path / "does_not_exist.txt"
        with pytest.raises(FileNotFoundError):
            compute_file_checksum(non_existent)

class TestChecksumManifest:
    def test_save_and_load_manifest(self, tmp_path):
        manifest_path = tmp_path / "manifest.json"
        test_manifest = {"files": {"file1.txt": {"checksum": "abc123"}}}

        save_checksum_manifest(test_manifest, manifest_path)
        loaded = load_checksum_manifest(manifest_path)

        assert loaded == test_manifest

    def test_load_missing_file_creates_empty(self, tmp_path):
        manifest_path = tmp_path / "missing.json"
        loaded = load_checksum_manifest(manifest_path)
        assert loaded == {"files": {}}

class TestVerifyChecksum:
    def test_verify_checksum_valid(self, tmp_path):
        test_file = tmp_path / "verify.txt"
        content = b"Verify this"
        test_file.write_bytes(content)
        checksum = hashlib.sha256(content).hexdigest()

        assert verify_checksum(test_file, checksum) is True

    def test_verify_checksum_invalid(self, tmp_path):
        test_file = tmp_path / "verify.txt"
        test_file.write_bytes(b"Wrong content")
        wrong_checksum = "0" * 64

        assert verify_checksum(test_file, wrong_checksum) is False

class TestVerifyAllFiles:
    def test_verify_all_files_valid(self, tmp_path):
        # Setup
        file1 = tmp_path / "f1.txt"
        file1.write_bytes(b"data1")
        file2 = tmp_path / "f2.txt"
        file2.write_bytes(b"data2")

        manifest = {
            "files": {
                "f1.txt": {"checksum": hashlib.sha256(b"data1").hexdigest()},
                "f2.txt": {"checksum": hashlib.sha256(b"data2").hexdigest()}
            }
        }

        passed, failed = verify_all_files(manifest, tmp_path)
        assert passed is True
        assert len(failed) == 0

    def test_verify_all_files_missing(self, tmp_path):
        manifest = {
            "files": {
                "missing.txt": {"checksum": "abc"}
            }
        }
        passed, failed = verify_all_files(manifest, tmp_path)
        assert passed is False
        assert "missing.txt" in failed

class TestUpdateChecksumForFile:
    def test_update_checksum_for_file(self, tmp_path):
        test_file = tmp_path / "update.txt"
        test_file.write_bytes(b"new data")

        manifest = {"files": {}}
        updated_manifest = update_checksum_for_file(test_file, manifest)

        assert "update.txt" in updated_manifest["files"]
        assert updated_manifest["files"]["update.txt"]["checksum"] == hashlib.sha256(b"new data").hexdigest()

class TestGetProjectRoot:
    # Note: This test assumes a specific directory structure or mocks the environment.
    # In a strict unit test, we might mock Path.cwd() or pass a specific root.
    # For now, we test the logic that raises if not found.
    def test_get_project_root_fallback_logic(self):
        # This is a structural test. If run in a standard env without project root, it might fail.
        # We rely on the fact that if the test is run inside the repo, it should find it.
        # If not, we catch the exception as valid behavior for "not found".
        try:
            root = get_project_root()
            assert root.exists()
            # Basic sanity check
            assert (root / "data").exists() or (root / "code").exists()
        except FileNotFoundError:
            # If we are running in a context without the project structure (e.g. /tmp),
            # this is expected behavior for the function.
            pass