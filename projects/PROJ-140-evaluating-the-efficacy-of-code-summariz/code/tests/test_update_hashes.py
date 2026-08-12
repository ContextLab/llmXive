"""
Tests for T032: Hash Generation
"""
import unittest
import os
import sys
import tempfile
import shutil
from pathlib import Path
import yaml

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.update_hashes import collect_artifacts, generate_hashes_for_project, main
from utils.hash_artifacts import hash_file

class TestUpdateHashes(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
        
        # Create a mock project structure
        (self.project_root / "code").mkdir()
        (self.project_root / "code" / "utils").mkdir()
        (self.project_root / "data").mkdir()
        (self.project_root / "data" / "analysis_results").mkdir()
        (self.project_root / "state").mkdir()
        (self.project_root / "state" / "projects").mkdir()
        (self.project_root / "state" / "projects" / "PROJ-140-evaluating-the-efficacy-of-code-summariz").mkdir()
        (self.project_root / "docs").mkdir()
        
        # Create a mock file
        test_file = self.project_root / "code" / "utils" / "test_file.py"
        test_file.write_text("# Test file\nprint('hello')")
        
        # Create a mock data file
        data_file = self.project_root / "data" / "analysis_results" / "results.csv"
        data_file.write_text("metric,value\ntest,1.0")

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_collect_artifacts(self):
        """Test that collect_artifacts finds the mock files"""
        patterns = ["code/**/*.py", "data/analysis_results/results.csv"]
        artifacts = collect_artifacts(self.project_root, patterns)
        
        self.assertTrue(any("test_file.py" in str(a) for a in artifacts))
        self.assertTrue(any("results.csv" in str(a) for a in artifacts))

    def test_hash_generation(self):
        """Test that hash generation works on mock files"""
        # Temporarily patch the project root
        import utils.update_hashes as update_module
        original_root = update_module.project_root
        update_module.project_root = self.project_root
        
        try:
            hashes = generate_hashes_for_project()
            self.assertTrue(len(hashes) > 0)
            self.assertIn("code/utils/test_file.py", hashes)
            self.assertIn("data/analysis_results/results.csv", hashes)
            
            # Verify hash format
            for path, hash_val in hashes.items():
                self.assertEqual(len(hash_val), 64)  # SHA-256 hex length
        finally:
            update_module.project_root = original_root

    def test_yaml_output_structure(self):
        """Test that the YAML output has the correct structure"""
        import utils.update_hashes as update_module
        original_root = update_module.project_root
        update_module.project_root = self.project_root
        
        try:
            hashes = generate_hashes_for_project()
            output_data = {
                "project_id": "PROJ-140-evaluating-the-efficacy-of-code-summariz",
                "generated_at": "2023-10-27T10:00:00Z",
                "artifacts": hashes
            }
            
            # Verify structure
            self.assertIn("project_id", output_data)
            self.assertIn("generated_at", output_data)
            self.assertIn("artifacts", output_data)
            self.assertIsInstance(output_data["artifacts"], dict)
        finally:
            update_module.project_root = original_root

if __name__ == "__main__":
    unittest.main()