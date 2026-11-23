"""
Unit Tests for Secure Storage Implementation (T019)
"""
import os
import stat
import tempfile
import shutil
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
from utils.secure_storage import (
    ensure_consent_directory,
    enforce_file_permissions,
    enforce_directory_permissions,
    ensure_gitignore_exclusion,
    secure_consent_storage
)

class TestSecureStorage(unittest.TestCase):

    def setUp(self):
        """Create a temporary directory structure for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        self.consent_dir = self.temp_path / "data" / "consent"
        self.gitignore_path = self.temp_path / ".gitignore"

    def tearDown(self):
        """Clean up the temporary directory."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_ensure_consent_directory_creates_missing(self):
        """Test that ensure_consent_directory creates the directory if missing."""
        result_path = ensure_consent_directory(self.temp_path)
        
        self.assertTrue(result_path.exists())
        self.assertTrue(result_path.is_dir())
        self.assertEqual(result_path, self.consent_dir)

    def test_ensure_consent_directory_exists(self):
        """Test that ensure_consent_directory handles existing directory."""
        self.consent_dir.mkdir(parents=True)
        result_path = ensure_consent_directory(self.temp_path)
        
        self.assertTrue(result_path.exists())
        self.assertEqual(result_path, self.consent_dir)

    def test_enforce_file_permissions(self):
        """Test setting file permissions."""
        test_file = self.consent_dir / "test.txt"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("secret")
        
        # Set to 0o600
        enforce_file_permissions(test_file, 0o600)
        
        current_mode = stat.S_IMODE(os.stat(test_file).st_mode)
        self.assertEqual(current_mode, 0o600)

    def test_enforce_directory_permissions_recursive(self):
        """Test recursive permission setting on directory and files."""
        # Create structure
        self.consent_dir.mkdir(parents=True)
        (self.consent_dir / "file1.txt").write_text("data")
        sub_dir = self.consent_dir / "subdir"
        sub_dir.mkdir()
        (sub_dir / "file2.txt").write_text("data")
        
        enforce_directory_permissions(self.consent_dir, file_mode=0o600, dir_mode=0o700)
        
        # Check directory permissions
        self.assertEqual(stat.S_IMODE(os.stat(self.consent_dir).st_mode), 0o700)
        self.assertEqual(stat.S_IMODE(os.stat(sub_dir).st_mode), 0o700)
        
        # Check file permissions
        self.assertEqual(stat.S_IMODE(os.stat(self.consent_dir / "file1.txt").st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(os.stat(sub_dir / "file2.txt").st_mode), 0o600)

    def test_ensure_gitignore_exclusion_creates(self):
        """Test that ensure_gitignore_exclusion creates .gitignore if missing."""
        ensure_gitignore_exclusion(self.temp_path)
        
        self.assertTrue(self.gitignore_path.exists())
        content = self.gitignore_path.read_text()
        self.assertIn("data/consent/", content)

    def test_ensure_gitignore_exclusion_adds(self):
        """Test that ensure_gitignore_exclusion adds line if missing."""
        self.gitignore_path.write_text("# existing ignore\n")
        ensure_gitignore_exclusion(self.temp_path)
        
        content = self.gitignore_path.read_text()
        self.assertIn("data/consent/", content)

    def test_ensure_gitignore_exclusion_skips_existing(self):
        """Test that ensure_gitignore_exclusion does not duplicate line."""
        self.gitignore_path.write_text("data/consent/\n")
        initial_content = self.gitignore_path.read_text()
        
        ensure_gitignore_exclusion(self.temp_path)
        
        final_content = self.gitignore_path.read_text()
        self.assertEqual(initial_content, final_content)

    @patch('utils.secure_storage.get_logger')
    def test_secure_consent_storage_full_flow(self, mock_logger):
        """Test the full secure_consent_storage workflow."""
        result = secure_consent_storage(self.temp_path)
        
        self.assertTrue(result)
        self.assertTrue(self.consent_dir.exists())
        self.assertTrue(self.gitignore_path.exists())
        
        # Verify permissions
        self.assertEqual(stat.S_IMODE(os.stat(self.consent_dir).st_mode), 0o700)
        # Verify gitignore content
        self.assertIn("data/consent/", self.gitignore_path.read_text())

if __name__ == '__main__':
    unittest.main()