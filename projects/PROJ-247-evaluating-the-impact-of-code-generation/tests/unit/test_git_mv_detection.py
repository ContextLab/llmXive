"""
Unit tests for T012b: Git MV Detection.

Tests the logic for detecting structural refactors using git log --follow.
"""
import pytest
import os
import tempfile
import subprocess
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
from code.utils.git_mv_detector import GitMvDetector, run_refactor_verification

class TestGitMvDetector:
    
    @pytest.fixture
    def temp_repo(self):
        """Create a temporary git repository with some history."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            
            # Initialize git repo
            subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_path, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_path, check=True, capture_output=True)
            
            # Create a file
            file_path = repo_path / "original_file.py"
            file_path.write_text("def hello(): pass\n")
            
            subprocess.run(["git", "add", "."], cwd=repo_path, check=True, capture_output=True)
            subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo_path, check=True, capture_output=True)
            
            yield repo_path, "original_file.py"

    def test_no_history(self, temp_repo):
        """Test behavior when file has no history."""
        repo_path, _ = temp_repo
        detector = GitMvDetector(str(repo_path))
        
        # Query a non-existent file
        result = detector.check_refactor_exclusion("block_123", "non_existent.py")
        
        # Should return None (not excluded) because we can't verify a refactor
        assert result is None

    def test_no_rename(self, temp_repo):
        """Test behavior when file has history but no rename."""
        repo_path, file_path = temp_repo
        
        # Modify the file
        (repo_path / file_path).write_text("def hello(): pass\n# Comment\n")
        subprocess.run(["git", "add", "."], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Modify file"], cwd=repo_path, check=True, capture_output=True)
        
        detector = GitMvDetector(str(repo_path))
        result = detector.check_refactor_exclusion("block_123", file_path)
        
        # Should return None (not excluded)
        assert result is None

    def test_rename_same_directory(self, temp_repo):
        """Test detection of rename within the same directory."""
        repo_path, file_path = temp_repo
        
        # Rename file within same directory
        new_path = "renamed_file.py"
        subprocess.run(["git", "mv", file_path, new_path], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Rename file"], cwd=repo_path, check=True, capture_output=True)
        
        detector = GitMvDetector(str(repo_path))
        
        # Query using the NEW path (current state)
        result = detector.check_refactor_exclusion("block_123", new_path)
        
        # Same directory rename should NOT be excluded (depth change = 0)
        assert result is None

    def test_rename_different_directory_deep(self, temp_repo):
        """Test detection of rename to a different directory (structural refactor)."""
        repo_path, file_path = temp_repo
        
        # Create a deep directory structure
        deep_dir = repo_path / "src" / "deep" / "nested"
        deep_dir.mkdir(parents=True)
        new_path = "src/deep/nested/renamed_file.py"
        
        subprocess.run(["git", "mv", file_path, new_path], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Move to deep directory"], cwd=repo_path, check=True, capture_output=True)
        
        detector = GitMvDetector(str(repo_path))
        
        # Query using the NEW path
        result = detector.check_refactor_exclusion("block_123", new_path)
        
        # Should be excluded due to directory level change
        assert result is not None
        assert "Directory level change" in result['reason']
        assert result['old_path'] == file_path
        assert result['new_path'] == new_path

    def test_run_refactor_verification(self, temp_repo):
        """Test the full pipeline execution."""
        repo_path, file_path = temp_repo
        
        # Create a deep move
        new_path = "src/deep/nested/renamed_file.py"
        deep_dir = repo_path / "src" / "deep" / "nested"
        deep_dir.mkdir(parents=True)
        subprocess.run(["git", "mv", file_path, new_path], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Move to deep directory"], cwd=repo_path, check=True, capture_output=True)
        
        # Create a mock CSV input
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("block_id,file_path,start_line,end_line,language,content_hash\n")
            f.write("block_1,src/deep/nested/renamed_file.py,1,5,python,abc123\n")
            f.write("block_2,original_file.py,1,5,python,def456\n") # This file doesn't exist in history anymore
            csv_path = f.name

        log_path = tempfile.mktemp(suffix='.log')
        report_path = tempfile.mktemp(suffix='.json')

        try:
            run_refactor_verification(
                repo_path=str(repo_path),
                code_blocks_csv_path=csv_path,
                log_path=log_path,
                report_path=report_path
            )

            # Check log file exists and has content
            assert os.path.exists(log_path)
            with open(log_path, 'r') as f:
                log_content = f.read()
                assert "block_1" in log_content # Should be excluded
                assert "Directory level change" in log_content

            # Check report file
            assert os.path.exists(report_path)
            with open(report_path, 'r') as f:
                report = json.load(f)
                assert report['total_excluded'] == 1
                assert report['inclusion_rate'] < 1.0

        finally:
            os.unlink(csv_path)
            if os.path.exists(log_path):
                os.unlink(log_path)
            if os.path.exists(report_path):
                os.unlink(report_path)

    def test_deferred_pass_rate(self, temp_repo):
        """
        Verify that the 'deferred' pass rate logic holds.
        The task description mentions 'ensuring [deferred] pass rate'.
        This test ensures that blocks with ambiguous history are NOT excluded (deferred decision).
        """
        repo_path, file_path = temp_repo
        
        # Just a normal modification, no rename
        (repo_path / file_path).write_text("def hello(): pass\n# More code\n")
        subprocess.run(["git", "add", "."], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Update"], cwd=repo_path, check=True, capture_output=True)
        
        detector = GitMvDetector(str(repo_path))
        
        # This should NOT be excluded
        result = detector.check_refactor_exclusion("block_deferred", file_path)
        
        # If result is None, it means we did NOT exclude it (deferred to next check or kept)
        # In the context of "deferred pass rate", this implies the block passed the exclusion check.
        assert result is None

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
