"""
Tests for update_state.py
"""

import hashlib
import os
import tempfile
from pathlib import Path
from unittest import TestCase

import yaml

# Ensure we can import from code/utils
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.update_state import calculate_sha256, scan_artifacts, update_state_file


class TestUpdateState(TestCase):
    def setUp(self):
        """Create a temporary directory structure for testing."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_root = Path(self.temp_dir.name)

        # Create subdirectories mimicking project structure
        self.artifact_dir = self.test_root / "data" / "derived"
        self.artifact_dir.mkdir(parents=True)

        # Create a test file
        self.test_file = self.artifact_dir / "test_artifact.json"
        self.test_content = '{"key": "value", "number": 42}'
        self.test_file.write_text(self.test_content)

        # Create another file to test hashing consistency
        self.test_file2 = self.artifact_dir / "test_artifact2.csv"
        self.test_file2.write_text("a,b\n1,2")

    def tearDown(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()

    def test_calculate_sha256(self):
        """Test SHA-256 calculation is correct and consistent."""
        # Calculate hash manually
        expected_hash = hashlib.sha256(self.test_content.encode("utf-8")).hexdigest()

        # Calculate using our function
        actual_hash = calculate_sha256(self.test_file)

        self.assertEqual(actual_hash, expected_hash)

        # Verify consistency
        hash_again = calculate_sha256(self.test_file)
        self.assertEqual(actual_hash, hash_again)

    def test_scan_artifacts(self):
        """Test artifact scanning finds files correctly."""
        artifacts = scan_artifacts(self.test_root)

        # Should find both files
        self.assertEqual(len(artifacts), 2)

        # Check that paths are relative to test_root
        paths = [a["path"] for a in artifacts]
        self.assertTrue(any("test_artifact.json" in p for p in paths))
        self.assertTrue(any("test_artifact2.csv" in p for p in paths))

        # Check that hashes are present and valid length
        for artifact in artifacts:
            self.assertIn("sha256", artifact)
            self.assertEqual(len(artifact["sha256"]), 64)  # SHA-256 hex length

            # Check size is positive
            self.assertGreater(artifact["size_bytes"], 0)

    def test_update_state_file(self):
        """Test state file creation and content."""
        state_path = self.test_root / "state.yaml"

        # Create some artifacts
        artifacts = scan_artifacts(self.test_root)

        # Update state
        update_state_file(artifacts, state_path, pipeline_version="1.0.0")

        # Verify file exists
        self.assertTrue(state_path.exists())

        # Load and verify content
        with open(state_path, "r") as f:
            state = yaml.safe_load(f)

        self.assertIn("last_updated", state)
        self.assertEqual(state["artifact_count"], 2)
        self.assertEqual(state["pipeline_version"], "1.0.0")
        self.assertIn("artifacts", state)
        self.assertEqual(len(state["artifacts"]), 2)

    def test_update_state_file_idempotent(self):
        """Test that updating state multiple times is consistent."""
        state_path = self.test_root / "state.yaml"
        artifacts = scan_artifacts(self.test_root)

        # First update
        update_state_file(artifacts, state_path)
        with open(state_path, "r") as f:
            state1 = yaml.safe_load(f)

        # Second update (should overwrite)
        update_state_file(artifacts, state_path)
        with open(state_path, "r") as f:
            state2 = yaml.safe_load(f)

        # Artifacts and count should be identical
        self.assertEqual(state1["artifact_count"], state2["artifact_count"])
        self.assertEqual(len(state1["artifacts"]), len(state2["artifacts"]))

        # Hashes should match
        hashes1 = {a["path"]: a["sha256"] for a in state1["artifacts"]}
        hashes2 = {a["path"]: a["sha256"] for a in state2["artifacts"]}
        self.assertEqual(hashes1, hashes2)
