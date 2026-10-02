"""
Tests for the State Manager module.
"""
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code root to path for imports
code_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(code_root))

from utils.state_manager import (
    calculate_sha256, 
    load_state_file, 
    save_state_file, 
    update_project_state,
    get_project_root,
    scan_directory_for_hashes
)

class TestStateManager(unittest.TestCase):
    """Test cases for the State Manager."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = Path(self.temp_dir.name)
        
        # Create mock project structure
        self.mock_project_root = self.test_dir / "project"
        self.mock_project_root.mkdir()
        (self.mock_project_root / "code").mkdir()
        (self.mock_project_root / "data").mkdir()
        (self.mock_project_root / "state").mkdir()
        
        # Create a test file
        self.test_file = self.mock_project_root / "code" / "test.txt"
        self.test_file.write_text("Hello, World!")

    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def test_calculate_sha256(self):
        """Test SHA-256 calculation for a known string."""
        # Create a temporary file with known content
        test_content = b"test content for hashing"
        test_file = self.test_dir / "hash_test.txt"
        test_file.write_bytes(test_content)
        
        hash_result = calculate_sha256(test_file)
        
        # Verify it's a valid hex string of correct length
        self.assertEqual(len(hash_result), 64)
        self.assertTrue(all(c in '0123456789abcdef' for c in hash_result))
        
        # Verify determinism
        hash_result_2 = calculate_sha256(test_file)
        self.assertEqual(hash_result, hash_result_2)

    def test_calculate_sha256_nonexistent_file(self):
        """Test that calculating hash for nonexistent file raises error."""
        nonexistent = self.test_dir / "does_not_exist.txt"
        with self.assertRaises(FileNotFoundError):
            calculate_sha256(nonexistent)

    def test_scan_directory_for_hashes(self):
        """Test scanning a directory for file hashes."""
        # Create a few test files
        file1 = self.mock_project_root / "code" / "file1.py"
        file1.write_text("print('hello')")
        
        file2 = self.mock_project_root / "data" / "file2.json"
        file2.write_text('{"key": "value"}')
        
        hashes = scan_directory_for_hashes(self.mock_project_root)
        
        # Check that files are found
        self.assertIn("code/file1.py", hashes)
        self.assertIn("data/file2.json", hashes)
        
        # Check that hashes are valid
        for hash_val in hashes.values():
            self.assertEqual(len(hash_val), 64)

    def test_save_and_load_state_file(self):
        """Test saving and loading state file."""
        state_path = self.mock_project_root / "state" / "test_state.yaml"
        
        test_data = {
            "project_id": "TEST-001",
            "last_updated": "2023-01-01T00:00:00",
            "artifact_hashes": {
                "code/main.py": "abc123"
            }
        }
        
        # Save state
        save_state_file(test_data, state_path)
        
        # Verify file exists
        self.assertTrue(state_path.exists())
        
        # Load state
        loaded_data = load_state_file(state_path)
        
        # Verify contents
        self.assertEqual(loaded_data["project_id"], "TEST-001")
        self.assertEqual(loaded_data["artifact_hashes"]["code/main.py"], "abc123")

    def test_update_project_state(self):
        """Test the full update_project_state workflow."""
        # Mock get_project_root to return our temp directory
        with patch('utils.state_manager.get_project_root', return_value=self.mock_project_root):
            # Create some test files
            (self.mock_project_root / "code" / "test.py").write_text("def foo(): pass")
            (self.mock_project_root / "data" / "test.json").write_text('{"a": 1}')
            
            # Run update
            result = update_project_state()
            
            # Verify result structure
            self.assertIn("last_updated", result)
            self.assertIn("artifact_hashes", result)
            self.assertIn("code/test.py", result["artifact_hashes"])
            self.assertIn("data/test.json", result["artifact_hashes"])
            
            # Verify state file was created
            state_file = self.mock_project_root / "state" / "projects" / "PROJ-864-llmxive-follow-up-extending-improved-lar.yaml"
            self.assertTrue(state_file.exists())

def run_tests():
    """Run all tests in this module."""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestStateManager)
    runner = unittest.TextTestRunner(verbosity=2)
    return runner.run(suite)

if __name__ == "__main__":
    run_tests()
