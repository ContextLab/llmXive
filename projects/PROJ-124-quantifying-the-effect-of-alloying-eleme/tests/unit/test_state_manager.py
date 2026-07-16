"""
Unit tests for state_manager module.

Tests Constitution Principle V: Artifact Hash Tracking.
"""
import os
import tempfile
from pathlib import Path
from unittest import TestCase

import yaml

from code.utils.state_manager import (
    compute_sha256,
    update_artifact_hash,
    verify_artifact_integrity,
)


class TestStateManager(TestCase):
    """Tests for the state_manager module."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = Path(self.temp_dir) / "test_artifact.txt"
        self.test_content = "This is a test artifact for hash verification."
        
        # Create test file
        self.test_file.write_text(self.test_content)
        
        # Ensure state directory exists for tests
        self.state_dir = Path("state")
        self.state_dir.mkdir(exist_ok=True)

    def tearDown(self):
        """Clean up test artifacts."""
        # Remove test file
        if self.test_file.exists():
            self.test_file.unlink()
        
        # Clean up state directory if created for test
        hash_file = self.state_dir / "artifact_hashes.yaml"
        if hash_file.exists():
            # Load and remove our test entry
            try:
                with open(hash_file, "r") as f:
                    data = yaml.safe_load(f) or {}
                if str(self.test_file) in data:
                    del data[str(self.test_file)]
                    with open(hash_file, "w") as f:
                        yaml.dump(data, f)
            except Exception:
                # If cleanup fails, just remove the file
                hash_file.unlink()

    def test_compute_sha256_basic(self):
        """Test basic SHA-256 computation."""
        hash_result = compute_sha256(self.test_file)
        
        # SHA-256 produces 64 hex characters
        self.assertEqual(len(hash_result), 64)
        self.assertTrue(all(c in "0123456789abcdef" for c in hash_result))

    def test_compute_sha256_deterministic(self):
        """Test that SHA-256 is deterministic."""
        hash1 = compute_sha256(self.test_file)
        hash2 = compute_sha256(self.test_file)
        
        self.assertEqual(hash1, hash2)

    def test_compute_sha256_content_sensitivity(self):
        """Test that different content produces different hashes."""
        # Create a second file with different content
        test_file2 = Path(self.temp_dir) / "test_artifact2.txt"
        test_file2.write_text("Different content")
        
        hash1 = compute_sha256(self.test_file)
        hash2 = compute_sha256(test_file2)
        
        self.assertNotEqual(hash1, hash2)
        test_file2.unlink()

    def test_update_artifact_hash_creates_file(self):
        """Test that update_artifact_hash creates the hash file."""
        # Remove hash file if it exists
        hash_file = self.state_dir / "artifact_hashes.yaml"
        if hash_file.exists():
            hash_file.unlink()
        
        update_artifact_hash(str(self.test_file))
        
        self.assertTrue(hash_file.exists())

    def test_update_artifact_hash_stores_correct_hash(self):
        """Test that the stored hash matches the computed hash."""
        expected_hash = compute_sha256(self.test_file)
        update_artifact_hash(str(self.test_file))
        
        hash_file = self.state_dir / "artifact_hashes.yaml"
        with open(hash_file, "r") as f:
            stored_data = yaml.safe_load(f)
        
        stored_hash = stored_data[str(self.test_file)]["hash"]
        self.assertEqual(stored_hash, expected_hash)

    def test_update_artifact_hash_updates_existing(self):
        """Test that updating an existing artifact updates the hash."""
        # First update
        update_artifact_hash(str(self.test_file))
        
        # Modify the file
        self.test_file.write_text("Modified content")
        new_hash = compute_sha256(self.test_file)
        
        # Second update
        update_artifact_hash(str(self.test_file))
        
        # Verify new hash is stored
        hash_file = self.state_dir / "artifact_hashes.yaml"
        with open(hash_file, "r") as f:
            stored_data = yaml.safe_load(f)
        
        stored_hash = stored_data[str(self.test_file)]["hash"]
        self.assertEqual(stored_hash, new_hash)

    def test_verify_artifact_integrity_success(self):
        """Test successful integrity verification."""
        update_artifact_hash(str(self.test_file))
        
        result = verify_artifact_integrity(str(self.test_file))
        
        self.assertTrue(result)

    def test_verify_artifact_integrity_failure(self):
        """Test integrity verification fails when content changes."""
        update_artifact_hash(str(self.test_file))
        
        # Modify the file
        self.test_file.write_text("Modified content")
        
        result = verify_artifact_integrity(str(self.test_file))
        
        self.assertFalse(result)

    def test_verify_artifact_integrity_with_expected_hash(self):
        """Test verification with explicitly provided expected hash."""
        expected_hash = compute_sha256(self.test_file)
        
        result = verify_artifact_integrity(str(self.test_file), expected_hash)
        
        self.assertTrue(result)

    def test_update_artifact_hash_nonexistent_file(self):
        """Test that updating a nonexistent file raises FileNotFoundError."""
        nonexistent = Path(self.temp_dir) / "nonexistent.txt"
        
        with self.assertRaises(FileNotFoundError):
            update_artifact_hash(str(nonexistent))

    def test_verify_artifact_integrity_nonexistent_file(self):
        """Test that verifying a nonexistent file raises FileNotFoundError."""
        nonexistent = Path(self.temp_dir) / "nonexistent.txt"
        
        with self.assertRaises(FileNotFoundError):
            verify_artifact_integrity(str(nonexistent))

    def test_verify_artifact_integrity_no_stored_hash(self):
        """Test verification fails when no hash is stored."""
        # Don't call update_artifact_hash first
        with self.assertRaises(FileNotFoundError):
            verify_artifact_integrity(str(self.test_file))
