import os
import unittest
import tempfile
import shutil
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the function to test
# Assuming the file is in code/metrics.py
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))
from metrics import calc_quality_rate

class TestCalcQualityRate(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.repo_path = Path(self.temp_dir) / "test_repo"
        self.repo_path.mkdir()
        
        # Initialize a git repo
        subprocess.run(["git", "init"], cwd=self.repo_path, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=self.repo_path, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=self.repo_path, check=True, capture_output=True)
        
        # Create a dummy file and commit
        test_file = self.repo_path / "test.py"
        test_file.write_text("# Simple test\nprint('hello')\n")
        subprocess.run(["git", "add", "."], cwd=self.repo_path, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=self.repo_path, check=True, capture_output=True)
        
        # Create a second commit
        test_file.write_text("# Updated test\nprint('hello world')\n")
        subprocess.run(["git", "add", "."], cwd=self.repo_path, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Second commit"], cwd=self.repo_path, check=True, capture_output=True)
        
        # Create manual labels file
        self.manual_labels_path = Path(self.temp_dir) / "manual_labels.csv"
        with open(self.manual_labels_path, "w", newline="") as f:
            f.write("repo_id,commit_hash,label,source\n")
            # Get the hash of the second commit
            result = subprocess.run(["git", "log", "-1", "--format=%H"], cwd=self.repo_path, capture_output=True, text=True, check=True)
            hash_val = result.stdout.strip()
            f.write(f"test_repo,{hash_val},bug_fix,manual_review\n")
            f.write(f"test_repo,non_existent_hash,not_bug_fix,manual_review\n")

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    @patch('metrics.subprocess.run')
    def test_calc_quality_rate_with_pylint(self, mock_run):
        """Test calc_quality_rate runs pylint and calculates ratio."""
        # Mock subprocess.run to return a clean pylint output (no errors)
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_run.return_value = mock_result
        
        result = calc_quality_rate(str(self.repo_path), str(self.manual_labels_path))
        
        self.assertIn('quality_rate', result)
        self.assertIn('error_rate', result)
        self.assertEqual(result['sample_size'], 10) # Default n=10 from CommitSampler
        
        # Since we mocked pylint to return 0 (no errors), quality_rate should be 1.0
        self.assertEqual(result['quality_rate'], 1.0)
        self.assertEqual(result['error_rate'], 0.0)

    @patch('metrics.subprocess.run')
    def test_calc_quality_rate_with_errors(self, mock_run):
        """Test calc_quality_rate detects errors."""
        # Mock subprocess.run to return an error
        mock_result = MagicMock()
        mock_result.returncode = 2
        mock_result.stdout = "E: 1:0: Some error"
        mock_run.return_value = mock_result
        
        result = calc_quality_rate(str(self.repo_path), str(self.manual_labels_path))
        
        self.assertGreater(result['error_rate'], 0.0)
        self.assertLess(result['quality_rate'], 1.0)

    def test_calc_quality_rate_no_manual_labels(self):
        """Test calc_quality_rate handles missing manual labels."""
        result = calc_quality_rate(str(self.repo_path), "non_existent_path.csv")
        
        self.assertEqual(result['validation_status'], 'skipped')
        self.assertIn('quality_rate', result)

    def test_calc_quality_rate_empty_repo(self):
        """Test calc_quality_rate handles empty repo (no commits)."""
        empty_repo = Path(self.temp_dir) / "empty_repo"
        empty_repo.mkdir()
        subprocess.run(["git", "init"], cwd=empty_repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=empty_repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=empty_repo, check=True, capture_output=True)
        
        result = calc_quality_rate(str(empty_repo), str(self.manual_labels_path))
        
        self.assertEqual(result['sample_size'], 0)
        self.assertEqual(result['validation_status'], 'skipped')

if __name__ == '__main__':
    unittest.main()