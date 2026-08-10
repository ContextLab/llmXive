import os
import sys
import tempfile
import unittest
from pathlib import Path
import yaml
import json

# Add code root to path
code_root = Path(__file__).parent.parent
sys.path.insert(0, str(code_root))

from utils.state_manager import (
    calculate_sha256, 
    scan_directory_for_hashes, 
    load_state_file, 
    save_state_file, 
    update_project_state,
    get_artifact_hash
)
from utils.logging import setup_logging

class TestStateManager(unittest.TestCase):
    
    def setUp(self):
        setup_logging()
        self.temp_dir = tempfile.mkdtemp()
        self.test_file_1 = Path(self.temp_dir) / "test1.txt"
        self.test_file_2 = Path(self.temp_dir) / "subdir" / "test2.json"
        
        # Create test files
        self.test_file_1.write_text("Hello, World!")
        self.test_file_2.parent.mkdir(parents=True, exist_ok=True)
        self.test_file_2.write_text(json.dumps({"key": "value"}))

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_calculate_sha256(self):
        """Test SHA-256 calculation for a known string."""
        content = "Hello, World!"
        expected_hash = calculate_sha256(str(self.test_file_1))
        # Known hash for "Hello, World!"
        known_hash = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        self.assertEqual(expected_hash, known_hash)

    def test_calculate_sha256_file_not_found(self):
        """Test that FileNotFoundError is raised for missing file."""
        with self.assertRaises(FileNotFoundError):
            calculate_sha256("/nonexistent/path/file.txt")

    def test_scan_directory_for_hashes(self):
        """Test scanning a directory for hashes."""
        hashes = scan_directory_for_hashes(self.temp_dir)
        
        # Check that both files are found
        self.assertIn("test1.txt", hashes)
        self.assertIn("subdir/test2.json", hashes)
        
        # Verify hash consistency
        self.assertEqual(hashes["test1.txt"], calculate_sha256(str(self.test_file_1)))

    def test_scan_directory_with_extension_filter(self):
        """Test scanning with extension filter."""
        hashes = scan_directory_for_hashes(self.temp_dir, extensions=[".txt"])
        
        self.assertIn("test1.txt", hashes)
        self.assertNotIn("subdir/test2.json", hashes)
        self.assertEqual(len(hashes), 1)

    def test_load_state_file_new(self):
        """Test loading a non-existent state file."""
        new_state_path = os.path.join(self.temp_dir, "new_state.yaml")
        state = load_state_file(new_state_path)
        
        self.assertEqual(state["project"], {})
        self.assertEqual(state["artifacts"], {})
        self.assertIsNone(state["last_updated"])

    def test_load_save_state_file(self):
        """Test saving and loading a state file."""
        state_path = os.path.join(self.temp_dir, "state.yaml")
        test_data = {
            "project": {"name": "TestProject"},
            "artifacts": {"file.txt": "hash123"},
            "last_updated": "2023-01-01T00:00:00"
        }
        
        save_state_file(state_path, test_data)
        loaded_data = load_state_file(state_path)
        
        self.assertEqual(loaded_data, test_data)

    def test_update_project_state(self):
        """Test updating the project state with real directory structure."""
        state_path = os.path.join(self.temp_dir, "project_state.yaml")
        
        # Create a mock project structure
        mock_code_dir = Path(self.temp_dir) / "code"
        mock_data_dir = Path(self.temp_dir) / "data"
        mock_code_dir.mkdir()
        mock_data_dir.mkdir()
        
        # Add a dummy file
        (mock_code_dir / "dummy.py").write_text("print('hello')")
        (mock_data_dir / "data.json").write_text("{}")

        # Run update
        state = update_project_state(
            project_root=str(self.temp_dir),
            state_path=state_path,
            artifact_dirs=['code', 'data']
        )

        self.assertIn("code/dummy.py", state["artifacts"])
        self.assertIn("data/data.json", state["artifacts"])
        self.assertEqual(state["project"]["name"], "PROJ-864-llmxive-follow-up-extending-improved-lar")
        self.assertIsNotNone(state["last_updated"])

    def test_get_artifact_hash(self):
        """Test retrieving a specific artifact hash."""
        state = {
            "artifacts": {
                "code/main.py": "abc123",
                "data/test.json": "def456"
            }
        }
        
        self.assertEqual(get_artifact_hash(state, "code/main.py"), "abc123")
        self.assertEqual(get_artifact_hash(state, "data/test.json"), "def456")
        self.assertIsNone(get_artifact_hash(state, "nonexistent.txt"))

def run_tests():
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestStateManager)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)

if __name__ == "__main__":
    run_tests()