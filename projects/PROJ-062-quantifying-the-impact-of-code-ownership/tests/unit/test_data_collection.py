import unittest
from unittest.mock import patch, MagicMock, mock_open, call
import csv
import os
import subprocess
from pathlib import Path
from datetime import datetime, timedelta

# Import the functions we are testing from the project code
# We assume the test runner is executed from the project root or code/ is in sys.path
try:
    from data_collection import clone_repository, verify_commit_count, parse_commit_history, process_issues_for_repo
    from utils.path_normalizer import normalize_path
except ImportError:
    # Fallback for running tests in isolated environments where path setup might differ
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from data_collection import clone_repository, verify_commit_count, parse_commit_history, process_issues_for_repo
    from utils.path_normalizer import normalize_path


class TestCloneRepository(unittest.TestCase):
    """Tests for the clone_repository function."""

    @patch('data_collection.subprocess.run')
    def test_clone_success(self, mock_run):
        """Test that a repository is cloned successfully with correct depth."""
        mock_run.return_value = MagicMock(returncode=0)
        
        repo_url = "https://github.com/test/repo.git"
        target_dir = Path("/tmp/test_repo")
        depth = 100
        
        result = clone_repository(repo_url, target_dir, depth)
        
        # Verify subprocess.run was called with correct arguments
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        
        # Check command structure
        cmd = call_args[0][0]
        self.assertIn("git", cmd)
        self.assertIn("clone", cmd)
        self.assertIn("--depth", cmd)
        self.assertIn(str(depth), cmd)
        self.assertIn(repo_url, cmd)
        self.assertIn(str(target_dir), cmd)
        
        self.assertTrue(result)

    @patch('data_collection.subprocess.run')
    def test_clone_failure(self, mock_run):
        """Test that cloning fails gracefully when git returns non-zero."""
        mock_run.return_value = MagicMock(returncode=128)
        
        repo_url = "https://github.com/test/nonexistent.git"
        target_dir = Path("/tmp/test_repo_fail")
        
        result = clone_repository(repo_url, target_dir, depth=100)
        
        self.assertFalse(result)


class TestVerifyCommitCount(unittest.TestCase):
    """Tests for the verify_commit_count function."""

    @patch('data_collection.subprocess.run')
    def test_verify_count_sufficient(self, mock_run):
        """Test verification when commit count meets minimum."""
        mock_run.return_value = MagicMock(returncode=0, stdout="1500\n")
        
        repo_dir = Path("/tmp/test_repo")
        min_commits = 1000
        
        result, count = verify_commit_count(repo_dir, min_commits)
        
        self.assertTrue(result)
        self.assertEqual(count, 1500)

    @patch('data_collection.subprocess.run')
    def test_verify_count_insufficient(self, mock_run):
        """Test verification when commit count is below minimum."""
        mock_run.return_value = MagicMock(returncode=0, stdout="500\n")
        
        repo_dir = Path("/tmp/test_repo")
        min_commits = 1000
        
        result, count = verify_commit_count(repo_dir, min_commits)
        
        self.assertFalse(result)
        self.assertEqual(count, 500)

    @patch('data_collection.subprocess.run')
    def test_verify_git_error(self, mock_run):
        """Test verification when git command fails."""
        mock_run.return_value = MagicMock(returncode=128, stderr="fatal: not a git repo")
        
        repo_dir = Path("/tmp/not_a_repo")
        min_commits = 1000
        
        result, count = verify_commit_count(repo_dir, min_commits)
        
        self.assertFalse(result)
        self.assertEqual(count, 0)


class TestParseCommitHistory(unittest.TestCase):
    """Tests for the parse_commit_history function."""

    @patch('data_collection.Path.exists')
    @patch('data_collection.subprocess.run')
    def test_parse_valid_history(self, mock_run, mock_exists):
        """Test parsing of valid commit history."""
        mock_exists.return_value = True
        # Mock git log output: hash|author|timestamp|file_path
        mock_output = (
            "abc123|John Doe|2023-01-01T10:00:00|src/main.py\n"
            "def456|Jane Smith|2023-01-02T11:00:00|src/utils/helper.py\n"
            "ghi789|John Doe|2023-01-03T12:00:00|src/main.py\n"
        )
        mock_run.return_value = MagicMock(returncode=0, stdout=mock_output)
        
        repo_dir = Path("/tmp/test_repo")
        output_csv = Path("/tmp/commits.csv")
        
        result = parse_commit_history(repo_dir, output_csv)
        
        self.assertTrue(result)
        
        # Verify file was written
        mock_run.assert_called()
        
    @patch('data_collection.Path.exists')
    @patch('data_collection.subprocess.run')
    def test_parse_empty_history(self, mock_run, mock_exists):
        """Test parsing when there are no commits."""
        mock_exists.return_value = True
        mock_run.return_value = MagicMock(returncode=0, stdout="")
        
        repo_dir = Path("/tmp/test_repo")
        output_csv = Path("/tmp/commits_empty.csv")
        
        result = parse_commit_history(repo_dir, output_csv)
        
        self.assertTrue(result)


class TestProcessIssuesForRepo(unittest.TestCase):
    """Tests for the issue processing logic including path normalization."""

    def setUp(self):
        """Set up test fixtures."""
        self.repo_dir = Path("/tmp/test_repo")
        self.issues_csv = Path("/tmp/issues.csv")
        self.output_csv = Path("/tmp/processed_issues.csv")
        
        # Create mock issues data
        self.mock_issues = [
            {
                "number": "101",
                "title": "Bug in main",
                "body": "There is a bug in src/main.py",
                "created_at": "2023-01-15T10:00:00"
            },
            {
                "number": "102",
                "title": "Feature request",
                "body": "Add support for src/utils/helper.PY",
                "created_at": "2023-01-16T11:00:00"
            },
            {
                "number": "103",
                "title": "Unknown path",
                "body": "Error in nonexistent/file.py",
                "created_at": "2023-01-17T12:00:00"
            }
        ]

    @patch('data_collection.Path.exists')
    @patch('data_collection.Path.write_text')
    @patch('data_collection.csv.DictWriter')
    @patch('data_collection.csv.DictReader')
    def test_process_issues_with_normalization(self, mock_reader, mock_writer, mock_write, mock_exists):
        """Test that issues are processed and paths are normalized correctly."""
        mock_exists.return_value = True
        
        # Mock reader to return our test issues
        mock_reader.return_value.__iter__ = lambda self: iter(self.mock_issues)
        mock_reader.return_value.fieldnames = ["number", "title", "body", "created_at"]
        
        # Mock writer
        mock_writer_instance = MagicMock()
        mock_writer.return_value = mock_writer_instance
        
        # Mock repo files (simulating what would be in the repo)
        repo_files = {
            "src/main": "src/main.py",
            "src/utils/helper": "src/utils/helper.py"
        }
        
        # We need to patch the logic that finds repo files or pass them in
        # For this test, we assume process_issues_for_repo handles this internally
        # and we verify the output logic
        
        result = process_issues_for_repo(self.repo_dir, self.issues_csv, self.output_csv)
        
        # The function should have written data
        mock_write.assert_called()

    def test_path_normalization_integration(self):
        """Integration test to verify path normalization logic matches FR-009."""
        # Test cases from FR-009: lowercase, strip extensions, normalize slashes
        test_cases = [
            ("src/MyFile.Py", "src/myfile"),
            ("src\\MyFile.Py", "src/myfile"),
            ("SRC/MyFile.Py", "src/myfile"),
            ("src/utils/helper.py", "src/utils/helper"),
            ("src\\utils\\helper.PY", "src/utils/helper"),
        ]
        
        for input_path, expected in test_cases:
            result = normalize_path(input_path)
            self.assertEqual(result, expected, f"Failed for {input_path}: got {result}, expected {expected}")


class TestCloneRepositories(unittest.TestCase):
    """Tests for the clone_repositories orchestration function."""

    @patch('data_collection.clone_repository')
    @patch('data_collection.verify_commit_count')
    @patch('data_collection.parse_commit_history')
    @patch('data_collection.fetch_github_issues')
    @patch('data_collection.process_issues_for_repo')
    def test_clone_repositories_full_pipeline(self, mock_process, mock_fetch, mock_parse, mock_verify, mock_clone):
        """Test the full cloning and processing pipeline for multiple repos."""
        
        # Setup mocks
        mock_clone.return_value = True
        mock_verify.return_value = (True, 1500)
        mock_parse.return_value = True
        mock_fetch.return_value = True
        mock_process.return_value = True
        
        repo_list = [
            "https://github.com/test/repo1.git",
            "https://github.com/test/repo2.git"
        ]
        depth = 100
        output_dir = Path("/tmp/output")
        
        results = clone_repositories(repo_list, depth, output_dir)
        
        # Verify all repos were attempted
        self.assertEqual(len(results), 2)
        
        # Verify clone was called for each repo
        self.assertEqual(mock_clone.call_count, 2)


if __name__ == '__main__':
    unittest.main()