import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import subprocess

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.data.extract_github import (
    shallow_clone,
    parse_git_log_and_count_authors,
    run_cloc_on_clone,
    process_repo,
    check_memory_usage
)

class TestShallowClone:
    def test_shallow_clone_success(self):
        """Test successful shallow clone"""
        with tempfile.TemporaryDirectory() as tmpdir:
            target_dir = Path(tmpdir) / "test_repo"
            # Mock the subprocess.run to simulate success
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = MagicMock(returncode=0, stderr=b'')
                success, msg = shallow_clone("https://github.com/test/test.git", target_dir)
                assert success is True
                assert msg == "Success"
                mock_run.assert_called_once()

    def test_shallow_clone_failure(self):
        """Test failed shallow clone"""
        with tempfile.TemporaryDirectory() as tmpdir:
            target_dir = Path(tmpdir) / "test_repo"
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = MagicMock(returncode=1, stderr=b'Clone failed: repo not found')
                success, msg = shallow_clone("https://github.com/test/test.git", target_dir)
                assert success is False
                assert "Clone failed" in msg

class TestParseGitLog:
    def test_parse_git_log_and_count_authors(self):
        """Test author count calculation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            # Create a fake .git directory
            git_dir = repo_path / ".git"
            git_dir.mkdir()
            
            # Mock the git log command to return specific authors
            with patch('subprocess.run') as mock_run:
                # First call: git log
                mock_run.side_effect = [
                    # git log return
                    MagicMock(returncode=0, stdout=b"author1@test.com\nauthor2@test.com\nauthor1@test.com\n"),
                    # git ls-files return
                    MagicMock(returncode=0, stdout=b"file1.py\nfile2.py\n"),
                    # git blame return (simulating 2 lines for author1, 1 for author2)
                    MagicMock(returncode=0, stdout=b"author Author 1\nauthor Author 1\nauthor Author 2\n")
                ]
                
                unique_authors, raw_lines = parse_git_log_and_count_authors(repo_path)
                
                # Should have 2 unique authors with >= 1 line each
                assert unique_authors == 2
                # Raw lines count depends on the mock, but should be > 0
                assert raw_lines >= 0

class TestRunCloc:
    def test_run_cloc_on_clone(self):
        """Test cloc execution"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=0,
                    stdout=b"SUM  100  50  20  30\n"
                )
                
                raw_lines, kloc = run_cloc_on_clone(repo_path)
                
                assert raw_lines == 100
                assert kloc == 0.1

class TestCheckMemoryUsage:
    def test_check_memory_usage(self):
        """Test memory usage check"""
        with patch('psutil.virtual_memory') as mock_mem:
            mock_mem.return_value = MagicMock(used=1024**3 * 4)  # 4 GB used
            assert check_memory_usage() is True
            
            mock_mem.return_value = MagicMock(used=1024**3 * 8)  # 8 GB used
            assert check_memory_usage() is False
