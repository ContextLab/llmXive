import os
import sys
import tempfile
import shutil
import subprocess
import pytest
from unittest.mock import patch, MagicMock

# Add the code directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from setup_linting import (
    check_tool_installed,
    create_ruff_config,
    create_black_config,
    run_flake8_check,
    run_black_check
)

class TestSetupLinting:
    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        # Create necessary subdirectories to avoid errors
        os.makedirs('code', exist_ok=True)
        
        yield
        
        # Cleanup
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)

    def test_check_tool_installed(self):
        """Test that check_tool_installed returns False for non-existent tool."""
        assert check_tool_installed('non_existent_tool_xyz') is False

    def test_create_ruff_config(self):
        """Test that ruff configuration file is created correctly."""
        create_ruff_config()
        config_path = os.path.join('code', 'ruff.toml')
        assert os.path.exists(config_path)
        
        with open(config_path, 'r') as f:
            content = f.read()
        
        assert '[tool.ruff]' in content
        assert 'select' in content
        assert 'line-length' in content
        assert 'target-version' in content

    def test_create_black_config_new_file(self):
        """Test that black configuration is created in a new pyproject.toml."""
        create_black_config()
        config_path = os.path.join('code', 'pyproject.toml')
        assert os.path.exists(config_path)
        
        with open(config_path, 'r') as f:
            content = f.read()
        
        assert '[tool.black]' in content
        assert 'line-length' in content
        assert 'py311' in content

    def test_create_black_config_existing_file(self):
        """Test that black configuration is appended to existing pyproject.toml."""
        # Create a dummy pyproject.toml
        config_path = os.path.join('code', 'pyproject.toml')
        with open(config_path, 'w') as f:
            f.write("[build-system]\nrequires = ['setuptools']\n")
        
        create_black_config()
        
        with open(config_path, 'r') as f:
            content = f.read()
        
        assert '[tool.black]' in content

    def test_run_flake8_check_no_flake8(self):
        """Test flake8 check when flake8 is not installed."""
        with patch('setup_linting.subprocess.run') as mock_run:
            mock_run.side_effect = FileNotFoundError("flake8 not found")
            success, msg = run_flake8_check()
            
            assert success is False
            assert 'not installed' in msg

    def test_run_black_check_no_black(self):
        """Test black check when black is not installed."""
        with patch('setup_linting.subprocess.run') as mock_run:
            mock_run.side_effect = FileNotFoundError("black not found")
            success, msg = run_black_check()
            
            assert success is False
            assert 'not installed' in msg

    def test_run_flake8_check_success(self):
        """Test successful flake8 check."""
        with patch('setup_linting.subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = ""
            mock_run.return_value = mock_result
            
            success, msg = run_flake8_check()
            
            assert success is True
            assert "No linting issues found" in msg

    def test_run_black_check_success(self):
        """Test successful black check."""
        with patch('setup_linting.subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = ""
            mock_run.return_value = mock_result
            
            success, msg = run_black_check()
            
            assert success is True
            assert "formatted correctly" in msg