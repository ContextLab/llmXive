"""
Unit tests for formatting utilities.
"""
import unittest
from pathlib import Path
import tempfile
import shutil
from code.formatting_utils import run_command

class TestFormattingUtils(unittest.TestCase):
    def setUp(self):
        """
        Set up a temporary directory for testing.
        """
        self.test_dir = Path(tempfile.mkdtemp())
        self.test_file = self.test_dir / "test.py"
        
        # Create a test file with formatting issues
        self.test_file.write_text("x=1+2\n")
    
    def tearDown(self):
        """
        Clean up temporary directory.
        """
        shutil.rmtree(self.test_dir)
    
    def test_run_command_success(self):
        """
        Test that run_command returns correct output on success.
        """
        returncode, stdout, stderr = run_command(["echo", "hello"], self.test_dir)
        self.assertEqual(returncode, 0)
        self.assertIn("hello", stdout)
    
    def test_run_command_failure(self):
        """
        Test that run_command handles errors gracefully.
        """
        returncode, stdout, stderr = run_command(["nonexistent_command"], self.test_dir)
        self.assertNotEqual(returncode, 0)
    
    def test_run_command_with_python(self):
        """
        Test running a Python command.
        """
        script = self.test_dir / "script.py"
        script.write_text("print('test output')")
        
        returncode, stdout, stderr = run_command(
            ["python", str(script)], self.test_dir
        )
        self.assertEqual(returncode, 0)
        self.assertIn("test output", stdout)

if __name__ == "__main__":
    unittest.main()