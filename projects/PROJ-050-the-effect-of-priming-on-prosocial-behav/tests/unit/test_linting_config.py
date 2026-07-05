"""
Unit tests for linting and formatting configuration.
Verifies that configuration files exist and contain expected settings.
"""
import os
from pathlib import Path

import pytest


class TestLintingConfiguration:
    """Tests for linting and formatting tool configurations."""

    @pytest.fixture
    def project_root(self) -> Path:
        """Get the project root directory."""
        return Path(__file__).parent.parent.parent

    def test_flake8_config_exists(self, project_root: Path):
        """Test that .flake8 configuration file exists."""
        flake8_config = project_root / "code" / ".flake8"
        assert flake8_config.exists(), "flake8 configuration file (.flake8) must exist"

    def test_flake8_config_valid(self, project_root: Path):
        """Test that .flake8 contains required settings."""
        flake8_config = project_root / "code" / ".flake8"
        content = flake8_config.read_text()

        assert "max-line-length" in content, "max-line-length must be configured"
        assert "exclude" in content, "exclude paths must be configured"

    def test_black_config_in_pyproject(self, project_root: Path):
        """Test that black configuration exists in pyproject.toml."""
        pyproject = project_root / "code" / "pyproject.toml"
        assert pyproject.exists(), "pyproject.toml must exist"

        content = pyproject.read_text()
        assert "[tool.black]" in content, "black configuration section must exist"
        assert "line-length" in content, "black line-length must be configured"

    def test_precommit_config_exists(self, project_root: Path):
        """Test that pre-commit configuration file exists."""
        precommit_config = project_root / "code" / ".pre-commit-config.yaml"
        assert precommit_config.exists(), "pre-commit configuration file must exist"

    def test_precommit_hooks_configured(self, project_root: Path):
        """Test that pre-commit config contains required hooks."""
        precommit_config = project_root / "code" / ".pre-commit-config.yaml"
        content = precommit_config.read_text()

        assert "black" in content, "black hook must be configured"
        assert "flake8" in content, "flake8 hook must be configured"
        assert "isort" in content, "isort hook must be configured"

    def test_requirements_dev_exists(self, project_root: Path):
        """Test that development requirements file exists."""
        dev_req = project_root / "code" / "requirements-dev.txt"
        assert dev_req.exists(), "requirements-dev.txt must exist"

        content = dev_req.read_text()
        assert "flake8" in content, "flake8 must be in dev requirements"
        assert "black" in content, "black must be in dev requirements"
        assert "pytest" in content, "pytest must be in dev requirements"

    def test_pytest_config_in_pyproject(self, project_root: Path):
        """Test that pytest configuration exists in pyproject.toml."""
        pyproject = project_root / "code" / "pyproject.toml"
        content = pyproject.read_text()

        assert "[tool.pytest.ini_options]" in content, "pytest configuration must exist"
        assert "testpaths" in content, "testpaths must be configured"