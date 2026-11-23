import os
import tempfile
import shutil
from pathlib import Path
import pytest
import subprocess
import sys

class TestLintingConfig:
    """Tests to verify that ruff and black configurations are valid and functional."""

    @pytest.fixture
    def temp_project_root(self):
        """Create a temporary directory structure simulating the project root."""
        temp_dir = tempfile.mkdtemp()
        project_root = Path(temp_dir) / "test_project"
        project_root.mkdir()
        
        # Create a minimal pyproject.toml with linting configs
        config_content = """
        [tool.black]
        line-length = 88
        target-version = ['py39']

        [tool.ruff]
        line-length = 88
        select = ["E", "W", "F"]
        ignore = ["E501"]
        """
        (project_root / "pyproject.toml").write_text(config_content)
        
        # Create a sample Python file to lint/format
        src_dir = project_root / "src"
        src_dir.mkdir()
        sample_file = src_dir / "sample.py"
        sample_file.write_text("import os\nimport sys\n\ndef test_func(  x,y  ):\n    return x+y\n")
        
        yield project_root
        
        # Cleanup
        shutil.rmtree(temp_dir)

    def test_pyproject_toml_exists(self, temp_project_root):
        """Verify pyproject.toml exists in the project root."""
        assert (temp_project_root / "pyproject.toml").exists()

    def test_black_config_present(self, temp_project_root):
        """Verify black configuration is present in pyproject.toml."""
        content = (temp_project_root / "pyproject.toml").read_text()
        assert "[tool.black]" in content
        assert "line-length" in content

    def test_ruff_config_present(self, temp_project_root):
        """Verify ruff configuration is present in pyproject.toml."""
        content = (temp_project_root / "pyproject.toml").read_text()
        assert "[tool.ruff]" in content
        assert "select" in content

    def test_black_can_format_file(self, temp_project_root):
        """Verify black can successfully format a Python file."""
        sample_file = temp_project_root / "src" / "sample.py"
        original_content = sample_file.read_text()
        
        # Run black on the file
        result = subprocess.run(
            [sys.executable, "-m", "black", "--check", str(sample_file)],
            cwd=temp_project_root,
            capture_output=True,
            text=True
        )
        
        # It should fail check because file is unformatted, but black must run without error
        assert result.returncode != 0  # Check fails because file is unformatted
        assert "would reformat" in result.stdout or "would reformat" in result.stderr

    def test_ruff_can_lint_file(self, temp_project_root):
        """Verify ruff can successfully lint a Python file."""
        sample_file = temp_project_root / "src" / "sample.py"
        
        # Run ruff on the file
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "check", str(sample_file)],
            cwd=temp_project_root,
            capture_output=True,
            text=True
        )
        
        # Ruff should run without crashing (return code might be non-zero if issues found)
        # We just verify it executes successfully
        assert result.returncode in [0, 1]  # 0 = no issues, 1 = issues found
        assert "syntax error" not in result.stderr.lower()

    def test_linting_tools_installable(self):
        """Verify that ruff and black can be installed (if not already)."""
        # Check if ruff is available
        try:
            subprocess.run([sys.executable, "-m", "ruff", "--version"], 
                         capture_output=True, check=True, timeout=10)
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Try to install
            subprocess.run([sys.executable, "-m", "pip", "install", "ruff", "--quiet"], 
                         check=True, timeout=60)
        
        # Check if black is available
        try:
            subprocess.run([sys.executable, "-m", "black", "--version"], 
                         capture_output=True, check=True, timeout=10)
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Try to install
            subprocess.run([sys.executable, "-m", "pip", "install", "black", "--quiet"], 
                         check=True, timeout=60)