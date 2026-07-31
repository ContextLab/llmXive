"""
Unit tests for setup_type_check.py (T031b)

These tests verify the type checking utility functionality.
"""
import os
import sys
import tempfile
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.setup_type_check import run_mypy_check, main


class TestSetupTypeCheck:
    """Test cases for the type checking utility."""

    def test_run_mypy_check_creates_log_file(self):
        """Test that run_mypy_check creates the output log file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Mock get_project_root to return our temp directory
            with patch('code.setup_type_check.get_project_root', return_value=tmpdir_path):
                # Create necessary subdirectories
                (tmpdir_path / "code").mkdir()
                (tmpdir_path / "data" / "processed").mkdir(parents=True)

                # Run the function (this will likely fail if mypy isn't installed,
                # but should still create the log file)
                result = run_mypy_check()

                # Verify log file was created
                log_path = tmpdir_path / "data" / "processed" / "type_log.txt"
                assert log_path.exists(), "Log file should be created even if mypy fails"

                # Verify log file has content
                with open(log_path, 'r') as f:
                    content = f.read()
                    assert "MYPI TYPE CHECK LOG" in content

    def test_run_mypy_check_with_mocked_success(self):
        """Test successful mypy run with mocked subprocess."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Mock get_project_root
            with patch('code.setup_type_check.get_project_root', return_value=tmpdir_path):
                # Create necessary subdirectories
                (tmpdir_path / "code").mkdir()
                (tmpdir_path / "data" / "processed").mkdir(parents=True)

                # Mock subprocess.run to simulate success
                mock_result = MagicMock()
                mock_result.returncode = 0
                mock_result.stdout = "Success: No type errors found.\n"
                mock_result.stderr = ""

                with patch('code.setup_type_check.subprocess.run', return_value=mock_result):
                    result = run_mypy_check()

                    assert result == 0

                    # Verify log file content
                    log_path = tmpdir_path / "data" / "processed" / "type_log.txt"
                    with open(log_path, 'r') as f:
                        content = f.read()
                        assert "TYPE CHECK PASSED" in content

    def test_run_mypy_check_with_mocked_failure(self):
        """Test failed mypy run with mocked subprocess."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Mock get_project_root
            with patch('code.setup_type_check.get_project_root', return_value=tmpdir_path):
                # Create necessary subdirectories
                (tmpdir_path / "code").mkdir()
                (tmpdir_path / "data" / "processed").mkdir(parents=True)

                # Mock subprocess.run to simulate failure
                mock_result = MagicMock()
                mock_result.returncode = 1
                mock_result.stdout = "code/example.py:10: error: Incompatible types\n"
                mock_result.stderr = ""

                with patch('code.setup_type_check.subprocess.run', return_value=mock_result):
                    result = run_mypy_check()

                    assert result == 1

                    # Verify log file content
                    log_path = tmpdir_path / "data" / "processed" / "type_log.txt"
                    with open(log_path, 'r') as f:
                        content = f.read()
                        assert "TYPE CHECK FAILED" in content
                        assert "Incompatible types" in content

    def test_run_mypy_check_timeout_handling(self):
        """Test timeout handling in run_mypy_check."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Mock get_project_root
            with patch('code.setup_type_check.get_project_root', return_value=tmpdir_path):
                # Create necessary subdirectories
                (tmpdir_path / "code").mkdir()
                (tmpdir_path / "data" / "processed").mkdir(parents=True)

                # Mock subprocess.run to raise TimeoutExpired
                with patch('code.setup_type_check.subprocess.run', side_effect=subprocess.TimeoutExpired(cmd=['mypy'], timeout=300)):
                    result = run_mypy_check()

                    assert result == 1

                    # Verify log file content
                    log_path = tmpdir_path / "data" / "processed" / "type_log.txt"
                    with open(log_path, 'r') as f:
                        content = f.read()
                        assert "timed out" in content.lower()

    def test_run_mypy_check_file_not_found(self):
        """Test handling of missing mypy executable."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Mock get_project_root
            with patch('code.setup_type_check.get_project_root', return_value=tmpdir_path):
                # Create necessary subdirectories
                (tmpdir_path / "code").mkdir()
                (tmpdir_path / "data" / "processed").mkdir(parents=True)

                # Mock subprocess.run to raise FileNotFoundError
                with patch('code.setup_type_check.subprocess.run', side_effect=FileNotFoundError("mypy not found")):
                    result = run_mypy_check()

                    assert result == 1

                    # Verify log file content
                    log_path = tmpdir_path / "data" / "processed" / "type_log.txt"
                    with open(log_path, 'r') as f:
                        content = f.read()
                        assert "mypy not found" in content

    def test_main_returns_exit_code(self):
        """Test that main() returns the correct exit code."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Mock get_project_root
            with patch('code.setup_type_check.get_project_root', return_value=tmpdir_path):
                # Create necessary subdirectories
                (tmpdir_path / "code").mkdir()
                (tmpdir_path / "data" / "processed").mkdir(parents=True)

                # Mock subprocess.run to simulate success
                mock_result = MagicMock()
                mock_result.returncode = 0
                mock_result.stdout = "Success\n"
                mock_result.stderr = ""

                with patch('code.setup_type_check.subprocess.run', return_value=mock_result):
                    result = main()
                    assert result == 0

                # Mock subprocess.run to simulate failure
                mock_result.returncode = 1
                mock_result.stdout = "Error\n"

                with patch('code.setup_type_check.subprocess.run', return_value=mock_result):
                    result = main()
                    assert result == 1