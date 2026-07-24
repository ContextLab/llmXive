"""
Unit tests for linting configuration and runner utilities.
"""
import pytest
from pathlib import Path
from code.linting_config import get_black_config, get_flake8_config
from code.utils.linting_runner import run_black_check, run_flake8_check

def test_black_config_values():
    """Test that black config returns expected default values."""
    config = get_black_config()
    assert config["line_length"] == 120
    assert "py310" in config["target_version"]
    assert "data" in config["exclude"]

def test_flake8_config_values():
    """Test that flake8 config returns expected default values."""
    config = get_flake8_config()
    assert config["max_line_length"] == 120
    assert "E203" in config["ignore"]
    assert "E266" in config["ignore"]
    assert "W503" in config["ignore"]

def test_run_black_check_returns_tuple():
    """Test that run_black_check returns a tuple of (bool, str)."""
    success, msg = run_black_check(Path(__file__).parent)
    assert isinstance(success, bool)
    assert isinstance(msg, str)

def test_run_flake8_check_returns_tuple():
    """Test that run_flake8_check returns a tuple of (bool, str)."""
    success, msg = run_flake8_check(Path(__file__).parent)
    assert isinstance(success, bool)
    assert isinstance(msg, str)