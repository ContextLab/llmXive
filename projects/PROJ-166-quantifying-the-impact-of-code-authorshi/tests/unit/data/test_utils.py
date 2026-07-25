import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import subprocess

from code.data.utils import run_command, parse_git_log, run_cloc


class TestRunCommand:
    """Tests for the run_command utility function."""

    def test_successful_command(self):
        """Test run_command with a successful execution."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                stdout=b"output",
                stderr=b"",
                returncode=0
            )
            
            stdout, stderr, code = run_command(["echo", "hello"])
            
            assert stdout == "output"
            assert stderr == ""
            assert code == 0

    def test_command_failure(self):
        """Test run_command when the command fails."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                stdout=b"",
                stderr=b"error",
                returncode=1
            )
            
            stdout, stderr, code = run_command(["false"])
            
            assert stdout == ""
            assert stderr == "error"
            assert code == 1

    def test_command_timeout(self):
        """Test run_command when the command times out."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(cmd=["sleep", "10"], timeout=1)
            
            stdout, stderr, code = run_command(["sleep", "10"], timeout=1)
            
            assert stdout == ""
            assert "Command timed out" in stderr
            assert code == -1


class TestParseGitLog:
    """Tests for the parse_git_log utility function."""

    def test_parse_git_log_success(self):
        """Test parse_git_log with successful git log output."""
        mock_path = Path("/fake/repo")
        
        with patch('code.data.utils.run_command') as mock_run:
            mock_run.return_value = ("author1@example.com\nauthor2@example.com\nauthor1@example.com\n", "", 0)
            
            authors = parse_git_log(mock_path, format_str="%ae")
            
            assert len(authors) == 3
            assert "author1@example.com" in authors
            assert "author2@example.com" in authors

    def test_parse_git_log_empty(self):
        """Test parse_git_log when git log returns empty output."""
        mock_path = Path("/fake/repo")
        
        with patch('code.data.utils.run_command') as mock_run:
            mock_run.return_value = ("", "", 0)
            
            authors = parse_git_log(mock_path)
            
            assert authors == []

    def test_parse_git_log_failure(self):
        """Test parse_git_log when git command fails."""
        mock_path = Path("/fake/repo")
        
        with patch('code.data.utils.run_command') as mock_run:
            mock_run.return_value = ("", "fatal: not a git repository", 128)
            
            authors = parse_git_log(mock_path)
            
            assert authors == []


class TestRunCloc:
    """Tests for the run_cloc utility function."""

    def test_run_cloc_success(self):
        """Test run_cloc with successful output including SUM line."""
        mock_path = Path("/fake/repo")
        mock_output = """
         Language         files          blank        comment           code
        ----------------------------------------------------------------------------
        Python              10            100              50            1000
        ----------------------------------------------------------------------------
        SUM:                10            100              50            1000
        """
        
        with patch('code.data.utils.run_command') as mock_run:
            mock_run.return_value = (mock_output, "", 0)
            
            result = run_cloc(mock_path)
            
            assert result['success'] is True
            assert result['total_lines'] == 1000
            assert result['kloc'] == 1.0

    def test_run_cloc_manual_sum(self):
        """Test run_cloc when SUM line is missing but data exists."""
        mock_path = Path("/fake/repo")
        mock_output = """
         Language         files          blank        comment           code
        ----------------------------------------------------------------------------
        Python              10            100              50            500
        JavaScript           5             50              25            300
        """
        
        with patch('code.data.utils.run_command') as mock_run:
            mock_run.return_value = (mock_output, "", 0)
            
            result = run_cloc(mock_path)
            
            assert result['success'] is True
            assert result['total_lines'] == 800
            assert result['kloc'] == 0.8

    def test_run_cloc_failure(self):
        """Test run_cloc when cloc command fails."""
        mock_path = Path("/fake/repo")
        
        with patch('code.data.utils.run_command') as mock_run:
            mock_run.return_value = ("", "cloc: command not found", 127)
            
            result = run_cloc(mock_path)
            
            assert result['success'] is False
            assert result['total_lines'] == 0
            assert result['kloc'] == 0.0

    def test_run_cloc_empty_output(self):
        """Test run_cloc with empty output."""
        mock_path = Path("/fake/repo")
        
        with patch('code.data.utils.run_command') as mock_run:
            mock_run.return_value = ("", "", 0)
            
            result = run_cloc(mock_path)
            
            assert result['success'] is True
            assert result['total_lines'] == 0
            assert result['kloc'] == 0.0