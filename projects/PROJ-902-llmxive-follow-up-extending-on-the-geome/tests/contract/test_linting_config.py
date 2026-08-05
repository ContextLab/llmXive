"""
Contract test for linting configuration files.

Validates that .ruff.toml and pyproject.toml contain expected linting
configurations as defined in the project setup (Task T003).
"""

import os
import re
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RUFF_CONFIG = PROJECT_ROOT / ".ruff.toml"
PYPROJECT_CONFIG = PROJECT_ROOT / "pyproject.toml"


class TestRuffConfiguration:
    """Tests for .ruff.toml configuration file."""

    @pytest.fixture
    def ruff_content(self):
        """Read the ruff configuration file."""
        if not RUFF_CONFIG.exists():
            pytest.fail(f"Ruff configuration file not found: {RUFF_CONFIG}")
        return RUFF_CONFIG.read_text()

    def test_ruff_config_exists(self):
        """Verify .ruff.toml exists in project root."""
        assert RUFF_CONFIG.exists(), "Ruff configuration file .ruff.toml must exist"

    def test_ruff_target_version(self, ruff_content):
        """Verify target Python version is set to 3.11."""
        assert "target-version" in ruff_content or 'target-version' in ruff_content, (
            "Ruff config must specify target-version"
        )
        # Check for python 3.11 reference
        assert "3.11" in ruff_content or "py311" in ruff_content, (
            "Ruff config must target Python 3.11"
        )

    def test_ruff_line_length(self, ruff_content):
        """Verify line length is configured (typically 88 for black compatibility)."""
        # Common patterns: line-length = 88 or line-length=88
        assert re.search(r"line-length\s*=\s*\d+", ruff_content), (
            "Ruff config must specify line-length"
        )

    def test_ruff_select_rules(self, ruff_content):
        """Verify that select rules are configured."""
        # Check for 'select' configuration
        assert re.search(r"select\s*=\s*\[", ruff_content) or re.search(
            r"select\s*=", ruff_content
        ), "Ruff config must specify select rules"

    def test_ruff_ignore_rules(self, ruff_content):
        """Verify ignore rules are configured if needed."""
        # This is optional but good practice to check structure
        # We just verify the file is parseable by looking for common sections
        assert re.search(
            r"(select|ignore|line-length|target-version)", ruff_content
        ), "Ruff config must contain at least one valid configuration key"


class TestPyprojectLintingConfig:
    """Tests for pyproject.toml linting configuration."""

    @pytest.fixture
    def pyproject_content(self):
        """Read the pyproject.toml file."""
        if not PYPROJECT_CONFIG.exists():
            pytest.fail(f"Pyproject.toml not found: {PYPROJECT_CONFIG}")
        return PYPROJECT_CONFIG.read_text()

    def test_pyproject_exists(self):
        """Verify pyproject.toml exists in project root."""
        assert PYPROJECT_CONFIG.exists(), "pyproject.toml must exist"

    def test_pyproject_has_ruff_section(self, pyproject_content):
        """Verify pyproject.toml contains ruff configuration section."""
        # Check for [tool.ruff] section
        assert "[tool.ruff]" in pyproject_content or "[tool.ruff." in pyproject_content, (
            "pyproject.toml must contain [tool.ruff] section or subsection"
        )

    def test_pyproject_has_black_section(self, pyproject_content):
        """Verify pyproject.toml contains black configuration section."""
        # Check for [tool.black] section
        assert "[tool.black]" in pyproject_content, (
            "pyproject.toml must contain [tool.black] section"
        )

    def test_pyproject_black_line_length(self, pyproject_content):
        """Verify black line length is configured."""
        assert re.search(
            r"line-length\s*=\s*\d+", pyproject_content
        ), "pyproject.toml must specify black line-length"

    def test_pyproject_black_target_version(self, pyproject_content):
        """Verify black target version is set to 3.11."""
        assert "python-version" in pyproject_content or "target-version" in pyproject_content, (
            "Black config should specify python/target version"
        )
        assert "3.11" in pyproject_content or "py311" in pyproject_content, (
            "Black config must target Python 3.11"
        )


class TestLintingConfigConsistency:
    """Tests for consistency between ruff and black configurations."""

    def test_line_length_consistency(self):
        """Verify line-length is consistent between .ruff.toml and pyproject.toml."""
        if not RUFF_CONFIG.exists() or not PYPROJECT_CONFIG.exists():
            pytest.skip("Configuration files not found")

        ruff_content = RUFF_CONFIG.read_text()
        pyproject_content = PYPROJECT_CONFIG.read_text()

        ruff_match = re.search(r"line-length\s*=\s*(\d+)", ruff_content)
        pyproject_match = re.search(r"line-length\s*=\s*(\d+)", pyproject_content)

        if ruff_match and pyproject_match:
            ruff_len = int(ruff_match.group(1))
            pyproject_len = int(pyproject_match.group(1))
            assert ruff_len == pyproject_len, (
                f"Line length mismatch: ruff={ruff_len}, black={pyproject_len}"
            )
        elif not ruff_match and not pyproject_match:
            pytest.skip("No line-length found in either config")
        else:
            pytest.skip("Line-length found in only one config file")

    def test_python_version_consistency(self):
        """Verify Python version is consistent across configs."""
        if not RUFF_CONFIG.exists() or not PYPROJECT_CONFIG.exists():
            pytest.skip("Configuration files not found")

        ruff_content = RUFF_CONFIG.read_text()
        pyproject_content = PYPROJECT_CONFIG.read_text()

        ruff_versions = re.findall(r"(py311|3\.11)", ruff_content)
        pyproject_versions = re.findall(r"(py311|3\.11)", pyproject_content)

        # Both should reference 3.11
        assert len(ruff_versions) > 0 or "3.11" in ruff_content, (
            "Ruff config should reference Python 3.11"
        )
        assert len(pyproject_versions) > 0 or "3.11" in pyproject_content, (
            "Pyproject config should reference Python 3.11"
        )