import os
import tempfile
import shutil
from pathlib import Path
import pytest
import subprocess
import sys

class TestLintingConfig:
    """Tests for linting and formatting configuration."""

    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_pyproject_toml_exists(self, temp_project_dir):
        """Test that pyproject.toml exists in the project root."""
        # Copy the expected file to temp dir for testing
        pyproject_path = Path(__file__).parent.parent.parent / "code" / "pyproject.toml"
        assert pyproject_path.exists(), "pyproject.toml should exist"

    def test_ruff_config_present(self, temp_project_dir):
        """Test that ruff configuration is present in pyproject.toml."""
        pyproject_path = Path(__file__).parent.parent.parent / "code" / "pyproject.toml"
        assert pyproject_path.exists()
        
        content = pyproject_path.read_text()
        assert "[tool.ruff]" in content, "Ruff configuration should be present"
        assert "select" in content, "Ruff should have select rules configured"
        assert "ignore" in content, "Ruff should have ignore rules configured"

    def test_black_config_present(self, temp_project_dir):
        """Test that black configuration is present in pyproject.toml."""
        pyproject_path = Path(__file__).parent.parent.parent / "code" / "pyproject.toml"
        assert pyproject_path.exists()
        
        content = pyproject_path.read_text()
        assert "[tool.black]" in content, "Black configuration should be present"
        assert "line-length" in content, "Black should have line-length configured"

    def test_precommit_config_exists(self, temp_project_dir):
        """Test that .pre-commit-config.yaml exists."""
        precommit_path = Path(__file__).parent.parent.parent / "code" / ".pre-commit-config.yaml"
        assert precommit_path.exists(), ".pre-commit-config.yaml should exist"
        
        content = precommit_path.read_text()
        assert "ruff" in content, "Pre-commit should include ruff"
        assert "black" in content, "Pre-commit should include black"

    def test_ruff_isort_config(self, temp_project_dir):
        """Test that isort is configured within ruff."""
        pyproject_path = Path(__file__).parent.parent.parent / "code" / "pyproject.toml"
        content = pyproject_path.read_text()
        assert "[tool.ruff.isort]" in content, "Ruff isort configuration should be present"

    def test_pytest_config_present(self, temp_project_dir):
        """Test that pytest configuration is present."""
        pyproject_path = Path(__file__).parent.parent.parent / "code" / "pyproject.toml"
        content = pyproject_path.read_text()
        assert "[tool.pytest.ini_options]" in content, "Pytest configuration should be present"
        assert "testpaths" in content, "Pytest should have testpaths configured"