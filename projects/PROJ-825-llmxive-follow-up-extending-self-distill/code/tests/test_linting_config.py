import subprocess
import sys
import os
import tempfile
import shutil
import pytest
from pathlib import Path

def run_command(cmd, cwd=None):
    """Helper to run a shell command and return stdout, stderr, and return code."""
    result = subprocess.run(
        cmd,
        shell=True,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False
    )
    return result.stdout, result.stderr, result.returncode

class TestLintingConfig:
    """Tests to verify that Ruff and Black are configured and functional."""

    @pytest.fixture
    def project_root(self):
        """Return the project root directory."""
        return Path(__file__).parent.parent.parent

    def test_ruff_config_exists(self, project_root):
        """Verify that a ruff configuration file exists."""
        # Check for .ruff.toml or pyproject.toml with [tool.ruff]
        ruff_toml = project_root / "code" / ".ruff.toml"
        pyproject = project_root / "code" / "pyproject.toml"
        
        assert ruff_toml.exists() or (pyproject.exists() and "[tool.ruff]" in pyproject.read_text()), \
            "Ruff configuration file (.ruff.toml) or section in pyproject.toml not found."

    def test_black_config_exists(self, project_root):
        """Verify that a Black configuration file exists."""
        # Check for pyproject.toml with [tool.black]
        pyproject = project_root / "code" / "pyproject.toml"
        
        assert pyproject.exists() and "[tool.black]" in pyproject.read_text(), \
            "Black configuration section [tool.black] not found in pyproject.toml."

    def test_ruff_check_code(self, project_root):
        """Verify that ruff can run on the codebase without crashing."""
        # Install ruff if not present
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "ruff"], check=True)
        
        code_dir = project_root / "code"
        stdout, stderr, returncode = run_command("ruff check .", cwd=code_dir)
        
        # We expect returncode 0 (clean) or 1 (found issues). 
        # We fail if it crashes (e.g., 2) or config is invalid.
        assert returncode in [0, 1], f"Ruff check failed with code {returncode}: {stderr}"

    def test_black_check_code(self, project_root):
        """Verify that black can run on the codebase without crashing."""
        # Install black if not present
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "black"], check=True)
        
        code_dir = project_root / "code"
        stdout, stderr, returncode = run_command("black --check .", cwd=code_dir)
        
        # We expect returncode 0 (clean) or 1 (needs formatting).
        # We fail if it crashes (e.g., 2).
        assert returncode in [0, 1], f"Black check failed with code {returncode}: {stderr}"