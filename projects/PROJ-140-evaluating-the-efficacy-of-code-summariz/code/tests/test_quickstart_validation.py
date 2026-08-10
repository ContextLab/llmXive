import os
import sys
import subprocess
import yaml
import json
import tempfile
import unittest
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from quickstart_validator import (
    validate_quickstart_file,
    validate_project_structure,
    validate_python_syntax,
    validate_dependencies,
    validate_data_files,
    run_quickstart_validation
)

class TestQuickstartValidation(unittest.TestCase):
    
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        
        # Create a minimal mock structure
        (self.temp_path / "code").mkdir()
        (self.temp_path / "docs").mkdir()
        (self.temp_path / "data").mkdir()
        
        # Create a mock quickstart.md
        self.quickstart_path = self.temp_path / "docs" / "quickstart.md"
        self.quickstart_path.write_text("""
        # Quickstart Guide

        ## Installation
        pip install -r requirements.txt

        ## Running the Pipeline
        python code/main.py run
        """)

        # Create a mock requirements.txt
        (self.temp_path / "requirements.txt").write_text("pandas\nnumpy")

        # Create a mock valid python file
        (self.temp_path / "code" / "main.py").write_text("print('hello')")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_validate_quickstart_file_exists(self):
        result = validate_quickstart_file(self.quickstart_path)
        self.assertTrue(result["file_exists"])
        self.assertTrue(result["has_content"])
        self.assertTrue(result["has_execution_steps"])
        self.assertTrue(result["has_dependency_check"])
        self.assertEqual(len(result["errors"]), 0)

    def test_validate_quickstart_file_missing(self):
        missing_path = self.temp_path / "docs" / "nonexistent.md"
        result = validate_quickstart_file(missing_path)
        self.assertFalse(result["file_exists"])
        self.assertTrue(len(result["errors"]) > 0)

    def test_validate_quickstart_file_empty(self):
        empty_path = self.temp_path / "docs" / "empty.md"
        empty_path.write_text("")
        result = validate_quickstart_file(empty_path)
        self.assertTrue(result["file_exists"])
        self.assertFalse(result["has_content"])
        self.assertTrue(len(result["errors"]) > 0)

    def test_validate_project_structure(self):
        # Create required dirs
        required = ["code/analysis", "data/raw"]
        for d in required:
            (self.temp_path / d).mkdir(parents=True, exist_ok=True)
        
        result = validate_project_structure(self.temp_path)
        # Should be valid now
        self.assertTrue(result["valid"])
        self.assertEqual(len(result["missing_dirs"]), 0)

    def test_validate_project_structure_missing_dirs(self):
        result = validate_project_structure(self.temp_path)
        self.assertFalse(result["valid"])
        self.assertGreater(len(result["missing_dirs"]), 0)

    def test_validate_python_syntax_valid(self):
        result = validate_python_syntax(self.temp_path)
        self.assertTrue(result["valid"])
        self.assertEqual(len(result["errors"]), 0)

    def test_validate_python_syntax_invalid(self):
        invalid_file = self.temp_path / "code" / "bad.py"
        invalid_file.write_text("def broken(") # Syntax error
        result = validate_python_syntax(self.temp_path)
        self.assertFalse(result["valid"])
        self.assertGreater(len(result["errors"]), 0)
        self.assertTrue(any("bad.py" in str(e) for e in result["errors"]))

    def test_validate_dependencies(self):
        result = validate_dependencies(self.temp_path)
        self.assertTrue(result["exists"])
        self.assertGreater(len(result["dependencies"]), 0)

    def test_validate_dependencies_missing(self):
        (self.temp_path / "requirements.txt").unlink()
        result = validate_dependencies(self.temp_path)
        self.assertFalse(result["exists"])

    def test_run_quickstart_validation(self):
        # Ensure structure is complete enough for a pass
        (self.temp_path / "data" / "raw").mkdir()
        (self.temp_path / "data" / "interaction_logs").mkdir()
        (self.temp_path / "data" / "analysis_results").mkdir()
        (self.temp_path / "state").mkdir()
        
        report = run_quickstart_validation(self.temp_path)
        
        self.assertIn("overall_success", report)
        # Depending on strictness of validation, this might be True or False
        # We just ensure it runs without crashing
        self.assertIsInstance(report["syntax"]["errors"], list)

if __name__ == "__main__":
    unittest.main()