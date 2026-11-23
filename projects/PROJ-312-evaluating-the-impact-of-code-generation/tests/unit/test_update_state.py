"""
Unit tests for T037: update_state.py functionality.
"""
import hashlib
import os
import tempfile
from pathlib import Path
from unittest import TestCase, mock

import yaml

# Import the module under test
from code.update_state import compute_file_hash, load_current_state, update_state_with_artifacts

class TestComputeFileHash(TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_file = Path(self.temp_dir.name) / "test.txt"
        self.test_content = b"Hello, World!"
        self.test_file.write_bytes(self.test_content)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_compute_sha256_hash(self):
        """Test that compute_file_hash returns correct SHA-256 hash."""
        expected_hash = hashlib.sha256(self.test_content).hexdigest()
        actual_hash = compute_file_hash(self.test_file)
        self.assertEqual(actual_hash, expected_hash)

    def test_compute_hash_large_file(self):
        """Test hashing a larger file."""
        large_content = b"x" * 10000
        self.test_file.write_bytes(large_content)
        expected_hash = hashlib.sha256(large_content).hexdigest()
        actual_hash = compute_file_hash(self.test_file)
        self.assertEqual(actual_hash, expected_hash)

    def test_compute_hash_missing_file(self):
        """Test that missing file raises FileNotFoundError."""
        missing_file = Path(self.temp_dir.name) / "nonexistent.txt"
        with self.assertRaises(FileNotFoundError):
            compute_file_hash(missing_file)

class TestLoadCurrentState(TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.state_file = Path(self.temp_dir.name) / "state.yaml"
        self.original_state_dir = Path("state/projects/PROJ-312-evaluating-the-impact-of-code-generation")
        # Mock the STATE_DIR to use temp directory
        self.mock_state_dir = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    @mock.patch('code.update_state.STATE_FILE')
    def test_load_existing_state(self, mock_state_file):
        """Test loading an existing state file."""
        mock_state_file.exists.return_value = True
        mock_state_file.read_text.return_value = "key: value"
        
        # We need to mock the yaml.safe_load as well
        with mock.patch('code.update_state.yaml.safe_load', return_value={"key": "value"}):
            state = load_current_state()
            self.assertEqual(state, {"key": "value"})

    @mock.patch('code.update_state.STATE_FILE')
    def test_load_nonexistent_state(self, mock_state_file):
        """Test loading when state file doesn't exist."""
        mock_state_file.exists.return_value = False
        state = load_current_state()
        self.assertEqual(state, {})

    @mock.patch('code.update_state.STATE_FILE')
    def test_load_corrupt_state(self, mock_state_file):
        """Test loading a corrupt state file."""
        mock_state_file.exists.return_value = True
        mock_state_file.read_text.return_value = "invalid: yaml: content"
        
        with mock.patch('code.update_state.yaml.safe_load', side_effect=yaml.YAMLError("test error")):
            state = load_current_state()
            self.assertEqual(state, {})

class TestUpdateStateWithArtifacts(TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.artifact1 = Path(self.temp_dir.name) / "artifact1.txt"
        self.artifact2 = Path(self.temp_dir.name) / "artifact2.txt"
        self.artifact1.write_text("content1")
        self.artifact2.write_text("content2")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_update_with_existing_artifacts(self):
        """Test updating state with existing artifacts."""
        state = {}
        artifact_paths = [
            str(self.artifact1),
            str(self.artifact2)
        ]
        
        # Temporarily modify the module's ARTIFACTS_TO_TRACK
        import code.update_state as update_state_module
        original_artifacts = update_state_module.ARTIFACTS_TO_TRACK
        update_state_module.ARTIFACTS_TO_TRACK = artifact_paths
        
        try:
            updated_state = update_state_with_artifacts(state)
            
            self.assertIn("artifacts", updated_state)
            self.assertIn(str(self.artifact1), updated_state["artifacts"])
            self.assertIn(str(self.artifact2), updated_state["artifacts"])
            self.assertTrue(updated_state["artifacts"][str(self.artifact1)]["exists"])
            self.assertTrue(updated_state["artifacts"][str(self.artifact2)]["exists"])
            self.assertIsNotNone(updated_state["artifacts"][str(self.artifact1)]["hash"])
            self.assertIsNotNone(updated_state["updated_at"])
        finally:
            update_state_module.ARTIFACTS_TO_TRACK = original_artifacts

    def test_update_with_missing_artifacts(self):
        """Test updating state with missing artifacts."""
        state = {}
        missing_path = "/nonexistent/path/file.txt"
        artifact_paths = [missing_path]
        
        import code.update_state as update_state_module
        original_artifacts = update_state_module.ARTIFACTS_TO_TRACK
        update_state_module.ARTIFACTS_TO_TRACK = artifact_paths
        
        try:
            updated_state = update_state_with_artifacts(state)
            
            self.assertIn(missing_path, updated_state["artifacts"])
            self.assertFalse(updated_state["artifacts"][missing_path]["exists"])
            self.assertIsNone(updated_state["artifacts"][missing_path]["hash"])
        finally:
            update_state_module.ARTIFACTS_TO_TRACK = original_artifacts

    def test_update_increments_counters(self):
        """Test that artifact and missing counters are correct."""
        state = {}
        artifact_paths = [
            str(self.artifact1),
            "/nonexistent/file.txt"
        ]
        
        import code.update_state as update_state_module
        original_artifacts = update_state_module.ARTIFACTS_TO_TRACK
        update_state_module.ARTIFACTS_TO_TRACK = artifact_paths
        
        try:
            updated_state = update_state_with_artifacts(state)
            
            self.assertEqual(updated_state["artifact_count"], 1)
            self.assertEqual(updated_state["missing_count"], 1)
        finally:
            update_state_module.ARTIFACTS_TO_TRACK = original_artifacts
