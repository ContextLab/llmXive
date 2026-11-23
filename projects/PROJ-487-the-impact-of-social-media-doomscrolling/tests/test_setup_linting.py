import unittest
import tempfile
import os
import sys
from pathlib import Path
import shutil

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from setup_linting import (
    create_gitignore_entry,
    create_flake8_config,
    create_black_config,
    create_isort_config
)

class TestSetupLinting(unittest.TestCase):
    def setUp(self):
        """Create a temporary directory for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        # Create a mock logging module to avoid import errors
        sys.modules['utils'] = type(sys)('utils')
        sys.modules['utils.logging'] = type(sys)('utils.logging')
        sys.modules['utils.logging'].get_logger = lambda name: unittest.mock.MagicMock()

    def tearDown(self):
        """Clean up temporary directory."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)

    def test_create_gitignore_entry_creates_file(self):
        """Test that .gitignore is created or updated."""
        create_gitignore_entry()
        self.assertTrue(Path(".gitignore").exists())

    def test_create_gitignore_entry_adds_patterns(self):
        """Test that linting patterns are added to .gitignore."""
        create_gitignore_entry()
        with open(".gitignore", 'r') as f:
            content = f.read()
        
        self.assertIn("__pycache__/", content)
        self.assertIn(".coverage", content)
        self.assertIn(".pytest_cache/", content)

    def test_create_flake8_config_creates_file(self):
        """Test that .flake8 is created."""
        create_flake8_config()
        self.assertTrue(Path(".flake8").exists())

    def test_create_flake8_config_has_correct_settings(self):
        """Test that .flake8 contains expected settings."""
        create_flake8_config()
        with open(".flake8", 'r') as f:
            content = f.read()
        
        self.assertIn("[flake8]", content)
        self.assertIn("max-line-length = 88", content)
        self.assertIn("exclude =", content)

    def test_create_black_config_creates_or_updates_pyproject(self):
        """Test that pyproject.toml is created or updated with Black config."""
        create_black_config()
        self.assertTrue(Path("pyproject.toml").exists())
        
        with open("pyproject.toml", 'r') as f:
            content = f.read()
        
        self.assertIn("[tool.black]", content)
        self.assertIn("line-length = 88", content)

    def test_create_isort_config_creates_or_updates_pyproject(self):
        """Test that pyproject.toml is created or updated with isort config."""
        create_isort_config()
        self.assertTrue(Path("pyproject.toml").exists())
        
        with open("pyproject.toml", 'r') as f:
            content = f.read()
        
        self.assertIn("[tool.isort]", content)
        self.assertIn("profile = \"black\"", content)

    def test_multiple_calls_idempotent(self):
        """Test that calling functions multiple times doesn't duplicate content."""
        create_flake8_config()
        create_flake8_config()
        
        with open(".flake8", 'r') as f:
            content = f.read()
        
        # Count occurrences of [flake8]
        count = content.count("[flake8]")
        self.assertEqual(count, 1)

    def test_black_and_isort_in_same_pyproject(self):
        """Test that both Black and isort configs exist in pyproject.toml."""
        create_black_config()
        create_isort_config()
        
        with open("pyproject.toml", 'r') as f:
            content = f.read()
        
        self.assertIn("[tool.black]", content)
        self.assertIn("[tool.isort]", content)

if __name__ == "__main__":
    unittest.main()