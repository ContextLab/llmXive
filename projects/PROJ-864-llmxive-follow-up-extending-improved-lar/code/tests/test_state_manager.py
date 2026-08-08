import os
import sys
import tempfile
import unittest
from pathlib import Path
import yaml
import hashlib

# Add parent directory to path to import utils
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.state_manager import (
    calculate_sha256,
    scan_directory_for_hashes,
    load_state_file,
    save_state_file,
    update_project_state
)
from utils.logging import setup_logging

setup_logging()

class TestStateManager(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.code_dir = self.test_dir / "code"
        self.code_dir.mkdir()
        self.state_dir = self.test_dir / "state"
        self.state_dir.mkdir()
        
        # Create some test files
        (self.code_dir / "test1.py").write_text("print('hello')")
        (self.code_dir / "test2.py").write_text("print('world')")
        (self.code_dir / "subdir").mkdir()
        (self.code_dir / "subdir" / "test3.py").write_text("print('nested')")
        
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_calculate_sha256(self):
        """Test SHA-256 calculation for a simple file."""
        file_path = self.code_dir / "test1.py"
        hash_value = calculate_sha256(file_path)
        
        # Verify it's a valid hex string of correct length
        self.assertEqual(len(hash_value), 64)
        self.assertTrue(all(c in '0123456789abcdef' for c in hash_value))
        
        # Verify consistency
        hash_value2 = calculate_sha256(file_path)
        self.assertEqual(hash_value, hash_value2)

    def test_scan_directory_for_hashes(self):
        """Test scanning a directory for file hashes."""
        hashes = scan_directory_for_hashes(self.code_dir)
        
        # Should find 3 files
        self.assertEqual(len(hashes), 3)
        
        # Verify structure
        self.assertIn("test1.py", hashes)
        self.assertIn("test2.py", hashes)
        self.assertIn("subdir/test3.py", hashes)
        
        # Verify values are valid hashes
        for file_path, hash_val in hashes.items():
            self.assertEqual(len(hash_val), 64)

    def test_scan_directory_with_extension_filter(self):
        """Test scanning with extension filter."""
        hashes = scan_directory_for_hashes(self.code_dir, extensions=[".py"])
        
        self.assertEqual(len(hashes), 3)
        
        # Add a non-py file
        (self.code_dir / "data.json").write_text("{}")
        hashes_filtered = scan_directory_for_hashes(self.code_dir, extensions=[".py"])
        hashes_all = scan_directory_for_hashes(self.code_dir)
        
        # Filtered should still be 3, all should be 4
        self.assertEqual(len(hashes_filtered), 3)
        self.assertEqual(len(hashes_all), 4)

    def test_load_state_file_nonexistent(self):
        """Test loading a non-existent state file."""
        state_path = self.state_dir / "nonexistent.yaml"
        state_data = load_state_file(state_path)
        
        self.assertEqual(state_data["version"], 1)
        self.assertIsNone(state_data["last_updated"])
        self.assertEqual(state_data["files"], {})

    def test_load_state_file_existing(self):
        """Test loading an existing state file."""
        state_path = self.state_dir / "state.yaml"
        test_data = {
            "version": 1,
            "last_updated": "2024-01-01T00:00:00",
            "files": {"test.txt": "abc123"}
        }
        
        with open(state_path, "w") as f:
            yaml.dump(test_data, f)
            
        loaded_data = load_state_file(state_path)
        
        self.assertEqual(loaded_data["version"], 1)
        self.assertEqual(loaded_data["last_updated"], "2024-01-01T00:00:00")
        self.assertEqual(loaded_data["files"]["test.txt"], "abc123")

    def test_save_state_file(self):
        """Test saving state to a file."""
        state_path = self.state_dir / "state.yaml"
        test_data = {
            "version": 1,
            "last_updated": "2024-01-01T00:00:00",
            "files": {"test.txt": "abc123"}
        }
        
        save_state_file(state_path, test_data)
        
        self.assertTrue(state_path.exists())
        
        # Verify content
        with open(state_path, "r") as f:
            loaded = yaml.safe_load(f)
            
        self.assertEqual(loaded["version"], 1)
        self.assertEqual(loaded["files"]["test.txt"], "abc123")

    def test_update_project_state(self):
        """Test updating the project state."""
        # Create a mock project structure
        state_file_name = "state.yaml"
        state_path = self.state_dir / state_file_name
        
        # Call update
        state = update_project_state(self.test_dir, state_file_name)
        
        # Verify state was created/updated
        self.assertTrue(state_path.exists())
        self.assertEqual(state["version"], 1)
        self.assertIn("last_updated", state)
        self.assertIn("files", state)
        self.assertEqual(state["project_id"], self.test_dir.name)
        
        # Verify files were hashed
        self.assertGreater(len(state["files"]), 0)
        self.assertIn("test1.py", state["files"])

    def test_update_project_state_missing_code_dir(self):
        """Test update fails gracefully when code dir is missing."""
        empty_dir = self.test_dir / "empty"
        empty_dir.mkdir()
        
        with self.assertRaises(FileNotFoundError):
            update_project_state(empty_dir)

def run_tests():
    """Run all tests and return results."""
    suite = unittest.TestLoader().loadTestsFromTestCase(TestStateManager)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result

if __name__ == "__main__":
    run_tests()