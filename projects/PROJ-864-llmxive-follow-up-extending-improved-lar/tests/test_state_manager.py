import os
import sys
import tempfile
import unittest
from pathlib import Path
import yaml

# Add the code root to the path so imports work
code_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(code_root))

from utils.state_manager import calculate_sha256, scan_directory_for_hashes, load_state_file, save_state_file, update_project_state
from utils.logging import setup_logging

class TestStateManager(unittest.TestCase):
    def setUp(self):
        setup_logging(level="DEBUG")
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = Path(self.temp_dir) / "test.txt"
        self.test_file.write_text("Hello, World!")
        
        self.state_file = Path(self.temp_dir) / "state.yaml"
    
    def test_calculate_sha256(self):
        """Test SHA-256 calculation for a known string."""
        # "Hello, World!" SHA-256
        expected_hash = "d9014c4624844aa5bac314773d6b689ad467fa4e1d1a50a1b8a99d5a95f72ff5"
        actual_hash = calculate_sha256(self.test_file)
        self.assertEqual(actual_hash, expected_hash)
    
    def test_calculate_sha256_nonexistent_file(self):
        """Test that FileNotFoundError is raised for missing files."""
        with self.assertRaises(FileNotFoundError):
            calculate_sha256(Path("/nonexistent/file.txt"))
    
    def test_scan_directory_for_hashes(self):
        """Test scanning a directory for file hashes."""
        # Create a few test files
        (Path(self.temp_dir) / "subdir").mkdir()
        file1 = Path(self.temp_dir) / "file1.txt"
        file2 = Path(self.temp_dir) / "subdir" / "file2.txt"
        file1.write_text("Content 1")
        file2.write_text("Content 2")
        
        hashes = scan_directory_for_hashes(Path(self.temp_dir))
        
        self.assertIn("file1.txt", hashes)
        self.assertIn("subdir/file2.txt", hashes)
        self.assertEqual(len(hashes), 2)
    
    def test_scan_directory_with_extension_filter(self):
        """Test scanning with file extension filter."""
        (Path(self.temp_dir) / "file1.txt").write_text("Text")
        (Path(self.temp_dir) / "file2.py").write_text("Code")
        
        hashes = scan_directory_for_hashes(Path(self.temp_dir), extensions=[".py"])
        
        self.assertNotIn("file1.txt", hashes)
        self.assertIn("file2.py", hashes)
        self.assertEqual(len(hashes), 1)
    
    def test_load_state_file_new(self):
        """Test loading a non-existent state file returns empty dict."""
        non_existent = Path(self.temp_dir) / "non_existent.yaml"
        state = load_state_file(non_existent)
        self.assertEqual(state, {})
    
    def test_save_and_load_state_file(self):
        """Test saving and loading a state file."""
        test_state = {
            "project_id": "test-project",
            "artifacts": {
                "code": {"main.py": "abc123"}
            }
        }
        
        save_state_file(self.state_file, test_state)
        
        self.assertTrue(self.state_file.exists())
        
        loaded_state = load_state_file(self.state_file)
        self.assertEqual(loaded_state["project_id"], "test-project")
        self.assertEqual(loaded_state["artifacts"]["code"]["main.py"], "abc123")
    
    def test_update_project_state(self):
        """Test updating the project state with hashes."""
        # Create a minimal project structure
        project_root = Path(self.temp_dir) / "test_project"
        project_root.mkdir()
        code_dir = project_root / "code"
        code_dir.mkdir()
        (code_dir / "main.py").write_text("print('hello')")
        
        state_path = project_root / "state.yaml"
        
        state = update_project_state(project_root, state_path, target_dirs=["code"])
        
        self.assertTrue(state_path.exists())
        self.assertIn("code", state["artifacts"])
        self.assertIn("main.py", state["artifacts"]["code"])
        self.assertIn("project_id", state)
        self.assertIn("last_updated", state)

def run_tests():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestStateManager)
    unittest.TextTestRunner(verbosity=2).run(suite)

if __name__ == "__main__":
    run_tests()