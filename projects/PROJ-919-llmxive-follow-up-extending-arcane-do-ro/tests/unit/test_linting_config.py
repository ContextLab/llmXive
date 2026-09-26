import subprocess
import tempfile
import os
from pathlib import Path
import pytest


class TestLintingConfiguration:
    """Tests to verify ruff and black configuration are valid and functional."""

    @pytest.fixture
    def temp_project(self, tmp_path):
        """Create a temporary project structure with a sample Python file."""
        # Create directories
        code_dir = tmp_path / "code"
        code_dir.mkdir()

        # Create a sample Python file with intentional style issues
        sample_file = code_dir / "sample_module.py"
        sample_file.write_text(
            "import os\n"
            "import sys\n"
            "\n"
            "def bad_function(  x,y  ):\n"
            "    # This function has style issues\n"
            "    result=x+y\n"
            "    if result > 10: return True\n"
            "    return False\n"
        )

        # Create pyproject.toml with ruff/black config
        config_file = tmp_path / "pyproject.toml"
        config_file.write_text(
            "[tool.ruff]\n"
            "line-length = 88\n"
            "select = [\"E\", \"W\", \"F\", \"I\"]\n"
            "ignore = [\"E501\"]\n"
            "\n"
            "[tool.black]\n"
            "line-length = 88\n"
        )

        return tmp_path

    def test_ruff_config_valid(self, temp_project):
        """Verify that ruff can parse the configuration without errors."""
        result = subprocess.run(
            ["ruff", "check", "--config", str(temp_project / "pyproject.toml"), "."],
            cwd=temp_project,
            capture_output=True,
            text=True
        )
        # Ruff should run without crashing (exit code 0 or 1 is fine, 2 is config error)
        assert result.returncode != 2, f"Ruff config error: {result.stderr}"

    def test_black_config_valid(self, temp_project):
        """Verify that black can parse the configuration without errors."""
        result = subprocess.run(
            ["black", "--config", str(temp_project / "pyproject.toml"), "--check", "--diff", "."],
            cwd=temp_project,
            capture_output=True,
            text=True
        )
        # Black should run without crashing (exit code 0 or 1 is fine, 2 is config error)
        assert result.returncode != 2, f"Black config error: {result.stderr}"

    def test_ruff_detects_issues(self, temp_project):
        """Verify that ruff actually detects style issues in the sample file."""
        sample_file = temp_project / "code" / "sample_module.py"
        result = subprocess.run(
            ["ruff", "check", str(sample_file)],
            capture_output=True,
            text=True
        )
        # Should find at least one issue (F811, E201, etc.)
        assert result.returncode != 0, "Ruff should detect issues in the sample file"
        assert "F" in result.stdout or "E" in result.stdout or "W" in result.stdout, \
            f"Ruff output should contain style issues: {result.stdout}"

    def test_black_formatting_check(self, temp_project):
        """Verify that black detects formatting issues."""
        sample_file = temp_project / "code" / "sample_module.py"
        result = subprocess.run(
            ["black", "--check", str(sample_file)],
            capture_output=True,
            text=True
        )
        # Should detect formatting issues
        assert result.returncode != 0, "Black should detect formatting issues in the sample file"
        assert "would reformat" in result.stdout or "isort" in result.stdout, \
            f"Black output should indicate reformatting needed: {result.stdout}"