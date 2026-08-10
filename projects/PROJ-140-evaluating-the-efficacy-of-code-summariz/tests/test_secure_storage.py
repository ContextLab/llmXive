import os
import stat
import tempfile
import shutil
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the functions we want to test
# Note: We are testing the logic, so we might need to mock file system operations
# or run them in a temp directory.
from utils.secure_storage import (
    ensure_consent_directory,
    enforce_file_permissions,
    enforce_directory_permissions,
    ensure_gitignore_exclusion,
    secure_consent_storage,
    CONSENT_DIR,
    GITIGNORE_PATH,
    PERMISSIONS_600
)

class TestSecureStorage(unittest.TestCase):

    def setUp(self):
        """Set up a temporary directory structure for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        
        # We will test logic relative to a temp root to avoid polluting the real project
        # However, the functions use hardcoded paths (Path("data/consent")).
        # To test effectively without changing the code under test, we will:
        # 1. Create the structure in the temp_dir
        # 2. Use monkey-patching or context switching if the code allowed config, 
        #    OR we simply verify the logic by creating the directory structure
        #    and checking the resulting permissions in the temp_dir if we can override paths.
        
        # Since the code uses hardcoded paths, we will test by:
        # 1. Creating a mock environment where "data/consent" points to our temp dir
        # 2. Or, simpler: We test the functions by creating the actual directory 
        #    in the temp dir and verifying permissions, assuming we can run the 
        #    script in a controlled environment.
        
        # Strategy: We will patch the Path class or the global constants if possible,
        # but since they are module-level constants, we'll use a different approach.
        # We will create the directory structure in the temp_dir and then 
        # verify the logic by checking if the functions work correctly on a real path
        # if we can make them point to temp_dir.
        
        # Actually, the cleanest way for this specific code (which uses hardcoded paths)
        # is to run the tests in a temporary directory that acts as the project root.
        # We will change the working directory to a temp dir, create 'data/consent' there.
        
        self.test_project_root = Path(self.temp_dir)
        os.chdir(self.test_project_root)
        
        # Create the data/consent directory manually for testing
        self.consent_dir = self.test_project_root / "data" / "consent"
        self.consent_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a dummy file in consent dir
        self.dummy_file = self.consent_dir / "dummy_consent.txt"
        self.dummy_file.write_text("test")

    def tearDown(self):
        """Clean up the temporary directory."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)

    def test_ensure_consent_directory_exists(self):
        """Test that ensure_consent_directory does nothing if directory exists."""
        # Directory already exists from setUp
        ensure_consent_directory()
        self.assertTrue(self.consent_dir.exists())

    def test_ensure_consent_directory_creates(self):
        """Test that ensure_consent_directory creates the directory if missing."""
        # Remove the directory
        shutil.rmtree(self.consent_dir)
        
        ensure_consent_directory()
        
        self.assertTrue(self.consent_dir.exists())
        # Check permissions (700)
        # Note: os.chmod might behave differently on different OS, but stat check is standard
        dir_stat = os.stat(self.consent_dir)
        # Check if only user bits are set (700 = 0o700)
        mode = dir_stat.st_mode & 0o777
        self.assertEqual(mode, 0o700)

    def test_enforce_file_permissions(self):
        """Test that enforce_file_permissions sets 600."""
        # Set to something else first
        os.chmod(self.dummy_file, 0o777)
        
        enforce_file_permissions(self.dummy_file)
        
        file_stat = os.stat(self.dummy_file)
        mode = file_stat.st_mode & 0o777
        self.assertEqual(mode, 0o600)

    def test_enforce_file_permissions_missing(self):
        """Test that enforce_file_permissions raises FileNotFoundError."""
        missing_file = self.test_project_root / "missing.txt"
        with self.assertRaises(FileNotFoundError):
            enforce_file_permissions(missing_file)

    def test_enforce_directory_permissions(self):
        """Test that enforce_directory_permissions sets 700 on dir and 600 on files."""
        # Reset permissions to something else
        os.chmod(self.consent_dir, 0o777)
        os.chmod(self.dummy_file, 0o777)
        
        enforce_directory_permissions(self.consent_dir)
        
        dir_stat = os.stat(self.consent_dir)
        file_stat = os.stat(self.dummy_file)
        
        self.assertEqual((dir_stat.st_mode & 0o777), 0o700)
        self.assertEqual((file_stat.st_mode & 0o777), 0o600)

    def test_ensure_gitignore_exclusion_adds(self):
        """Test that ensure_gitignore_exclusion adds the entry if missing."""
        gitignore_path = self.test_project_root / ".gitignore"
        gitignore_path.write_text("data/raw/\n")
        
        ensure_gitignore_exclusion()
        
        content = gitignore_path.read_text()
        self.assertIn("data/consent/", content)

    def test_ensure_gitignore_exclusion_skips_existing(self):
        """Test that ensure_gitignore_exclusion does not duplicate entry."""
        gitignore_path = self.test_project_root / ".gitignore"
        gitignore_path.write_text("data/consent/\n")
        
        ensure_gitignore_exclusion()
        
        content = gitignore_path.read_text()
        # Count occurrences
        count = content.count("data/consent/")
        self.assertEqual(count, 1)

    def test_secure_consent_storage_full_flow(self):
        """Test the full secure_consent_storage flow."""
        # Setup: Create a clean state
        if self.consent_dir.exists():
            shutil.rmtree(self.consent_dir)
        self.consent_dir.mkdir(parents=True)
        self.dummy_file = self.consent_dir / "dummy.txt"
        self.dummy_file.write_text("test")
        
        gitignore_path = self.test_project_root / ".gitignore"
        if gitignore_path.exists():
            gitignore_path.unlink()
        
        success = secure_consent_storage()
        
        self.assertTrue(success)
        self.assertTrue(self.consent_dir.exists())
        self.assertTrue(gitignore_path.exists())
        self.assertIn("data/consent/", gitignore_path.read_text())
        
        # Check permissions
        dir_stat = os.stat(self.consent_dir)
        self.assertEqual((dir_stat.st_mode & 0o777), 0o700)
        
        file_stat = os.stat(self.dummy_file)
        self.assertEqual((file_stat.st_mode & 0o777), 0o600)

if __name__ == "__main__":
    unittest.main()
