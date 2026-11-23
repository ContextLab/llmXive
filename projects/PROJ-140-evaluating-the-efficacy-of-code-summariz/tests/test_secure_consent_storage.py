"""
Unit tests for secure_consent_storage.py (T019)
"""
import unittest
import os
import tempfile
import stat
from pathlib import Path
import shutil

# Import the module under test
# Adjust import path based on how tests are run (usually code/ is in sys.path)
try:
    from utils.secure_consent_storage import (
        ensure_consent_directory,
        enforce_file_permissions,
        enforce_directory_permissions,
        ensure_gitignore_exclusion,
        secure_consent_storage
    )
except ImportError:
    # Fallback for running tests from root
    import sys
    sys.path.insert(0, 'code')
    from utils.secure_consent_storage import (
        ensure_consent_directory,
        enforce_file_permissions,
        enforce_directory_permissions,
        ensure_gitignore_exclusion,
        secure_consent_storage
    )

class TestSecureConsentStorage(unittest.TestCase):

    def setUp(self):
        """Create a temporary directory to simulate project root."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

    def tearDown(self):
        """Clean up the temporary directory."""
        shutil.rmtree(self.temp_dir)

    def test_ensure_consent_directory_creates_dir(self):
        """Test that ensure_consent_directory creates the directory if it doesn't exist."""
        consent_path = self.temp_path / "data" / "consent"
        self.assertFalse(consent_path.exists())
        
        result = ensure_consent_directory(self.temp_path)
        
        self.assertTrue(consent_path.exists())
        self.assertTrue(result.is_dir())
        self.assertEqual(result, consent_path)

    def test_ensure_consent_directory_exists_if_exists(self):
        """Test that ensure_consent_directory does nothing if directory exists."""
        consent_path = self.temp_path / "data" / "consent"
        consent_path.mkdir(parents=True)
        
        result = ensure_consent_directory(self.temp_path)
        
        self.assertTrue(result.is_dir())
        self.assertEqual(result, consent_path)

    def test_enforce_file_permissions_sets_600(self):
        """Test that enforce_file_permissions sets 600 permissions."""
        test_file = self.temp_path / "test_file.txt"
        test_file.touch()
        
        # Set to 644 initially to verify change
        os.chmod(test_file, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
        
        enforce_file_permissions(test_file)
        
        # Check permissions
        mode = test_file.stat().st_mode
        # Mask for permission bits
        perm_bits = mode & 0o777
        
        self.assertEqual(perm_bits, 0o600, f"Expected 600, got {oct(perm_bits)}")

    def test_enforce_file_permissions_raises_on_missing(self):
        """Test that enforce_file_permissions raises FileNotFoundError for missing file."""
        missing_file = self.temp_path / "nonexistent.txt"
        
        with self.assertRaises(FileNotFoundError):
            enforce_file_permissions(missing_file)

    def test_enforce_directory_permissions_secures_all_files(self):
        """Test that enforce_directory_permissions secures all files in the directory."""
        consent_dir = self.temp_path / "data" / "consent"
        consent_dir.mkdir(parents=True)
        
        # Create some files
        file1 = consent_dir / "form1.txt"
        file2 = consent_dir / "form2.txt"
        file1.touch()
        file2.touch()
        
        # Set to 644 initially
        os.chmod(file1, 0o644)
        os.chmod(file2, 0o644)
        
        enforce_directory_permissions(consent_dir)
        
        # Verify permissions
        self.assertEqual(file1.stat().st_mode & 0o777, 0o600)
        self.assertEqual(file2.stat().st_mode & 0o777, 0o600)

    def test_ensure_gitignore_exclusion_adds_rule(self):
        """Test that ensure_gitignore_exclusion adds the rule if missing."""
        gitignore_path = self.temp_path / ".gitignore"
        gitignore_path.write_text("*.pyc\n")
        
        ensure_gitignore_exclusion(self.temp_path)
        
        content = gitignore_path.read_text()
        self.assertIn("data/consent/", content)

    def test_ensure_gitignore_exclusion_ignores_duplicate(self):
        """Test that ensure_gitignore_exclusion does not add duplicate rule."""
        gitignore_path = self.temp_path / ".gitignore"
        gitignore_path.write_text("data/consent/\n*.pyc\n")
        
        ensure_gitignore_exclusion(self.temp_path)
        
        content = gitignore_path.read_text()
        # Count occurrences
        count = content.count("data/consent/")
        self.assertEqual(count, 1)

    def test_ensure_gitignore_exclusion_creates_gitignore(self):
        """Test that ensure_gitignore_exclusion creates .gitignore if missing."""
        gitignore_path = self.temp_path / ".gitignore"
        self.assertFalse(gitignore_path.exists())
        
        ensure_gitignore_exclusion(self.temp_path)
        
        self.assertTrue(gitignore_path.exists())
        content = gitignore_path.read_text()
        self.assertIn("data/consent/", content)

    def test_secure_consent_storage_integration(self):
        """Integration test: runs the full secure_consent_storage flow."""
        # 1. Directory created
        # 2. Permissions set (none to set initially)
        # 3. .gitignore updated
        
        result_dir = secure_consent_storage(self.temp_path)
        
        self.assertTrue(result_dir.exists())
        
        # Check .gitignore
        gitignore_path = self.temp_path / ".gitignore"
        self.assertTrue(gitignore_path.exists())
        self.assertIn("data/consent/", gitignore_path.read_text())

    def test_secure_consent_storage_secures_existing_files(self):
        """Integration test: ensures existing files are secured."""
        consent_dir = self.temp_path / "data" / "consent"
        consent_dir.mkdir(parents=True)
        
        test_file = consent_dir / "existing_form.txt"
        test_file.touch()
        os.chmod(test_file, 0o644) # Start with 644
        
        secure_consent_storage(self.temp_path)
        
        # Verify it was changed to 600
        self.assertEqual(test_file.stat().st_mode & 0o777, 0o600)

if __name__ == '__main__':
    unittest.main()