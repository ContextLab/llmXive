import os
import sys
import tempfile
import subprocess
import csv
import json
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.git_mv_detector import GitMvDetector, run_refactor_verification

class TestGitMvDetector(unittest.TestCase):

    def setUp(self):
        # Create a temporary directory structure for testing
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_path = Path(self.test_dir.name) / "repo"
        self.repo_path.mkdir()
        
        # Initialize git repo
        subprocess.run(["git", "init"], cwd=self.repo_path, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=self.repo_path, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=self.repo_path, check=True, capture_output=True)

        # Create initial file
        initial_file = self.repo_path / "src" / "old_file.py"
        initial_file.parent.mkdir(parents=True, exist_ok=True)
        initial_file.write_text("def hello(): pass\n")
        
        subprocess.run(["git", "add", "."], cwd=self.repo_path, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=self.repo_path, check=True, capture_output=True)

        # Simulate a rename (git mv)
        new_file = self.repo_path / "src" / "new_file.py"
        subprocess.run(["git", "mv", "src/old_file.py", "src/new_file.py"], cwd=self.repo_path, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Rename file"], cwd=self.repo_path, check=True, capture_output=True)

        # Create code blocks CSV
        self.blocks_csv = Path(self.test_dir.name) / "code_blocks.csv"
        with open(self.blocks_csv, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["block_id", "file_path", "start_line", "end_line", "language", "content_hash"])
            writer.writerow(["block_1", "src/old_file.py", "1", "1", "python", "hash123"])
            writer.writerow(["block_2", "src/new_file.py", "1", "1", "python", "hash456"])
            writer.writerow(["block_3", "src/unchanged.py", "1", "1", "python", "hash789"]) # Unchanged file

        self.log_path = Path(self.test_dir.name) / "logs" / "exclusions.log"
        self.report_path = Path(self.test_dir.name) / "logs" / "report.json"

    def tearDown(self):
        self.test_dir.cleanup()

    def test_detect_rename(self):
        """Test that the detector identifies a renamed file."""
        detector = GitMvDetector(str(self.repo_path), log_path=str(self.log_path))
        
        # Block 1 refers to old path. History should show it moved to new path.
        exclusion = detector.detect_refactor("block_1", "src/old_file.py")
        
        self.assertIsNotNone(exclusion)
        self.assertEqual(exclusion["block_id"], "block_1")
        self.assertEqual(exclusion["old_path"], "src/old_file.py")
        self.assertEqual(exclusion["new_path"], "src/new_file.py")
        self.assertIn("Rename", exclusion["reason"])

    def test_no_rename(self):
        """Test that unchanged files are not flagged."""
        detector = GitMvDetector(str(self.repo_path), log_path=str(self.log_path))
        
        # Create a dummy unchanged file for the test to exist in git
        unchanged_file = self.repo_path / "src" / "unchanged.py"
        unchanged_file.write_text("def world(): pass\n")
        subprocess.run(["git", "add", "."], cwd=self.repo_path, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Add unchanged"], cwd=self.repo_path, check=True, capture_output=True)

        exclusion = detector.detect_refactor("block_3", "src/unchanged.py")
        self.assertIsNone(exclusion)

    def test_run_refactor_verification(self):
        """Test the full pipeline function."""
        result = run_refactor_verification(
            str(self.blocks_csv),
            str(self.repo_path),
            str(self.log_path),
            str(self.report_path)
        )

        self.assertIn("total_blocks_processed", result)
        self.assertIn("blocks_excluded", result)
        self.assertGreater(result["blocks_excluded"], 0)

        # Verify log file content
        self.assertTrue(self.log_path.exists())
        with open(self.log_path, 'r') as f:
            log_content = f.read()
            self.assertIn("block_1", log_content)
            self.assertIn("src/old_file.py", log_content)

        # Verify report content
        self.assertTrue(self.report_path.exists())
        with open(self.report_path, 'r') as f:
            report_data = json.load(f)
            self.assertEqual(report_data["blocks_excluded"], 1)
            self.assertEqual(report_data["exclusions"][0]["block_id"], "block_1")

if __name__ == "__main__":
    unittest.main()