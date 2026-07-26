"""
Tests for formatting utilities.
"""
import unittest
from pathlib import Path
import tempfile
import shutil
import os
from code.formatting_utils import run_command, run_ruff_check_and_fix, run_black_format

class TestFormattingUtils(unittest.TestCase):
    """Test cases for formatting utilities."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.code_dir = Path(self.test_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_run_command_success(self):
        """Test that run_command executes successfully."""
        result = run_command([sys.executable, "--version"], check=True)
        self.assertEqual(result.returncode, 0)

    def test_run_command_failure(self):
        """Test that run_command handles failures correctly."""
        with self.assertRaises(subprocess.CalledProcessError):
            run_command(["nonexistent_command"], check=True)

    def test_run_ruff_check_on_empty_dir(self):
        """Test ruff check on an empty directory."""
        # Create a simple Python file
        test_file = self.code_dir / "test.py"
        test_file.write_text("x = 1\n")
        
        success, message = run_ruff_check_and_fix(self.code_dir)
        # Should succeed even if no issues found
        self.assertTrue(success)

    def test_run_black_format_on_empty_dir(self):
        """Test black format on an empty directory."""
        # Create a simple Python file
        test_file = self.code_dir / "test.py"
        test_file.write_text("x=1\n")
        
        success, message = run_black_format(self.code_dir)
        # Should succeed
        self.assertTrue(success)

def test_func():
    """Simple test function for quick validation."""
    assert True

if __name__ == '__main__':
    unittest.main()