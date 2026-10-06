import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path
import pytest

# Add the code directory to the path so we can import setup_linting
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "code"))

from setup_linting import (
    check_file_exists,
    validate_pyproject_config,
    install_requirements,
    run_linting,
    run_formatting,
    PROJECT_ROOT
)

class TestLintingSetup:

    def test_check_file_exists(self):
        """Test that check_file_exists correctly identifies existing and missing files."""
        existing_file = Path(__file__)
        missing_file = Path("/tmp/this_file_does_not_exist_12345.txt")
        
        assert check_file_exists(existing_file) is True
        assert check_file_exists(missing_file) is False

    def test_validate_pyproject_config_missing(self, tmp_path):
        """Test validation on a missing pyproject.toml."""
        missing_path = tmp_path / "pyproject.toml"
        assert validate_pyproject_config(missing_path) is False

    def test_install_requirements(self):
        """Test that install_requirements runs without error (idempotent)."""
        # This test assumes flake8 and black might already be installed or can be installed.
        # We just check that the function doesn't raise an exception.
        try:
            install_requirements()
        except Exception as e:
            pytest.fail(f"install_requirements raised an exception: {e}")

    def test_run_linting(self):
        """Test that run_linting executes flake8 without crashing."""
        # We don't assert on the return code because the codebase might have linting errors.
        # We just assert that the function runs.
        try:
            run_linting()
        except Exception as e:
            pytest.fail(f"run_linting raised an exception: {e}")

    def test_run_formatting(self):
        """Test that run_formatting executes black without crashing."""
        try:
            run_formatting()
        except Exception as e:
            pytest.fail(f"run_formatting raised an exception: {e}")

    def test_pyproject_toml_structure(self):
        """Verify that pyproject.toml contains required sections if it exists."""
        pyproject_path = PROJECT_ROOT / "pyproject.toml"
        if pyproject_path.exists():
            import toml
            try:
                config = toml.load(pyproject_path)
                assert 'tool' in config, "pyproject.toml must contain [tool] section"
                assert 'black' in config.get('tool', {}), "pyproject.toml must contain [tool.black] section"
            except Exception as e:
                pytest.fail(f"Failed to parse or validate pyproject.toml: {e}")
