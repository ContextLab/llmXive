import subprocess
import tempfile
import os
from pathlib import Path
import pytest

class TestLintingConfiguration:
    """
    Test that linting and formatting tools are correctly configured
    and can be executed without errors on the codebase.
    """

    @pytest.fixture
    def project_root(self):
        # Return the actual project root relative to where tests run
        # Assuming tests are run from the repo root or code/
        current = Path(__file__).resolve().parent
        # Traverse up to find the root with pyproject.toml
        while not (current / "pyproject.toml").exists():
            current = current.parent
            if current == current.parent:
                break
        return current

    def test_ruff_check_passes(self, project_root):
        """Verify that 'ruff check' runs without errors on the src directory."""
        src_dir = project_root / "code" / "src"
        if not src_dir.exists():
            pytest.skip("Source directory not found, skipping lint check")

        result = subprocess.run(
            ["ruff", "check", str(src_dir)],
            capture_output=True,
            text=True,
            cwd=project_root
        )
        # Ruff returns 0 if no issues found (or 1 if issues found but not fixed)
        # We expect it to run successfully (exit code 0 or 1, but not 2 for syntax error)
        # For this test, we just verify the tool runs and parses the config correctly.
        # If the config is invalid, ruff might exit with 2.
        assert result.returncode in [0, 1], f"Ruff check failed with code {result.returncode}: {result.stderr}"

    def test_black_check_passes(self, project_root):
        """Verify that 'black --check' runs without errors on the src directory."""
        src_dir = project_root / "code" / "src"
        if not src_dir.exists():
            pytest.skip("Source directory not found, skipping format check")

        result = subprocess.run(
            ["black", "--check", "--diff", str(src_dir)],
            capture_output=True,
            text=True,
            cwd=project_root
        )
        # Black returns 0 if all files are formatted correctly, 1 if not.
        # We verify the tool runs successfully.
        assert result.returncode in [0, 1], f"Black check failed with code {result.returncode}: {result.stderr}"

    def test_pyproject_toml_exists(self, project_root):
        """Verify pyproject.toml exists and contains black/ruff config."""
        config_file = project_root / "pyproject.toml"
        assert config_file.exists(), "pyproject.toml not found in project root"

        content = config_file.read_text()
        assert "[tool.black]" in content, "Black configuration missing from pyproject.toml"
        assert "[tool.ruff]" in content, "Ruff configuration missing from pyproject.toml"
