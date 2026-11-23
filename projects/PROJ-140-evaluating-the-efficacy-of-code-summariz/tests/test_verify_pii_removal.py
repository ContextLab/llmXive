"""
Unit tests for verify_pii_removal.py (T031b).

These tests verify the logic of PII detection and VCS exclusion checks.
"""
import unittest
import os
import sys
import tempfile
import shutil
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.verify_pii_removal import scan_csv_for_pii, check_vcs_exclusion, verify_gitignore_exclusion, PII_PATTERNS

class TestVerifyPIIRemoval(unittest.TestCase):

    def setUp(self):
        """Set up temporary directories and files for testing."""
        self.test_dir = tempfile.mkdtemp()
        self.test_csv_path = Path(self.test_dir) / "test_logs.csv"
        self.test_git_dir = Path(self.test_dir) / "git_repo"
        os.makedirs(self.test_git_dir)

    def tearDown(self):
        """Clean up temporary files."""
        shutil.rmtree(self.test_dir)

    def test_scan_csv_no_pii(self):
        """Test scanning a CSV with no PII returns empty list."""
        content = """participant_id,task_id,timestamp_ms
        P001,T01,123456789
        P002,T02,123456790
        """
        self.test_csv_path.write_text(content)
        
        findings = scan_csv_for_pii(self.test_csv_path)
        self.assertEqual(len(findings), 0)

    def test_scan_csv_with_email(self):
        """Test scanning a CSV with an email address detects it."""
        content = """participant_id,task_id,timestamp_ms
        P001,T01,123456789
        P002,test@example.com,123456790
        """
        self.test_csv_path.write_text(content)
        
        findings = scan_csv_for_pii(self.test_csv_path)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0][2], "email")

    def test_scan_csv_with_ssn(self):
        """Test scanning a CSV with an SSN detects it."""
        content = """participant_id,task_id,timestamp_ms
        P001,T01,123456789
        P002,123-45-6789,123456790
        """
        self.test_csv_path.write_text(content)
        
        findings = scan_csv_for_pii(self.test_csv_path)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0][2], "ssn")

    def test_scan_csv_with_phone(self):
        """Test scanning a CSV with a US phone number detects it."""
        content = """participant_id,task_id,timestamp_ms
        P001,T01,123456789
        P002,555-123-4567,123456790
        """
        self.test_csv_path.write_text(content)
        
        findings = scan_csv_for_pii(self.test_csv_path)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0][2], "phone_us")

    def test_scan_csv_missing_file(self):
        """Test scanning a non-existent file returns empty list and logs error."""
        findings = scan_csv_for_pii(Path("non_existent_file.csv"))
        self.assertEqual(len(findings), 0)

    @patch('subprocess.run')
    def test_check_vcs_exclusion_not_in_history(self, mock_run):
        """Test VCS check when directory is not in history."""
        mock_run.return_value = MagicMock(returncode=0, stdout="")
        
        result = check_vcs_exclusion(Path("data/consent"))
        self.assertTrue(result)

    @patch('subprocess.run')
    def test_check_vcs_exclusion_in_history(self, mock_run):
        """Test VCS check when directory IS in history."""
        mock_run.return_value = MagicMock(returncode=0, stdout="commit abc123...")
        
        result = check_vcs_exclusion(Path("data/consent"))
        self.assertFalse(result)

    @patch('subprocess.run')
    def test_check_vcs_exclusion_git_error(self, mock_run):
        """Test VCS check when git command fails."""
        mock_run.return_value = MagicMock(returncode=1, stderr="fatal: not a git repo")
        
        result = check_vcs_exclusion(Path("data/consent"))
        self.assertTrue(result) # Should return True (pass) on error as per implementation logic

    def test_verify_gitignore_exclusion_found(self):
        """Test .gitignore check when exclusion is present."""
        gitignore_path = Path(self.test_dir) / ".gitignore"
        gitignore_path.write_text("data/consent\n")
        
        # Temporarily change cwd to test_dir to find .gitignore
        original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        try:
            result = verify_gitignore_exclusion(Path("data/consent"))
            self.assertTrue(result)
        finally:
            os.chdir(original_cwd)

    def test_verify_gitignore_exclusion_not_found(self):
        """Test .gitignore check when exclusion is missing."""
        gitignore_path = Path(self.test_dir) / ".gitignore"
        gitignore_path.write_text("*.pyc\n")
        
        original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        try:
            result = verify_gitignore_exclusion(Path("data/consent"))
            self.assertFalse(result)
        finally:
            os.chdir(original_cwd)

    def test_verify_gitignore_no_file(self):
        """Test .gitignore check when .gitignore does not exist."""
        original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        try:
            result = verify_gitignore_exclusion(Path("data/consent"))
            self.assertFalse(result)
        finally:
            os.chdir(original_cwd)

if __name__ == '__main__':
    unittest.main()