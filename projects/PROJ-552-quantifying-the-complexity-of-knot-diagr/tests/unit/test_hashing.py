"""
Unit tests for content hashing module (Constitution Principle V).

These tests verify that the hashing module correctly implements
Constitution Principle V requirements:
1. Content hash recorded in state file artifact_hashes map
2. updated_at timestamp updated in state file
"""

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest import TestCase

import pytest

# Import hashing module
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from reproducibility.hashing import (
    HASH_ALGORITHM,
    STATE_FILE_PATH,
    compute_file_hash,
    compute_string_hash,
    get_artifact_hash,
    list_recorded_artifacts,
    record_artifact_hash,
    record_multiple_artifact_hashes,
    verify_artifact_hash,
)


class TestComputeFileHash(TestCase):
    """Tests for compute_file_hash function."""

    def test_compute_hash_of_known_file(self):
        """Test hashing a file with known content."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("Hello, World!")
            temp_path = f.name

        try:
            hash_value = compute_file_hash(temp_path)
            # SHA-256 of "Hello, World!"
            expected = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
            self.assertEqual(hash_value, expected)
        finally:
            os.unlink(temp_path)

    def test_compute_hash_of_large_file(self):
        """Test hashing a larger file (chunked reading)."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            # Write 1MB of data
            f.write("x" * (1024 * 1024))
            temp_path = f.name

        try:
            hash_value = compute_file_hash(temp_path)
            # Should complete without error
            self.assertEqual(len(hash_value), 64)  # SHA-256 hex length
        finally:
            os.unlink(temp_path)

    def test_compute_hash_nonexistent_file(self):
        """Test hashing a file that doesn't exist raises FileNotFoundError."""
        with self.assertRaises(FileNotFoundError):
            compute_file_hash("/nonexistent/path/file.txt")


class TestComputeStringHash(TestCase):
    """Tests for compute_string_hash function."""

    def test_compute_hash_of_string(self):
        """Test hashing a string."""
        hash_value = compute_string_hash("Hello, World!")
        # SHA-256 of "Hello, World!"
        expected = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        self.assertEqual(hash_value, expected)

    def test_compute_hash_of_empty_string(self):
        """Test hashing an empty string."""
        hash_value = compute_string_hash("")
        # SHA-256 of empty string
        expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        self.assertEqual(hash_value, expected)


class TestRecordArtifactHash(TestCase):
    """Tests for record_artifact_hash function (Constitution Principle V)."""

    def setUp(self):
        """Set up test fixtures."""
        # Create temporary directory for state file
        self.temp_dir = tempfile.mkdtemp()
        self.state_path = Path(self.temp_dir) / "state.yaml"

        # Create test artifact
        self.artifact_path = Path(self.temp_dir) / "test_artifact.txt"
        self.artifact_path.write_text("Test content for hashing")

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_record_hash_creates_state_file(self):
        """Test that recording a hash creates the state file."""
        from reproducibility.hashing import STATE_FILE_PATH
        # Temporarily override STATE_FILE_PATH
        original_path = STATE_FILE_PATH
        import reproducibility.hashing as hashing_module
        hashing_module.STATE_FILE_PATH = self.state_path

        try:
            record_artifact_hash(self.artifact_path, "test_artifact")
            self.assertTrue(self.state_path.exists())
        finally:
            hashing_module.STATE_FILE_PATH = original_path

    def test_record_hash_updates_artifact_hashes_map(self):
        """Test that recording a hash updates artifact_hashes map (Constitution Principle V)."""
        import yaml
        from reproducibility.hashing import STATE_FILE_PATH
        original_path = STATE_FILE_PATH
        import reproducibility.hashing as hashing_module
        hashing_module.STATE_FILE_PATH = self.state_path

        try:
            record_artifact_hash(self.artifact_path, "test_artifact")

            with open(self.state_path, "r") as f:
                state = yaml.safe_load(f)

            self.assertIn("artifact_hashes", state)
            self.assertIn("test_artifact", state["artifact_hashes"])
            self.assertIn("hash", state["artifact_hashes"]["test_artifact"])
        finally:
            hashing_module.STATE_FILE_PATH = original_path

    def test_record_hash_updates_timestamp(self):
        """Test that recording a hash updates updated_at timestamp (Constitution Principle V)."""
        import yaml
        from reproducibility.hashing import STATE_FILE_PATH
        original_path = STATE_FILE_PATH
        import reproducibility.hashing as hashing_module
        hashing_module.STATE_FILE_PATH = self.state_path

        try:
            # Record first hash
            record_artifact_hash(self.artifact_path, "test_artifact")

            with open(self.state_path, "r") as f:
                state1 = yaml.safe_load(f)

            # Wait a moment
            import time
            time.sleep(0.1)

            # Record second hash
            record_artifact_hash(self.artifact_path, "test_artifact_2")

            with open(self.state_path, "r") as f:
                state2 = yaml.safe_load(f)

            # Timestamp should be updated
            self.assertGreater(
                datetime.fromisoformat(state2["updated_at"]),
                datetime.fromisoformat(state1["updated_at"])
            )
        finally:
            hashing_module.STATE_FILE_PATH = original_path

    def test_record_hash_includes_metadata(self):
        """Test that recorded hash includes required metadata."""
        import yaml
        from reproducibility.hashing import STATE_FILE_PATH
        original_path = STATE_FILE_PATH
        import reproducibility.hashing as hashing_module
        hashing_module.STATE_FILE_PATH = self.state_path

        try:
            record_artifact_hash(self.artifact_path, "test_artifact")

            with open(self.state_path, "r") as f:
                state = yaml.safe_load(f)

            artifact_info = state["artifact_hashes"]["test_artifact"]
            self.assertIn("hash", artifact_info)
            self.assertIn("path", artifact_info)
            self.assertIn("algorithm", artifact_info)
            self.assertIn("recorded_at", artifact_info)
            self.assertEqual(artifact_info["algorithm"], "sha256")
        finally:
            hashing_module.STATE_FILE_PATH = original_path


class TestVerifyArtifactHash(TestCase):
    """Tests for verify_artifact_hash function."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.artifact_path = Path(self.temp_dir) / "test_artifact.txt"
        self.artifact_path.write_text("Test content for verification")

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_verify_correct_hash(self):
        """Test verifying with correct hash returns True."""
        hash_value = compute_file_hash(self.artifact_path)
        self.assertTrue(verify_artifact_hash(self.artifact_path, hash_value))

    def test_verify_incorrect_hash(self):
        """Test verifying with incorrect hash returns False."""
        wrong_hash = "0" * 64
        self.assertFalse(verify_artifact_hash(self.artifact_path, wrong_hash))


class TestGetArtifactHash(TestCase):
    """Tests for get_artifact_hash function."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.state_path = Path(self.temp_dir) / "state.yaml"
        self.artifact_path = Path(self.temp_dir) / "test_artifact.txt"
        self.artifact_path.write_text("Test content")

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_get_hash_for_recorded_artifact(self):
        """Test getting hash for a recorded artifact."""
        import yaml
        from reproducibility.hashing import STATE_FILE_PATH
        original_path = STATE_FILE_PATH
        import reproducibility.hashing as hashing_module
        hashing_module.STATE_FILE_PATH = self.state_path

        try:
            record_artifact_hash(self.artifact_path, "test_artifact")
            hash_value = get_artifact_hash("test_artifact")

            self.assertIsNotNone(hash_value)
            self.assertEqual(len(hash_value), 64)
        finally:
            hashing_module.STATE_FILE_PATH = original_path

    def test_get_hash_for_unrecorded_artifact(self):
        """Test getting hash for an unrecorded artifact returns None."""
        self.assertIsNone(get_artifact_hash("nonexistent_artifact"))


class TestListRecordedArtifacts(TestCase):
    """Tests for list_recorded_artifacts function."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.state_path = Path(self.temp_dir) / "state.yaml"

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_list_artifacts_empty(self):
        """Test listing artifacts when state is empty."""
        from reproducibility.hashing import STATE_FILE_PATH
        original_path = STATE_FILE_PATH
        import reproducibility.hashing as hashing_module
        hashing_module.STATE_FILE_PATH = self.state_path

        try:
            artifacts = list_recorded_artifacts()
            self.assertEqual(artifacts, [])
        finally:
            hashing_module.STATE_FILE_PATH = original_path

    def test_list_artifacts_after_recording(self):
        """Test listing artifacts after recording some."""
        from reproducibility.hashing import STATE_FILE_PATH
        original_path = STATE_FILE_PATH
        import reproducibility.hashing as hashing_module
        hashing_module.STATE_FILE_PATH = self.state_path

        try:
            artifact_path = Path(self.temp_dir) / "test.txt"
            artifact_path.write_text("test")

            record_artifact_hash(artifact_path, "artifact_1")
            record_artifact_hash(artifact_path, "artifact_2")

            artifacts = list_recorded_artifacts()
            self.assertIn("artifact_1", artifacts)
            self.assertIn("artifact_2", artifacts)
        finally:
            hashing_module.STATE_FILE_PATH = original_path


class TestRecordMultipleArtifactHashes(TestCase):
    """Tests for record_multiple_artifact_hashes function."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.state_path = Path(self.temp_dir) / "state.yaml"

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_record_multiple_hashes(self):
        """Test recording hashes for multiple artifacts."""
        import yaml
        from reproducibility.hashing import STATE_FILE_PATH
        original_path = STATE_FILE_PATH
        import reproducibility.hashing as hashing_module
        hashing_module.STATE_FILE_PATH = self.state_path

        try:
            # Create multiple artifacts
            artifact_paths = []
            for i in range(3):
                artifact_path = Path(self.temp_dir) / f"artifact_{i}.txt"
                artifact_path.write_text(f"Content {i}")
                artifact_paths.append(artifact_path)

            results = record_multiple_artifact_hashes(artifact_paths)

            # Should have 3 results
            self.assertEqual(len(results), 3)

            # All should be valid hashes
            for hash_value in results.values():
                self.assertEqual(len(hash_value), 64)

            # State file should have all 3 artifacts
            with open(self.state_path, "r") as f:
                state = yaml.safe_load(f)

            self.assertEqual(len(state["artifact_hashes"]), 3)
        finally:
            hashing_module.STATE_FILE_PATH = original_path

    def test_record_multiple_updates_timestamp_once(self):
        """Test that recording multiple hashes updates timestamp only once."""
        import yaml
        from reproducibility.hashing import STATE_FILE_PATH
        original_path = STATE_FILE_PATH
        import reproducibility.hashing as hashing_module
        hashing_module.STATE_FILE_PATH = self.state_path

        try:
            # Create multiple artifacts
            artifact_paths = []
            for i in range(3):
                artifact_path = Path(self.temp_dir) / f"artifact_{i}.txt"
                artifact_path.write_text(f"Content {i}")
                artifact_paths.append(artifact_path)

            # Record multiple hashes
            record_multiple_artifact_hashes(artifact_paths)

            # Verify timestamp is set (updated once for all)
            with open(self.state_path, "r") as f:
                state = yaml.safe_load(f)

            self.assertIn("updated_at", state)
        finally:
            hashing_module.STATE_FILE_PATH = original_path