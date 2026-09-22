import subprocess
import tempfile
import os
from pathlib import Path
import pytest

class TestLintingConfiguration:
    """Tests to verify that ruff and black configurations are valid and functional."""

    def test_ruff_config_exists_and_valid(self, tmp_path):
        """Ensure .ruff.toml exists and ruff can parse it without errors."""
        # Create a minimal python file to lint
        test_file = tmp_path / "test_file.py"
        test_file.write_text("x=1+2\n")

        # Copy config to tmp
        ruff_config = Path(__file__).parent.parent.parent / ".ruff.toml"
        assert ruff_config.exists(), ".ruff.toml must exist in project root"

        # Run ruff check on the test file using the project config
        result = subprocess.run(
            ["ruff", "check", "--config", str(ruff_config), str(test_file)],
            capture_output=True,
            text=True,
        )
        # We expect ruff to run without crashing (return code 0 or 1 is fine, 2 is error)
        assert result.returncode != 2, f"Ruff configuration error: {result.stderr}"

    def test_black_config_exists_and_valid(self, tmp_path):
        """Ensure pyproject.toml exists with black config and black can check it."""
        pyproject = Path(__file__).parent.parent.parent / "pyproject.toml"
        assert pyproject.exists(), "pyproject.toml must exist in project root"

        # Create a minimal python file to format
        test_file = tmp_path / "test_file.py"
        test_file.write_text("x=1+2\n")

        # Run black check (check mode)
        result = subprocess.run(
            ["black", "--check", "--config", str(pyproject), str(test_file)],
            capture_output=True,
            text=True,
        )
        # We expect black to run without crashing (return code 0 or 1 is fine, 2 is error)
        # Return code 1 means "would reformat", which is expected for "x=1+2"
        assert result.returncode != 2, f"Black configuration error: {result.stderr}"

    def test_ruff_enforces_style(self, tmp_path):
        """Verify ruff actually catches style errors based on our config."""
        test_file = tmp_path / "bad_style.py"
        # Intentionally bad style: missing whitespace around operator, unused import
        test_file.write_text("import os\nx=1+2\n")

        ruff_config = Path(__file__).parent.parent.parent / ".ruff.toml"

        result = subprocess.run(
            ["ruff", "check", "--config", str(ruff_config), str(test_file)],
            capture_output=True,
            text=True,
        )

        # Should find errors (return code 1)
        assert result.returncode == 1, "Ruff should detect style violations in bad_style.py"
        assert "E" in result.stdout or "F" in result.stdout or "W" in result.stdout, \
            "Ruff output should indicate specific error codes"

    def test_black_enforces_style(self, tmp_path):
        """Verify black actually catches format errors."""
        test_file = tmp_path / "bad_format.py"
        # Intentionally bad format: no spaces around operator
        test_file.write_text("x=1+2\n")

        pyproject = Path(__file__).parent.parent.parent / "pyproject.toml"

        result = subprocess.run(
            ["black", "--check", "--config", str(pyproject), str(test_file)],
            capture_output=True,
            text=True,
        )

        # Should find errors (return code 1)
        assert result.returncode == 1, "Black should detect format violations in bad_format.py"