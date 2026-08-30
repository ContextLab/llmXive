import os
import subprocess
import tempfile
import shutil
from pathlib import Path
import pytest

# We need to add the code directory to the path to import the module
# In a real test runner, this would be handled by the environment setup
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_git_hooks import check_git_lfs_installed, run_command, create_pre_push_hook

class TestGitHooks:
    
    def test_run_command_success(self):
        """Test that run_command returns True for a successful command."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cwd = Path(tmpdir)
            result = run_command(["echo", "hello"], cwd=cwd)
            assert result is True

    def test_run_command_failure(self):
        """Test that run_command returns False for a failing command."""
        result = run_command(["false"]) # 'false' always exits with 1
        assert result is False

    def test_pre_push_hook_creation(self):
        """Test that the pre-push hook is created and is executable."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            # Initialize a fake git repo
            subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
            
            hook_created = create_pre_push_hook()
            assert hook_created is True
            
            hook_path = tmp_path / ".git" / "hooks" / "pre-push"
            assert hook_path.exists()
            assert os.access(hook_path, os.X_OK)
            
            # Check content
            with open(hook_path, 'r') as f:
                content = f.read()
            assert "Git LFS" in content
            assert "push rejected" in content

    def test_git_lfs_check_mocks(self, monkeypatch):
        """Test check_git_lfs_installed with mocked subprocess."""
        def mock_run(cmd, *args, **kwargs):
            if "git" in cmd and "lfs" in cmd and "version" in cmd:
                # Mock success
                class MockResult:
                    stdout = "git-lfs/3.0.0"
                return MockResult
            raise FileNotFoundError("Mocked")

        # Test success case
        monkeypatch.setattr("subprocess.run", mock_run)
        assert check_git_lfs_installed() is True

        # Test failure case (FileNotFoundError)
        def mock_fail(*args, **kwargs):
            raise FileNotFoundError("Not found")
        
        monkeypatch.setattr("subprocess.run", mock_fail)
        assert check_git_lfs_installed() is False