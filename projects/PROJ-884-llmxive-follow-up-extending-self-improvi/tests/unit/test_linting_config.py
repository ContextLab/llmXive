"""
Unit tests for linting configuration utilities.
"""
import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
# We need to ensure the code path is correct relative to the test location
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.linting_config import (
    create_black_config_file,
    create_flake8_config_file,
    run_black_check,
    run_flake8_check,
    setup_linting
)


class TestBlackConfig:
    def test_creates_black_config_if_missing(self, tmp_path):
        """Test that a black config file is created if it doesn't exist."""
        config_path = tmp_path / "pyproject.toml"
        
        result = create_black_config_file(config_path)
        
        assert result.exists()
        content = result.read_text()
        assert "[tool.black]" in content
        assert "line-length = 88" in content
        assert "target-version" in content

    def test_appends_black_config_if_exists(self, tmp_path):
        """Test that black config is appended if file exists but lacks section."""
        config_path = tmp_path / "pyproject.toml"
        config_path.write_text("[tool.mypy]\nstrict = true\n")
        
        result = create_black_config_file(config_path)
        
        content = result.read_text()
        assert "[tool.mypy]" in content
        assert "[tool.black]" in content

    def test_skips_if_black_config_exists(self, tmp_path):
        """Test that config is not overwritten if black section exists."""
        config_path = tmp_path / "pyproject.toml"
        original_content = "[tool.black]\nline-length = 79\n"
        config_path.write_text(original_content)
        
        result = create_black_config_file(config_path)
        
        assert result.read_text() == original_content


class TestFlake8Config:
    def test_creates_flake8_config_if_missing(self, tmp_path):
        """Test that a flake8 config file is created if it doesn't exist."""
        config_path = tmp_path / ".flake8"
        
        result = create_flake8_config_file(config_path)
        
        assert result.exists()
        content = result.read_text()
        assert "[flake8]" in content
        assert "max-line-length = 88" in content

    def test_skips_if_flake8_config_exists(self, tmp_path):
        """Test that config is not overwritten if it exists."""
        config_path = tmp_path / ".flake8"
        original_content = "[flake8]\nmax-line-length = 100\n"
        config_path.write_text(original_content)
        
        result = create_flake8_config_file(config_path)
        
        assert result.read_text() == original_content


class TestRunBlackCheck:
    def test_returns_success_on_clean_code(self, tmp_path):
        """Test that black check returns success on properly formatted code."""
        # Create a temporary file with valid, formatted code
        test_file = tmp_path / "test_code.py"
        test_file.write_text("x = 1\ny = 2\n")
        
        # Mock subprocess to simulate success
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            
            success, msg = run_black_check(tmp_path, check_only=True)
            
            assert success is True
            assert "passed" in msg.lower()

    def test_returns_failure_on_misformatted_code(self, tmp_path):
        """Test that black check returns failure on misformatted code."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1, 
                stdout="would reformat", 
                stderr=""
            )
            
            success, msg = run_black_check(tmp_path, check_only=True)
            
            assert success is False
            assert "failed" in msg.lower()

    def test_handles_timeout(self, tmp_path):
        """Test that timeout is handled gracefully."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(cmd=[], timeout=300)
            
            success, msg = run_black_check(tmp_path, check_only=True)
            
            assert success is False
            assert "timed out" in msg.lower()


class TestRunFlake8Check:
    def test_returns_success_on_clean_code(self, tmp_path):
        """Test that flake8 check returns success on clean code."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            
            success, msg = run_flake8_check(tmp_path)
            
            assert success is True
            assert "passed" in msg.lower()

    def test_returns_failure_on_lint_errors(self, tmp_path):
        """Test that flake8 check returns failure on lint errors."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1, 
                stdout="test.py:1:1: F401", 
                stderr=""
            )
            
            success, msg = run_flake8_check(tmp_path)
            
            assert success is False
            assert "failed" in msg.lower()

    def test_handles_timeout(self, tmp_path):
        """Test that timeout is handled gracefully."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(cmd=[], timeout=300)
            
            success, msg = run_flake8_check(tmp_path)
            
            assert success is False
            assert "timed out" in msg.lower()


class TestSetupLinting:
    def test_creates_both_configs(self, tmp_path):
        """Test that setup_linting creates both black and flake8 configs."""
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            black_cfg, flake8_cfg = setup_linting(tmp_path)
            
            assert black_cfg.exists()
            assert flake8_cfg.exists()
            assert "[tool.black]" in black_cfg.read_text()
            assert "[flake8]" in flake8_cfg.read_text()
        finally:
            os.chdir(original_cwd)