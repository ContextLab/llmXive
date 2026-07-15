"""
Tests to verify that linting and formatting configurations exist and are valid.
"""
import os
import tomli
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUFF_CONFIG = os.path.join(PROJECT_ROOT, "code", ".ruff.toml")
BLACK_CONFIG = os.path.join(PROJECT_ROOT, "code", ".black.toml")

@pytest.fixture
def ruff_config():
    with open(RUFF_CONFIG, "rb") as f:
        return tomli.load(f)

@pytest.fixture
def black_config():
    with open(BLACK_CONFIG, "rb") as f:
        return tomli.load(f)

def test_ruff_config_exists(ruff_config):
    """Verify Ruff configuration file exists and is valid TOML."""
    assert ruff_config is not None
    assert "lint" in ruff_config

def test_black_config_exists(black_config):
    """Verify Black configuration file exists and is valid TOML."""
    assert black_config is not None
    assert "tool" in black_config
    assert "black" in black_config["tool"]

def test_black_line_length(black_config):
    """Verify Black line length is set to 88."""
    assert black_config["tool"]["black"]["line-length"] == 88

def test_ruff_select_rules(ruff_config):
    """Verify Ruff selects standard linting rules."""
    select_rules = ruff_config["lint"]["select"]
    assert "E" in select_rules  # pycodestyle errors
    assert "F" in select_rules  # Pyflakes
    assert "I" in select_rules  # isort