"""
Unit tests for the linting setup verification.
"""
import os
import sys
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_linting import check_file_exists, check_config_content


def test_check_file_exists_pyproject():
    """Test that pyproject.toml exists."""
    root = Path(__file__).parent.parent.parent
    filepath = root / "code" / "pyproject.toml"
    assert check_file_exists(str(filepath)) is True


def test_check_file_exists_ruff():
    """Test that .ruff.toml exists."""
    root = Path(__file__).parent.parent.parent
    filepath = root / "code" / ".ruff.toml"
    assert check_file_exists(str(filepath)) is True


def test_check_config_content_black():
    """Test that pyproject.toml contains Black settings."""
    root = Path(__file__).parent.parent.parent
    filepath = root / "code" / "pyproject.toml"
    assert check_config_content(str(filepath)) is True


def test_check_config_content_ruff():
    """Test that .ruff.toml contains Ruff settings."""
    root = Path(__file__).parent.parent.parent
    filepath = root / "code" / ".ruff.toml"
    assert check_config_content(str(filepath)) is True