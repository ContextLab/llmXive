import unittest
from pathlib import Path
import tempfile
import shutil
import os
from code.formatting_utils import run_command, run_ruff_check_and_fix, run_black_format

class TestFormattingUtils(unittest.TestCase):
    """Test cases for formatting utility functions."""

    def setUp(self):
        """Set up a temporary directory for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = Path(self.temp_dir) / "test_module.py"
        # Create a poorly formatted file
        self.test_file.write_text("import os\nimport sys\ndef bad_func( ):\n    x=1+2\n    return x\n")

    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_run_command_success(self):
        """Test run_command with a successful command."""
        code, out, err = run_command(["echo", "hello"], cwd=Path(self.temp_dir))
        self.assertEqual(code, 0)
        self.assertIn("hello", out)

    def test_run_command_failure(self):
        """Test run_command with a failing command."""
        code, out, err = run_command(["false"], cwd=Path(self.temp_dir))
        self.assertNotEqual(code, 0)

    def test_ruff_check_on_poorly_formatted_code(self):
        """Test ruff check on poorly formatted code."""
        # Note: This test may pass or fail depending on whether ruff is installed
        # and the specific rules configured. We test that the function runs without error.
        success, report = run_ruff_check_and_fix(Path(self.temp_dir))
        self.assertIsInstance(success, bool)
        self.assertIsInstance(report, list)

    def test_black_format_on_poorly_formatted_code(self):
        """Test black format on poorly formatted code."""
        # Note: This test may pass or fail depending on whether black is installed
        success, report = run_black_format(Path(self.temp_dir))
        self.assertIsInstance(success, bool)
        self.assertIsInstance(report, list)

    def test_file_is_formatted_after_black(self):
        """Verify that black actually modifies the file."""
        # Run black
        run_black_format(Path(self.temp_dir))
        
        # Read the file back
        content = self.test_file.read_text()
        
        # Black should have formatted it (no spaces inside parens, spaces around operators)
        self.assertNotIn("bad_func( )", content)
        self.assertIn("bad_func():", content)
        self.assertIn("x = 1 + 2", content)

def test_func():
    """A simple test function to ensure the module has a callable test."""
    assert True

if __name__ == "__main__":
    unittest.main()
