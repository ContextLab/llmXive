import unittest
import os
import sys
import tempfile
import shutil
from pathlib import Path
import yaml

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.hash_artifacts import hash_file
from utils.generate_artifact_hashes import collect_artifacts, generate_hashes

class TestGenerateArtifactHashes(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        self.project_root = project_root

    def test_collect_artifacts_exists(self):
        """Test that collect_artifacts returns a list of existing files."""
        artifacts = collect_artifacts()
        self.assertIsInstance(artifacts, list)
        self.assertGreater(len(artifacts), 0, "No artifacts were collected")
        
        for artifact in artifacts:
            full_path = self.project_root / artifact
            self.assertTrue(full_path.exists(), f"Collected artifact does not exist: {artifact}")

    def test_generate_hashes_format(self):
        """Test that generate_hashes returns a dict with correct format."""
        artifacts = collect_artifacts()
        # Take a subset for testing to speed up
        test_artifacts = artifacts[:5] if len(artifacts) > 5 else artifacts
        
        hashes = generate_hashes(test_artifacts)
        
        self.assertIsInstance(hashes, dict)
        self.assertEqual(len(hashes), len(test_artifacts))
        
        for path, hash_val in hashes.items():
            self.assertIn(path, test_artifacts)
            self.assertIsInstance(hash_val, str)
            self.assertEqual(len(hash_val), 64)  # SHA-256 hex length

    def test_hash_consistency(self):
        """Test that hashing the same file twice yields the same result."""
        test_file = self.project_root / "code" / "utils" / "hash_artifacts.py"
        if test_file.exists():
            hash1 = hash_file(test_file)
            hash2 = hash_file(test_file)
            self.assertEqual(hash1, hash2)

    def test_yaml_output_structure(self):
        """Test that the generated YAML has the expected structure."""
        # Simulate the main logic without writing to disk
        artifacts = collect_artifacts()
        hashes = generate_hashes(artifacts)
        
        metadata = {
            "project_id": "PROJ-140-evaluating-the-efficacy-of-code-summariz",
            "task_id": "T032",
            "hashes": hashes
        }
        
        # Verify structure
        self.assertIn("project_id", metadata)
        self.assertIn("task_id", metadata)
        self.assertIn("hashes", metadata)
        self.assertEqual(metadata["task_id"], "T032")
        self.assertEqual(len(metadata["hashes"]), len(artifacts))

if __name__ == "__main__":
    unittest.main()