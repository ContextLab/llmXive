import unittest
from pathlib import Path
import tempfile
import shutil
import os
from code.formatting_utils import run_command, run_ruff_check_and_fix, run_black_format

class TestFormattingUtils(unittest.TestCase):
    def setUp(self):
        """Set up a temporary directory for testing."""
        self.test_dir = tempfile.mkdtemp()
        self.test_code_dir = Path(self.test_dir) / "code"
        self.test_code_dir.mkdir()

    def tearDown(self):
        """Clean up the temporary directory."""
        shutil.rmtree(self.test_dir)

    def test_run_command_success(self):
        """Test that run_command executes a simple command successfully."""
        returncode, stdout, stderr = run_command(["echo", "hello"])
        self.assertEqual(returncode, 0)
        self.assertIn("hello", stdout)

    def test_run_command_failure(self):
        """Test that run_command handles command failure gracefully."""
        returncode, stdout, stderr = run_command(["sh", "-c", "exit 1"])
        self.assertEqual(returncode, 1)

    def test_run_ruff_check_and_fix_on_empty_dir(self):
        """Test ruff on a directory with no Python files."""
        # Create a temporary project structure
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            code_dir = tmppath / "code"
            code_dir.mkdir()
            # Run ruff on empty code dir
            result = run_ruff_check_and_fix(tmppath)
            # Should succeed (no files to check)
            self.assertTrue(result)

    def test_run_black_format_on_empty_dir(self):
        """Test black on a directory with no Python files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            code_dir = tmppath / "code"
            code_dir.mkdir()
            # Run black on empty code dir
            result = run_black_format(tmppath)
            # Should succeed (no files to format)
            self.assertTrue(result)

    def test_run_command_with_cwd(self):
        """Test that run_command respects the cwd parameter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            returncode, stdout, stderr = run_command(["pwd"], cwd=tmppath)
            self.assertEqual(returncode, 0)
            self.assertIn(str(tmppath), stdout)

def test_func():
    """Placeholder function for test discovery."""
    pass

if __name__ == '__main__':
    unittest.main()