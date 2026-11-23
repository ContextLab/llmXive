"""
Unit tests for the quickstart validation script.

These tests verify that the validation logic correctly identifies
missing files, invalid content, and structural issues.
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from code.validation.quickstart_validator import (
    check_file_exists,
    check_content,
    validate_project_structure,
    validate_python_imports,
    run_quickstart_validation
)

class TestQuickstartValidator(TestCase):
    """Test cases for the quickstart validation functionality."""

    def setUp(self):
        """Set up a temporary directory structure for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.base_path = Path(self.temp_dir)

        # Create a minimal valid structure
        required_dirs = [
            "data/raw",
            "data/processed",
            "artifacts/checkpoints",
            "artifacts/results",
            "code",
            "code/models",
            "code/training",
            "code/evaluation",
            "code/analysis",
            "code/utils",
            "tests",
            "docs"
        ]

        for dir_path in required_dirs:
            (self.base_path / dir_path).mkdir(parents=True, exist_ok=True)

        # Create minimal __init__.py files
        for dir_path in ["code", "code/models", "code/training", "code/evaluation", "code/analysis", "code/utils"]:
            (self.base_path / dir_path / "__init__.py").write_text("")

        # Create minimal config.py
        config_content = """
        import torch

        class Config:
            TOKEN_LIMIT = 100000
            recursion_depth = 2
            seed = 42
            batch_size = 8
            learning_rate = 1e-4

        def get_config():
            return Config()

        def validate_config(config):
            return True
        """
        (self.base_path / "code" / "config.py").write_text(config_content)

        # Create minimal manifest.json
        manifest_content = {
            "checksum": "abc123",
            "dataset_name": "test_dataset",
            "file_path": "data/raw/test.json"
        }
        (self.base_path / "data" / "manifest.json").write_text(json.dumps(manifest_content))

    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)

    def test_check_file_exists_directory(self):
        """Test checking for directory existence."""
        # Test existing directory
        exists, message = check_file_exists(self.base_path / "code", "Directory")
        self.assertTrue(exists)
        self.assertIn("✓", message)

        # Test missing directory
        exists, message = check_file_exists(self.base_path / "nonexistent", "Directory")
        self.assertFalse(exists)
        self.assertIn("✗", message)

    def test_check_file_exists_file(self):
        """Test checking for file existence."""
        # Test existing file
        exists, message = check_file_exists(self.base_path / "code" / "config.py", "File")
        self.assertTrue(exists)
        self.assertIn("✓", message)

        # Test missing file
        exists, message = check_file_exists(self.base_path / "nonexistent.py", "File")
        self.assertFalse(exists)
        self.assertIn("✗", message)

    def test_check_content_valid(self):
        """Test content validation with valid content."""
        test_file = self.base_path / "test.txt"
        test_file.write_text("This is a test file with required terms.")

        exists, missing = check_content(test_file, ["test", "file", "required"])
        self.assertTrue(exists)
        self.assertEqual(len(missing), 0)

    def test_check_content_missing_terms(self):
        """Test content validation with missing terms."""
        test_file = self.base_path / "test.txt"
        test_file.write_text("This is a test file.")

        exists, missing = check_content(test_file, ["test", "file", "missing_term"])
        self.assertFalse(exists)
        self.assertIn("missing_term", missing)

    def test_validate_project_structure_valid(self):
        """Test structure validation with valid structure."""
        errors = validate_project_structure(self.base_path)
        self.assertEqual(len(errors), 0)

    def test_validate_project_structure_missing_dir(self):
        """Test structure validation with missing directory."""
        # Remove a required directory
        (self.base_path / "docs").rmdir()

        errors = validate_project_structure(self.base_path)
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("docs" in error for error in errors))

    def test_validate_python_imports_valid(self):
        """Test Python import validation with valid files."""
        # Create a valid Python file
        test_file = self.base_path / "code" / "test_module.py"
        test_file.write_text("def hello():\n    return 'world'")

        errors = validate_python_imports(self.base_path)
        # Should not have syntax errors
        syntax_errors = [e for e in errors if "Syntax error" in e]
        self.assertEqual(len(syntax_errors), 0)

    def test_validate_python_imports_invalid_syntax(self):
        """Test Python import validation with invalid syntax."""
        # Create an invalid Python file
        test_file = self.base_path / "code" / "invalid_module.py"
        test_file.write_text("def invalid(\n    # Missing closing parenthesis")

        errors = validate_python_imports(self.base_path)
        syntax_errors = [e for e in errors if "Syntax error" in e]
        self.assertGreater(len(syntax_errors), 0)

    @patch('code.validation.quickstart_validator.get_config')
    @patch('code.validation.quickstart_validator.validate_config')
    def test_run_quickstart_validation_valid(self, mock_validate, mock_get_config):
        """Test full validation with a valid project structure."""
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config
        mock_validate.return_value = True

        success = run_quickstart_validation(self.base_path, verbose=False)
        self.assertTrue(success)

    @patch('code.validation.quickstart_validator.get_config')
    @patch('code.validation.quickstart_validator.validate_config')
    def test_run_quickstart_validation_invalid_config(self, mock_validate, mock_get_config):
        """Test full validation with invalid configuration."""
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config
        mock_validate.return_value = False

        success = run_quickstart_validation(self.base_path, verbose=False)
        self.assertFalse(success)

if __name__ == "__main__":
    import unittest
    unittest.main()
