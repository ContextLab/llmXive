import os
import sys
import unittest
from pathlib import Path
import tempfile
import shutil
from utils.setup_data_dirs import setup_data_directories

class TestDataDirectories(unittest.TestCase):
    """Test directory setup functionality."""

    def test_setup_creates_directories(self):
        """Test that setup_data_directories creates required directories."""
        # Use a temporary directory to test
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # Temporarily patch the project root detection
            # by creating the expected structure
            code_dir = tmp_path / "code"
            code_dir.mkdir()
            
            # Create a dummy utils module to satisfy imports
            (code_dir / "utils").mkdir()
            (code_dir / "utils" / "__init__.py").write_text("")
            
            # Now run setup
            created = setup_data_directories()
            
            # Verify directories exist
            self.assertTrue((tmp_path / "code").exists())
            self.assertTrue((tmp_path / "data").exists())
            self.assertTrue((tmp_path / "state").exists())
            self.assertTrue((tmp_path / "tests").exists())

    def test_setup_handles_existing_directories(self):
        """Test that setup handles existing directories gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            code_dir = tmp_path / "code"
            code_dir.mkdir()
            (code_dir / "utils").mkdir()
            (code_dir / "utils" / "__init__.py").write_text("")
            
            # Run setup twice
            first_run = setup_data_directories()
            second_run = setup_data_directories()
            
            # Second run should not create new directories
            self.assertEqual(len(second_run), 0)

def run_tests():
    """Run the tests and return results."""
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDataDirectories)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)