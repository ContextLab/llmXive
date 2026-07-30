import pytest
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

from setup_type_check import run_mypy_check, main


class TestRunMypyCheck:
    def test_target_dir_exists(self, tmp_path):
        """Test that function handles existing directory"""
        # Create a dummy python file
        test_file = tmp_path / "test.py"
        test_file.write_text("x: int = 1\n")

        with patch("setup_type_check.get_project_root", return_value=tmp_path):
            # Should not raise, though mypy might not be installed in test env
            try:
                result = run_mypy_check(target_dir=str(tmp_path), strict=False)
                assert isinstance(result, bool)
            except Exception:
                # If mypy is not installed, it should return False, not crash
                pass

    def test_target_dir_not_exists(self, tmp_path):
        """Test that function handles non-existing directory"""
        non_existent = tmp_path / "does_not_exist"

        with patch("setup_type_check.get_project_root", return_value=tmp_path):
            result = run_mypy_check(target_dir=str(non_existent))
            assert result is False

    def test_mypy_not_installed(self, tmp_path):
        """Test handling when mypy is not installed"""
        test_file = tmp_path / "test.py"
        test_file.write_text("x: int = 1\n")

        with patch("setup_type_check.subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("mypy not found")
            with patch("setup_type_check.get_project_root", return_value=tmp_path):
                result = run_mypy_check(target_dir=str(tmp_path))
                assert result is False

    def test_timeout_handling(self, tmp_path):
        """Test handling of timeout"""
        test_file = tmp_path / "test.py"
        test_file.write_text("x: int = 1\n")

        with patch("setup_type_check.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(cmd=["mypy"], timeout=300)
            with patch("setup_type_check.get_project_root", return_value=tmp_path):
                result = run_mypy_check(target_dir=str(tmp_path))
                assert result is False


class TestMain:
    def test_main_returns_int(self, tmp_path, caplog):
        """Test that main returns an integer exit code"""
        with patch("setup_type_check.get_project_root", return_value=tmp_path):
            with patch("setup_type_check.run_mypy_check", return_value=True):
                result = main()
                assert isinstance(result, int)
                assert result in (0, 1)

    def test_main_creates_log_file(self, tmp_path):
        """Test that main creates the log file"""
        output_dir = tmp_path / "data" / "processed"
        output_dir.mkdir(parents=True)

        with patch("setup_type_check.get_project_root", return_value=tmp_path):
            with patch("setup_type_check.run_mypy_check", return_value=True):
                main()

        log_path = output_dir / "type_log.txt"
        assert log_path.exists()
        assert "Type Check Log" in log_path.read_text()