"""
Unit tests for the verify_formatting module.
"""
import subprocess
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys
import tempfile
import os

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from verify_formatting import run_command, main


class TestRunCommand:
    def test_successful_command(self):
        """Test run_command with a successful command."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="Success",
                stderr=""
            )
            result = run_command(["echo", "test"], "Test command")
            assert result is True
            mock_run.assert_called_once()

    def test_failed_command(self):
        """Test run_command with a failing command."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout="",
                stderr="Error"
            )
            result = run_command(["false"], "Test command")
            assert result is False

    def test_exception_handling(self):
        """Test run_command when an exception occurs."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = Exception("Network error")
            result = run_command(["curl", "fail"], "Test command")
            assert result is False


class TestMain:
    def test_missing_code_directory(self, tmp_path):
        """Test main() when code directory is missing."""
        # Create a temporary directory structure without 'code'
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        
        # Mock Path(__file__).parent.parent to point to tmp_path
        with patch("verify_formatting.Path") as mock_path:
            mock_instance = MagicMock()
            mock_instance.parent.parent = tmp_path
            mock_path.return_value = mock_instance
            
            # Mock the existence check
            with patch("pathlib.Path.exists") as mock_exists:
                # First call (code_dir) returns False, second (tests_dir) returns True
                mock_exists.side_effect = [False, True]
                
                result = main()
                assert result == 1

    def test_missing_tests_directory(self, tmp_path):
        """Test main() when tests directory is missing."""
        code_dir = tmp_path / "code"
        code_dir.mkdir()
        
        with patch("verify_formatting.Path") as mock_path:
            mock_instance = MagicMock()
            mock_instance.parent.parent = tmp_path
            mock_path.return_value = mock_instance
            
            with patch("pathlib.Path.exists") as mock_exists:
                mock_exists.side_effect = [True, False]
                
                result = main()
                assert result == 1

    def test_all_checks_pass(self, tmp_path, capsys):
        """Test main() when all formatting checks pass."""
        code_dir = tmp_path / "code"
        tests_dir = tmp_path / "tests"
        code_dir.mkdir()
        tests_dir.mkdir()
        
        # Create dummy files to satisfy directory existence
        (code_dir / "__init__.py").touch()
        (tests_dir / "__init__.py").touch()
        
        with patch("verify_formatting.Path") as mock_path:
            mock_instance = MagicMock()
            mock_instance.parent.parent = tmp_path
            mock_path.return_value = mock_instance
            
            with patch("pathlib.Path.exists") as mock_exists:
                mock_exists.return_value = True
                
                with patch("verify_formatting.run_command") as mock_run_cmd:
                    # Both checks pass
                    mock_run_cmd.return_value = True
                    
                    result = main()
                    assert result == 0
                    
                    # Verify run_command was called twice
                    assert mock_run_cmd.call_count == 2

    def test_black_check_fails(self, tmp_path):
        """Test main() when black check fails."""
        code_dir = tmp_path / "code"
        tests_dir = tmp_path / "tests"
        code_dir.mkdir()
        tests_dir.mkdir()
        
        (code_dir / "__init__.py").touch()
        (tests_dir / "__init__.py").touch()
        
        with patch("verify_formatting.Path") as mock_path:
            mock_instance = MagicMock()
            mock_instance.parent.parent = tmp_path
            mock_path.return_value = mock_instance
            
            with patch("pathlib.Path.exists") as mock_exists:
                mock_exists.return_value = True
                
                with patch("verify_formatting.run_command") as mock_run_cmd:
                    # Black fails, isort passes
                    def side_effect(*args, **kwargs):
                        if "black" in str(args):
                            return False
                        return True
                    
                    mock_run_cmd.side_effect = side_effect
                    
                    result = main()
                    assert result == 1