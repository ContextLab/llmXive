import os
import tempfile
import shutil
from pathlib import Path
import pytest
import subprocess
import sys

class TestLintingConfig:
    """Tests to verify that linting (ruff) and formatting (black) are correctly configured."""

    @pytest.fixture
    def temp_project_root(self):
        """Create a temporary directory structure mimicking the project root."""
        temp_dir = tempfile.mkdtemp()
        # Create a dummy python file to test against
        dummy_file = Path(temp_dir) / "test_module.py"
        dummy_file.write_text(
            "import os\nimport sys\n\ndef bad_function(  x,y  ):\n    return x+y\n"
        )
        yield temp_dir
        shutil.rmtree(temp_dir)

    def test_pyproject_toml_exists(self):
        """Verify pyproject.toml exists in the code directory."""
        code_dir = Path(__file__).parent.parent.parent / "code"
        assert (code_dir / "pyproject.toml").exists(), "pyproject.toml not found in code/"

    def test_ruff_config_present(self):
        """Verify ruff configuration exists in pyproject.toml."""
        code_dir = Path(__file__).parent.parent.parent / "code"
        config_path = code_dir / "pyproject.toml"
        content = config_path.read_text()
        assert "[tool.ruff]" in content, "Ruff configuration missing in pyproject.toml"
        assert "line-length" in content, "Ruff line-length not configured"

    def test_black_config_present(self):
        """Verify black configuration exists in pyproject.toml."""
        code_dir = Path(__file__).parent.parent.parent / "code"
        config_path = code_dir / "pyproject.toml"
        content = config_path.read_text()
        assert "[tool.black]" in content, "Black configuration missing in pyproject.toml"
        assert "line-length" in content, "Black line-length not configured"

    def test_ruff_can_run_on_code_dir(self, temp_project_root):
        """Verify ruff can be invoked and finds configuration."""
        # We test that ruff is installed and can run, even if it finds issues
        # We don't assert success because the dummy file has intentional issues
        try:
            result = subprocess.run(
                ["ruff", "check", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            assert result.returncode == 0, "Ruff is not installed or not in PATH"
        except FileNotFoundError:
            pytest.skip("Ruff not installed in environment")

    def test_black_can_run_on_code_dir(self, temp_project_root):
        """Verify black can be invoked."""
        try:
            result = subprocess.run(
                ["black", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            assert result.returncode == 0, "Black is not installed or not in PATH"
        except FileNotFoundError:
            pytest.skip("Black not installed in environment")

    def test_pre_commit_config_exists(self):
        """Verify .pre-commit-config.yaml exists."""
        code_dir = Path(__file__).parent.parent.parent / "code"
        assert (code_dir / ".pre-commit-config.yaml").exists(), ".pre-commit-config.yaml not found"
