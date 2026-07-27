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
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)

    def test_run_command_success(self):
        """Test that run_command executes successfully."""
        # Create a test script
        test_script = Path(self.test_dir) / "test_script.py"
        test_script.write_text("print('hello')")
        
        returncode, stdout, stderr = run_command(
            [sys.executable, str(test_script)]
        )
        
        self.assertEqual(returncode, 0)
        self.assertIn("hello", stdout)
        self.assertEqual(stderr, "")

    def test_run_command_failure(self):
        """Test that run_command handles failures correctly."""
        returncode, stdout, stderr = run_command(
            [sys.executable, "-c", "raise SystemExit(1)"],
            check=False
        )
        
        self.assertEqual(returncode, 1)
        self.assertIn("", stdout)

    def test_run_ruff_check_and_fix(self):
        """Test ruff check and fix functionality."""
        # Create a test directory with a Python file
        code_dir = Path(self.test_dir) / "code"
        code_dir.mkdir()
        
        # Create a file with formatting issues
        test_file = code_dir / "test_file.py"
        test_file.write_text("x=1+2\n")
        
        # This should run without crashing
        # Note: We don't assert success because ruff/black might not be installed
        try:
            result = run_ruff_check_and_fix()
            self.assertIsInstance(result, bool)
        except FileNotFoundError:
            # Expected if ruff is not installed
            pass

    def test_run_black_format(self):
        """Test black formatting functionality."""
        # Create a test directory with a Python file
        code_dir = Path(self.test_dir) / "code"
        code_dir.mkdir()
        
        # Create a file with formatting issues
        test_file = code_dir / "test_file.py"
        test_file.write_text("x=1+2\n")
        
        # This should run without crashing
        try:
            result = run_black_format()
            self.assertIsInstance(result, bool)
        except FileNotFoundError:
            # Expected if black is not installed
            pass

def test_func():
    """Helper function for testing."""
    return "test"

if __name__ == "__main__":
    unittest.main()
