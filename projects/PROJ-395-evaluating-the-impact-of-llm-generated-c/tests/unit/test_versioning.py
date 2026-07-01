"""
Unit tests for code/versioning.py artifact versioning logic.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest import TestCase

from code.versioning import (
    compute_file_hash,
    discover_artifacts,
    compute_artifact_hashes,
    load_existing_manifest,
    save_manifest,
    verify_artifact_integrity,
    update_state_manifest,
    generate_version_report,
)


class TestComputeFileHash(TestCase):
    def test_hash_of_known_file(self):
        """Test hashing a file with known content."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("Hello, World!")
            temp_path = Path(f.name)

        try:
            hash_val = compute_file_hash(temp_path)
            self.assertIsNotNone(hash_val)
            self.assertEqual(len(hash_val), 64)  # SHA-256 hex digest length
            # Verify it's a valid hex string
            int(hash_val, 16)
        finally:
            temp_path.unlink()

    def test_hash_of_nonexistent_file(self):
        """Test hashing a file that doesn't exist."""
        hash_val = compute_file_hash(Path("/nonexistent/path/file.txt"))
        self.assertIsNone(hash_val)

    def test_hash_of_empty_file(self):
        """Test hashing an empty file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            temp_path = Path(f.name)

        try:
            hash_val = compute_file_hash(temp_path)
            self.assertIsNotNone(hash_val)
            # SHA-256 of empty string
            expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
            self.assertEqual(hash_val, expected)
        finally:
            temp_path.unlink()

class TestDiscoverArtifacts(TestCase):
    def test_discover_artifacts_in_temp_dir(self):
        """Test artifact discovery in a temporary directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Create some files
            (tmp_path / "file1.py").write_text("print(1)")
            (tmp_path / "file2.csv").write_text("a,b\n1,2")
            (tmp_path / "file3.txt").write_text("text")
            (tmp_path / "file4.json").write_text("{}")
            (tmp_path / "ignore.log").write_text("log")  # Should be ignored

            # Create subdirectory
            subdir = tmp_path / "subdir"
            subdir.mkdir()
            (subdir / "nested.py").write_text("print(2)")

            artifacts = discover_artifacts(tmp_path)

            self.assertEqual(len(artifacts), 5)
            paths = [str(a.name) for a in artifacts]
            self.assertIn("file1.py", paths)
            self.assertIn("file2.csv", paths)
            self.assertIn("file3.txt", paths)
            self.assertIn("file4.json", paths)
            self.assertIn("nested.py", paths)
            self.assertNotIn("ignore.log", paths)

    def test_discover_artifacts_empty_dir(self):
        """Test artifact discovery in an empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            artifacts = discover_artifacts(Path(tmpdir))
            self.assertEqual(len(artifacts), 0)

    def test_discover_artifacts_nonexistent_dir(self):
        """Test artifact discovery in a non-existent directory."""
        artifacts = discover_artifacts(Path("/nonexistent"))
        self.assertEqual(len(artifacts), 0)

class TestComputeArtifactHashes(TestCase):
    def test_compute_hashes_for_specific_files(self):
        """Test computing hashes for a list of specific files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            file1 = tmp_path / "file1.py"
            file1.write_text("print(1)")

            file2 = tmp_path / "file2.py"
            file2.write_text("print(2)")

            hashes = compute_artifact_hashes(specific_files=[file1, file2])

            self.assertEqual(len(hashes), 2)
            # Keys should contain the file names
            self.assertTrue(any("file1.py" in k for k in hashes.keys()))
            self.assertTrue(any("file2.py" in k for k in hashes.keys()))

class TestManifestOperations(TestCase):
    def test_load_nonexistent_manifest(self):
        """Test loading a manifest that doesn't exist."""
        manifest = load_existing_manifest(Path("/nonexistent/manifest.json"))
        self.assertEqual(manifest["version"], "1.0")
        self.assertEqual(manifest["artifacts"], {})

    def test_save_and_load_manifest(self):
        """Test saving and loading a manifest."""
        with tempfile.TemporaryDirectory() as tmpdir:
          tmp_path = Path(tmpdir)
          manifest_path = tmp_path / "test_manifest.json"

          artifacts = {"file1.py": "abc123", "file2.csv": "def456"}
          metadata = {"test": "value", "count": 42}

          saved_path = save_manifest(artifacts, metadata, manifest_path)

          self.assertTrue(saved_path.exists())

          loaded = load_existing_manifest(saved_path)
          self.assertEqual(loaded["artifacts"], artifacts)
          self.assertEqual(loaded["metadata"]["test"], "value")
          self.assertEqual(loaded["metadata"]["count"], 42)
          self.assertIn("generated_at", loaded["metadata"])

class TestVerifyIntegrity(TestCase):
    def test_verify_all_ok(self):
        """Test verification when all artifacts match."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Create a file
            test_file = tmp_path / "test.py"
            test_file.write_text("print(1)")

            # Create manifest with correct hash
            hash_val = compute_file_hash(test_file)
            artifacts = {str(test_file): hash_val}
            manifest_path = tmp_path / "manifest.json"
            save_manifest(artifacts, manifest_path=manifest_path)

            valid, details = verify_artifact_integrity(manifest_path)

            self.assertTrue(valid)
            self.assertEqual(details[str(test_file)], "OK")

    def test_verify_missing_file(self):
        """Test verification when a file is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Create manifest referencing non-existent file
            artifacts = {"nonexistent.py": "abc123"}
            manifest_path = tmp_path / "manifest.json"
            save_manifest(artifacts, manifest_path=manifest_path)

            valid, details = verify_artifact_integrity(manifest_path)

            self.assertFalse(valid)
            self.assertEqual(details["nonexistent.py"], "MISSING")

    def test_verify_hash_mismatch(self):
        """Test verification when hash doesn't match."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Create a file
            test_file = tmp_path / "test.py"
            test_file.write_text("print(1)")

            # Create manifest with WRONG hash
            artifacts = {str(test_file): "wronghash000000000000000000000000000000000000000000000000000"}
            manifest_path = tmp_path / "manifest.json"
            save_manifest(artifacts, manifest_path=manifest_path)

            valid, details = verify_artifact_integrity(manifest_path)

            self.assertFalse(valid)
            self.assertIn("HASH_MISMATCH", details[str(test_file)])

class TestGenerateVersionReport(TestCase):
    def test_report_with_artifacts(self):
        """Test report generation with artifacts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            manifest_path = tmp_path / "manifest.json"

            artifacts = {"file1.py": "abc123", "file2.csv": "def456"}
            save_manifest(artifacts, manifest_path=manifest_path)

            report = generate_version_report(manifest_path)

            self.assertIn("Artifact Version Report", report)
            self.assertIn("file1.py", report)
            self.assertIn("file2.csv", report)
            self.assertIn("abc123", report)

    def test_report_empty(self):
        """Test report generation with no artifacts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            manifest_path = tmp_path / "manifest.json"

            save_manifest({}, manifest_path=manifest_path)

            report = generate_version_report(manifest_path)
            self.assertIn("No artifacts recorded.", report)

class TestUpdateStateManifest(TestCase):
    def test_update_manifest(self):
        """Test full update workflow."""
        # This test creates a temporary state/data structure
        # and verifies the update process works end-to-end
        import shutil

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Create mock state and data directories
            state_dir = tmp_path / "state"
            data_dir = tmp_path / "data"
            state_dir.mkdir()
            data_dir.mkdir()

            # Create some files
            (state_dir / "config.json").write_text("{}")
            (data_dir / "results.csv").write_text("a,b\n1,2")

            # Patch the config functions to use our temp dirs
            import code.versioning as versioning_module

            original_get_state = versioning_module.get_state_dir
            original_get_data = versioning_module.get_data_dir

            versioning_module.get_state_dir = lambda: state_dir
            versioning_module.get_data_dir = lambda: data_dir

            try:
                manifest = update_state_manifest()

                self.assertIn("artifacts", manifest)
                self.assertGreater(len(manifest["artifacts"]), 0)
                self.assertIn("metadata", manifest)
                self.assertIn("generated_at", manifest["metadata"])
            finally:
                versioning_module.get_state_dir = original_get_state
                versioning_module.get_data_dir = original_get_data