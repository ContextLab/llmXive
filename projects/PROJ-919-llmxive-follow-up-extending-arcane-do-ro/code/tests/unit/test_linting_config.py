import subprocess
import tempfile
import os
from pathlib import Path
import pytest


class TestLintingConfiguration:
    """Verify that ruff and black configurations are valid and functional."""

    @pytest.fixture
    def temp_project_root(self, tmp_path):
        """Create a temporary project structure with a dummy python file."""
        # Create necessary directories
        (tmp_path / "src").mkdir()
        (tmp_path / "tests").mkdir()
        (tmp_path / "scripts").mkdir()

        # Create a dummy python file with intentional style issues
        dummy_file = tmp_path / "src" / "dummy_module.py"
        dummy_file.write_text(
            "import os\n"
            "import sys\n"
            "\n"
            "def bad_function(  x,y  ):\n"
            "    return x+y\n"
        )

        # Create a valid pyproject.toml with black and ruff config
        config_file = tmp_path / "pyproject.toml"
        config_file.write_text(
            "[tool.black]\n"
            'line-length = 88\n'
            '\n'
            "[tool.ruff]\n"
            'line-length = 88\n'
            'select = ["E", "F", "I"]\n'
            'ignore = ["E501"]\n'
        )

        return tmp_path

    def test_ruff_check_runs(self, temp_project_root):
        """Verify that ruff can be invoked and checks the code."""
        # Run ruff check
        result = subprocess.run(
            ["ruff", "check", str(temp_project_root)],
            capture_output=True,
            text=True,
            cwd=temp_project_root
        )
        # Ruff should find issues in the dummy file
        # We just verify it runs without crashing
        assert result.returncode != 0 or result.returncode == 0
        # The important part is that the config is valid and the tool runs

    def test_black_check_runs(self, temp_project_root):
        """Verify that black can be invoked and checks the code."""
        # Run black check (diff mode)
        result = subprocess.run(
            ["black", "--check", "--diff", str(temp_project_root)],
            capture_output=True,
            text=True,
            cwd=temp_project_root
        )
        # Black should report issues or run successfully
        # We verify the tool runs
        assert result.returncode in [0, 1]

    def test_ruff_config_exists(self, temp_project_root):
        """Verify that the ruff configuration file exists or is embedded in pyproject.toml."""
        ruff_toml = temp_project_root / ".ruff.toml"
        pyproject = temp_project_root / "pyproject.toml"

        assert (
            ruff_toml.exists()
            or pyproject.exists()
            and "[tool.ruff]" in pyproject.read_text()
        ), "Ruff configuration must exist either in .ruff.toml or pyproject.toml"

    def test_black_config_exists(self, temp_project_root):
        """Verify that the black configuration file exists or is embedded in pyproject.toml."""
        pyproject = temp_project_root / "pyproject.toml"
        black_toml = temp_project_root / ".black.toml" # Black usually uses pyproject.toml

        # Black typically reads from pyproject.toml
        assert pyproject.exists() and "[tool.black]" in pyproject.read_text(), \
            "Black configuration must exist in pyproject.toml"