import os
import sys
import tempfile
import unittest
from pathlib import Path
from utils.state_manager import calculate_sha256, load_state_file, save_state_file, update_project_state

class TestStateManager(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
        
        # Create test directory structure
        self.code_dir = self.project_root / "code"
        self.data_dir = self.project_root / "data"
        self.state_dir = self.project_root / "state"
        
        self.code_dir.mkdir()
        self.data_dir.mkdir()
        self.state_dir.mkdir()
        
        # Create test files
        self.test_file = self.code_dir / "test.py"
        self.test_file.write_text("# Test file\nprint('hello')\n")
        
        self.state_file = self.state_dir / f"{self.project_root.name}.yaml"
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_calculate_sha256(self):
        """Test SHA-256 calculation for a file."""
        # Known content and its expected hash
        content = b"hello world"
        expected_hash = "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
        
        test_file = self.project_root / "test_hash.txt"
        test_file.write_bytes(content)
        
        calculated_hash = calculate_sha256(test_file)
        
        self.assertEqual(calculated_hash, expected_hash)
        test_file.unlink()
    
    def test_load_state_file_nonexistent(self):
        """Test loading a non-existent state file returns default structure."""
        non_existent_path = self.project_root / "non_existent.yaml"
        state = load_state_file(non_existent_path)
        
        self.assertIn("project", state)
        self.assertIn("artifacts", state)
        self.assertIsNone(state["last_updated"])
    
    def test_save_and_load_state_file(self):
        """Test saving and loading a state file."""
        test_state = {
            "project": "test_project",
            "last_updated": "2024-01-01T00:00:00",
            "artifacts": {
                "code/test.py": "abc123",
                "data/test.json": "def456"
            }
        }
        
        save_state_file(self.state_file, test_state)
        
        self.assertTrue(self.state_file.exists())
        
        loaded_state = load_state_file(self.state_file)
        
        self.assertEqual(loaded_state["project"], test_state["project"])
        self.assertEqual(loaded_state["last_updated"], test_state["last_updated"])
        self.assertEqual(loaded_state["artifacts"], test_state["artifacts"])
    
    def test_update_project_state(self):
        """Test updating project state with actual file hashes."""
        # Create a test file in the code directory
        test_script = self.code_dir / "script.py"
        test_script.write_text("def hello():\n    return 'world'\n")
        
        # Update state
        state = update_project_state(
            self.project_root,
            self.state_file,
            extensions=[".py"]
        )
        
        # Verify state was updated
        self.assertIn("project", state)
        self.assertIn("artifacts", state)
        self.assertIn("last_updated", state)
        
        # Verify the test script is in the artifacts
        self.assertIn("code/script.py", state["artifacts"])
        
        # Verify the hash is valid (64 hex characters for SHA-256)
        file_hash = state["artifacts"]["code/script.py"]
        self.assertEqual(len(file_hash), 64)
        self.assertTrue(all(c in '0123456789abcdef' for c in file_hash))
    
    def test_update_project_state_missing_file(self):
        """Test that update_project_state handles missing files gracefully."""
        # Don't create any files - directories exist but are empty
        state = update_project_state(
            self.project_root,
            self.state_file,
            extensions=[".py"]
        )
        
        # Should still create a valid state file
        self.assertIn("project", state)
        self.assertEqual(state["artifacts"], {})
    
    def test_state_file_persistence(self):
        """Test that state file persists across multiple updates."""
        # First update
        test_file_1 = self.code_dir / "file1.py"
        test_file_1.write_text("# File 1\n")
        
        state1 = update_project_state(
            self.project_root,
            self.state_file,
            extensions=[".py"]
        )
        
        self.assertIn("code/file1.py", state1["artifacts"])
        
        # Second update with different file
        test_file_2 = self.code_dir / "file2.py"
        test_file_2.write_text("# File 2\n")
        
        state2 = update_project_state(
            self.project_root,
            self.state_file,
            extensions=[".py"]
        )
        
        # Both files should be present
        self.assertIn("code/file1.py", state2["artifacts"])
        self.assertIn("code/file2.py", state2["artifacts"])
        
        # Hashes should be different
        self.assertNotEqual(
            state2["artifacts"]["code/file1.py"],
            state2["artifacts"]["code/file2.py"]
        )

def run_tests():
    """Run all tests in this module."""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestStateManager)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
