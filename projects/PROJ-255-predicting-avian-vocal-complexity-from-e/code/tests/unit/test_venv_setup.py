import pytest
import os
import shutil
import tempfile
from pathlib import Path
from setup_venv import get_python_executable, run_command, setup_venv, activate_and_upgrade_pip, install_requirements

class TestVenvSetup:
    def test_get_python_executable(self):
        """Test that we get a valid python executable path."""
        exe = get_python_executable()
        assert exe is not None
        assert os.path.exists(exe)

    def test_run_command_success(self):
        """Test running a simple command."""
        # Create a temp file to verify command execution
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            if os.name == 'nt':
                cmd = f'cmd /c echo test > {test_file}'
            else:
                cmd = f'echo test > {test_file}'
            
            run_command(cmd, cwd=tmpdir)
            assert test_file.exists()

    def test_setup_venv_creates_directory(self, tmp_path):
        """Test that setup_venv creates the venv directory."""
        venv_path = setup_venv(tmp_path)
        assert venv_path.exists()
        # Check for standard venv files
        if os.name == 'nt':
            assert (venv_path / "Scripts" / "python.exe").exists()
        else:
            assert (venv_path / "bin" / "python").exists()

    def test_install_requirements_missing_file(self, tmp_path):
        """Test that install_requirements raises error for missing file."""
        # Create a dummy pip path
        pip_path = tmp_path / "pip"
        requirements_path = tmp_path / "nonexistent.txt"
        
        with pytest.raises(FileNotFoundError):
            install_requirements(pip_path, requirements_path)

    def test_full_flow_integration(self, tmp_path):
        """Test the full setup flow with a mock requirements file."""
        # Create a minimal requirements file
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("pip>=20.0\n")
        
        # Setup venv
        venv_path = setup_venv(tmp_path)
        
        # Upgrade pip
        pip_path = activate_and_upgrade_pip(venv_path)
        
        # Install requirements (should succeed for pip)
        install_requirements(pip_path, req_file)
        
        # Verify pip was upgraded/installed
        if os.name == 'nt':
            assert (venv_path / "Scripts" / "pip.exe").exists()
        else:
            assert (venv_path / "bin" / "pip").exists()
