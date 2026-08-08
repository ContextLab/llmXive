"""
Unit tests for virtual environment setup functionality (Task T002c).

These tests verify that the setup_venv.py script correctly:
1. Creates a virtual environment
2. Upgrades pip
3. Installs requirements
4. Runs pip check
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock, call
import pytest

# Import the module under test
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))
import setup_venv


class TestVenvSetup:
    """Test suite for virtual environment setup functions."""
    
    def test_get_python_executable(self):
        """Test that get_python_executable returns the current Python path."""
        result = setup_venv.get_python_executable()
        assert result == sys.executable
        assert isinstance(result, str)
    
    def test_run_command_success(self):
        """Test run_command with a successful command."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="output",
                stderr=""
            )
            
            result = setup_venv.run_command(["echo", "hello"], check=True)
            
            mock_run.assert_called_once()
            assert result.returncode == 0
    
    def test_run_command_failure(self):
        """Test run_command with a failing command."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(
                returncode=1,
                cmd=["fail"],
                output="error"
            )
            
            with pytest.raises(subprocess.CalledProcessError):
                setup_venv.run_command(["fail"], check=True)
    
    def test_setup_venv_creates_directory(self):
        """Test that setup_venv creates the virtual environment directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            venv_path = Path(tmpdir) / "test_venv"
            
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0)
                
                setup_venv.setup_venv(venv_path)
                
                # Verify venv command was called with correct arguments
                mock_run.assert_called_once()
                cmd_args = mock_run.call_args[0][0]
                assert "venv" in cmd_args
                assert str(venv_path) in cmd_args
    
    def test_activate_and_upgrade_pip(self):
        """Test pip upgrade command construction."""
        with tempfile.TemporaryDirectory() as tmpdir:
            venv_path = Path(tmpdir) / "test_venv"
            venv_path.mkdir()
            
            # Create a fake pip path
            bin_dir = venv_path / "bin"
            bin_dir.mkdir()
            pip_path = bin_dir / "pip"
            pip_path.touch()
            
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0)
                
                setup_venv.activate_and_upgrade_pip(venv_path)
                
                # Verify pip install --upgrade pip was called
                mock_run.assert_called_once()
                cmd_args = mock_run.call_args[0][0]
                assert "pip" in str(cmd_args[0])
                assert "--upgrade" in cmd_args
                assert "pip" in cmd_args
    
    def test_install_requirements(self):
        """Test requirements installation command construction."""
        with tempfile.TemporaryDirectory() as tmpdir:
            venv_path = Path(tmpdir) / "test_venv"
            venv_path.mkdir()
            bin_dir = venv_path / "bin"
            bin_dir.mkdir()
            pip_path = bin_dir / "pip"
            pip_path.touch()
            
            requirements_path = Path(tmpdir) / "requirements.txt"
            requirements_path.touch()
            
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0)
                
                setup_venv.install_requirements(venv_path, requirements_path)
                
                # Verify pip install -r was called
                mock_run.assert_called_once()
                cmd_args = mock_run.call_args[0][0]
                assert "pip" in str(cmd_args[0])
                assert "-r" in cmd_args
                assert str(requirements_path) in cmd_args
    
    def test_run_pip_check_success(self):
        """Test pip check when no conflicts exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            venv_path = Path(tmpdir) / "test_venv"
            venv_path.mkdir()
            bin_dir = venv_path / "bin"
            bin_dir.mkdir()
            pip_path = bin_dir / "pip"
            pip_path.touch()
            
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0)
                
                result = setup_venv.run_pip_check(venv_path)
                
                assert result is True
                mock_run.assert_called_once()
    
    def test_run_pip_check_failure(self):
        """Test pip check when conflicts exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            venv_path = Path(tmpdir) / "test_venv"
            venv_path.mkdir()
            bin_dir = venv_path / "bin"
            bin_dir.mkdir()
            pip_path = bin_dir / "pip"
            pip_path.touch()
            
            with patch("subprocess.run") as mock_run:
                mock_run.side_effect = subprocess.CalledProcessError(
                    returncode=1,
                    cmd=["pip", "check"]
                )
                
                result = setup_venv.run_pip_check(venv_path)
                
                assert result is False
    
    def test_main_with_missing_requirements(self):
        """Test main() exits when requirements.txt is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a fake code directory structure
            code_dir = Path(tmpdir) / "code"
            code_dir.mkdir()
            requirements_path = Path(tmpdir) / "requirements.txt"
            # requirements.txt does NOT exist
            
            with patch.object(setup_venv, "Path") as mock_path:
                mock_path.return_value.parent = Path(tmpdir)
                mock_path.return_value.exists.return_value = False
                
                with pytest.raises(SystemExit) as exc_info:
                    setup_venv.main()
                
                assert exc_info.value.code == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])