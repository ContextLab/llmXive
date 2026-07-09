"""
Unit tests for secure_consent_storage.py.
Verifies directory creation, .gitignore exclusion, and file permissions.
"""
import os
import stat
import unittest
import tempfile
import shutil
from pathlib import Path
import sys

# Add parent directory to path to import utils
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.secure_consent_storage import (
    ensure_consent_directory,
    enforce_file_permissions,
    enforce_directory_permissions,
    ensure_gitignore_exclusion,
    secure_consent_storage,
    CONSENT_DIR,
    GITIGNORE_PATH,
    GITIGNORE_RULE
)

class TestSecureConsentStorage(unittest.TestCase):
    def setUp(self):
        """
        Create a temporary directory structure for testing to avoid modifying the real project tree.
        We will mock the global paths temporarily.
        """
        self.temp_dir = tempfile.mkdtemp()
        self.original_consent_dir = CONSENT_DIR
        self.original_gitignore_path = GITIGNORE_PATH
        
        # Create a fake consent dir inside temp
        self.test_consent_dir = Path(self.temp_dir) / "data" / "consent"
        self.test_gitignore = Path(self.temp_dir) / ".gitignore"
        
        # Patch the module globals
        import utils.secure_consent_storage as mod
        mod.CONSENT_DIR = self.test_consent_dir
        mod.GITIGNORE_PATH = self.test_gitignore

    def tearDown(self):
        """
        Restore original paths and clean up temp directory.
        """
        import utils.secure_consent_storage as mod
        mod.CONSENT_DIR = self.original_consent_dir
        mod.GITIGNORE_PATH = self.original_gitignore_path
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_ensure_consent_directory_creates(self):
        """Test that ensure_consent_directory creates the directory if missing."""
        self.assertFalse(self.test_consent_dir.exists())
        result = ensure_consent_directory()
        self.assertTrue(result.exists())
        self.assertTrue(result.is_dir())

    def test_ensure_gitignore_exclusion_adds_rule(self):
        """Test that ensure_gitignore_exclusion adds the rule if missing."""
        self.test_gitignore.touch() # Create empty file
        self.assertFalse(GITIGNORE_RULE in self.test_gitignore.read_text())
        
        result = ensure_gitignore_exclusion()
        self.assertTrue(result)
        content = self.test_gitignore.read_text()
        self.assertIn(GITIGNORE_RULE, content)

    def test_ensure_gitignore_exclusion_skips_existing(self):
        """Test that ensure_gitignore_exclusion does not duplicate rule if present."""
        self.test_gitignore.write_text(f"# Existing\n{GITIGNORE_RULE}\n")
        
        result = ensure_gitignore_exclusion()
        self.assertTrue(result)
        content = self.test_gitignore.read_text()
        # Count occurrences
        count = content.count(GITIGNORE_RULE)
        self.assertEqual(count, 1)

    def test_enforce_file_permissions_sets_600(self):
        """Test that enforce_file_permissions sets mode 600."""
        self.test_consent_dir.mkdir(parents=True, exist_ok=True)
        test_file = self.test_consent_dir / "consent_form.pdf"
        test_file.write_text("fake consent data")
        
        # Set to a permissive mode first (e.g., 644)
        test_file.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
        
        result = enforce_file_permissions(test_file)
        self.assertTrue(result)
        
        current_mode = test_file.stat().st_mode
        # Check owner read/write, no group, no other
        self.assertEqual(current_mode & 0o777, 0o600)

    def test_enforce_directory_permissions_sets_700_and_files_600(self):
        """Test that enforce_directory_permissions sets dir to 700 and files to 600."""
        self.test_consent_dir.mkdir(parents=True, exist_ok=True)
        test_file = self.test_consent_dir / "form.txt"
        test_file.write_text("data")
        
        # Set permissive initially
        self.test_consent_dir.chmod(0o755)
        test_file.chmod(0o644)
        
        result = enforce_directory_permissions(self.test_consent_dir)
        self.assertTrue(result)
        
        dir_mode = self.test_consent_dir.stat().st_mode
        self.assertEqual(dir_mode & 0o777, 0o700)
        
        file_mode = test_file.stat().st_mode
        self.assertEqual(file_mode & 0o777, 0o600)

    def test_secure_consent_storage_full_flow(self):
        """Test the full secure_consent_storage flow."""
        # Ensure dir exists
        self.test_consent_dir.mkdir(parents=True, exist_ok=True)
        # Create a file
        test_file = self.test_consent_dir / "test.pdf"
        test_file.write_text("test")
        
        # Run the full secure function
        success = secure_consent_storage()
        
        self.assertTrue(success)
        self.assertTrue(self.test_consent_dir.exists())
        self.assertTrue(self.test_gitignore.exists())
        self.assertIn(GITIGNORE_RULE, self.test_gitignore.read_text())
        self.assertEqual(test_file.stat().st_mode & 0o777, 0o600)

if __name__ == "__main__":
    unittest.main()