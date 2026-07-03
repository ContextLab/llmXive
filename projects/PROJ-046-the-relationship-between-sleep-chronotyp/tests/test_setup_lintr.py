import os
import unittest
from pathlib import Path
from code.setup_lintr_config import create_lintr_config

class TestLintrConfig(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = Path("tests/test_tmp_lintr")
        self.test_dir.mkdir(parents=True, exist_ok=True)
        self.code_dir = self.test_dir / "code"
        self.code_dir.mkdir(exist_ok=True)
        
    def tearDown(self):
        """Clean up test fixtures."""
        if self.test_dir.exists():
            import shutil
            shutil.rmtree(self.test_dir)
            
    def test_lintr_config_creation(self):
        """Test that the lintr config file is created correctly."""
        config_path = create_lintr_config(str(self.test_dir))
        
        # Verify the file exists
        self.assertTrue(os.path.exists(config_path), "lintr config file was not created")
        
        # Verify the content contains expected linters
        with open(config_path, 'r') as f:
            content = f.read()
            
        expected_linters = [
            "line_length_linter(120)",
            "assignment_linter()",
            "object_name_linter()",
            "spaces_inside_linter()"
        ]
        
        for linter in expected_linters:
            self.assertIn(linter, content, f"Expected linter '{linter}' not found in config")
            
        # Verify exclusions list exists
        self.assertIn("exclusions: list()", content, "Exclusions list not found in config")

    def test_lintr_config_structure(self):
        """Test that the lintr config has the correct YAML structure."""
        config_path = create_lintr_config(str(self.test_dir))
        
        with open(config_path, 'r') as f:
            content = f.read()
            
        # Check for basic YAML structure
        self.assertIn("linters: list(", content, "Linters list not found")
        self.assertIn(")", content, "Linters list closing parenthesis not found")
        self.assertTrue(content.count("(") == content.count(")"), "Mismatched parentheses in linters list")

if __name__ == '__main__':
    unittest.main()