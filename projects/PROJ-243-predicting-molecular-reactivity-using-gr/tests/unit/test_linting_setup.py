"""
Unit tests for linting setup configuration.
"""
import os
import pytest


def test_ruff_config_exists():
    """Test that ruff.toml configuration file exists."""
    assert os.path.exists("ruff.toml"), "ruff.toml configuration file should exist"


def test_black_config_exists():
    """Test that pyproject.toml contains Black configuration."""
    assert os.path.exists("pyproject.toml"), "pyproject.toml should exist"
    with open("pyproject.toml", "r") as f:
        content = f.read()
    assert "[tool.black]" in content, "pyproject.toml should contain [tool.black] section"


def test_black_config_line_length():
    """Test that Black line length is set to 88."""
    with open("pyproject.toml", "r") as f:
        content = f.read()
    assert "line-length = 88" in content, "Black line-length should be 88"


def test_black_config_target_version():
    """Test that Black target version is Python 3.11."""
    with open("pyproject.toml", "r") as f:
        content = f.read()
    assert "py311" in content, "Black target-version should include py311"


def test_ruff_config_select_rules():
    """Test that ruff.toml selects common linting rules."""
    with open("ruff.toml", "r") as f:
        content = f.read()
    assert '"E"' in content, "ruff.toml should select E rules"
    assert '"F"' in content, "ruff.toml should select F rules"
    assert '"I"' in content, "ruff.toml should select I rules"


def test_ruff_config_ignore_line_length():
    """Test that ruff.toml ignores E501 (line too long)."""
    with open("ruff.toml", "r") as f:
        content = f.read()
    assert '"E501"' in content, "ruff.toml should ignore E501"