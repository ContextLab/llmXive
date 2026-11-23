"""
Unit tests for verify_accuracy_gate.py
"""
import os
import sys
import tempfile
import unittest
from pathlib import Path
import yaml

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from verify_accuracy_gate import (
    load_research_md, 
    verify_url_format, 
    verify_material_type, 
    update_state_verification_record
)
from utils import load_state, setup_logging

class TestVerifyAccuracyGate(unittest.TestCase):
    
    def setUp(self):
        """Set up temporary files for testing."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.research_md_path = Path(self.temp_dir.name) / "research.md"
        self.state_path = Path(self.temp_dir.name) / "state.yaml"
        
        # Create a minimal state file
        with open(self.state_path, 'w') as f:
            yaml.dump({}, f)
        
        # Change to temp dir for file operations
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir.name)
        
        # Mock the module-level paths by patching if necessary, 
        # but for now we assume the script uses relative paths from cwd
        # We will write test files to the temp dir and run the logic directly

    def tearDown(self):
        """Clean up temporary files."""
        os.chdir(self.original_cwd)
        self.temp_dir.cleanup()

    def test_load_research_md_missing(self):
        """Test that load_research_md raises FileNotFoundError when file is missing."""
        with self.assertRaises(FileNotFoundError):
            load_research_md()

    def test_verify_url_format_no_url(self):
        """Test verify_url_format with no URL in content."""
        content = "This is a test document with no URLs."
        with self.assertRaises(ValueError) as context:
            verify_url_format(content)
        self.assertIn("No valid dataset URL", str(context.exception))

    def test_verify_url_format_valid(self):
        """Test verify_url_format finds a valid URL."""
        content = "Data available at https://zenodo.org/record/12345/data.csv"
        url = verify_url_format(content)
        self.assertEqual(url, "https://zenodo.org/record/12345/data.csv")

    def test_verify_material_type_missing(self):
        """Test verify_material_type raises error if material not found."""
        content = "This dataset is about Aluminum."
        url = "https://example.com/data"
        with self.assertRaises(ValueError) as context:
            verify_material_type(content, url)
        self.assertIn("Material Mismatch", str(context.exception))

    def test_verify_material_type_valid(self):
        """Test verify_material_type passes for 316L."""
        content = "This dataset contains parameters for 316L Stainless Steel."
        url = "https://example.com/data"
        result = verify_material_type(content, url)
        self.assertTrue(result)

    def test_update_state_verification_record(self):
        """Test updating the state file with a verification record."""
        # Create a dummy research.md to satisfy load_research_md if needed
        # But we are testing the update function directly
        
        # Ensure state file exists
        with open(self.state_path, 'w') as f:
            yaml.dump({}, f)
        
        # Patch the module to use our temp state path? 
        # Since the function uses the global constant STATE_FILE_PATH, 
        # and we changed cwd, it should work if we ensure the file exists.
        
        # Actually, the function uses the constant "state.yaml" relative to cwd.
        # We are in temp_dir, so it will write there.
        
        record = update_state_verification_record("https://test.com", "316L")
        
        self.assertEqual(record["status"], "verified")
        self.assertEqual(record["material_verified"], "316L")
        
        # Verify file was updated
        with open(self.state_path, 'r') as f:
            state = yaml.safe_load(f)
        
        self.assertIn("phase0_verification", state)
        self.assertEqual(state["phase0_verification"]["status"], "verified")

if __name__ == "__main__":
    unittest.main()
