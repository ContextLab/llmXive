"""
Unit tests to verify that linting and formatting configurations are present and valid.
This satisfies the "Independent Test" acceptance criteria for T003.
"""
import os
import yaml
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PRE_COMMIT_PATH = os.path.join(PROJECT_ROOT, ".pre-commit-config.yaml")
RUFF_PATH = os.path.join(PROJECT_ROOT, "ruff.toml")

def test_pre_commit_config_exists():
    """Verify .pre-commit-config.yaml exists in project root."""
    assert os.path.isfile(PRE_COMMIT_PATH), f"File not found: {PRE_COMMIT_PATH}"

def test_pre_commit_config_valid_yaml():
    """Verify .pre-commit-config.yaml is valid YAML."""
    with open(PRE_COMMIT_PATH, "r") as f:
        try:
            config = yaml.safe_load(f)
            assert isinstance(config, dict), "Pre-commit config must be a dictionary"
            assert "repos" in config, "Pre-commit config must contain 'repos' key"
            assert isinstance(config["repos"], list), "'repos' must be a list"
        except yaml.YAMLError as e:
            pytest.fail(f"Invalid YAML in .pre-commit-config.yaml: {e}")

def test_pre_commit_has_black():
    """Verify Black is configured in pre-commit."""
    with open(PRE_COMMIT_PATH, "r") as f:
        content = f.read()
        assert "psf/black" in content or "black" in content, "Black must be in pre-commit config"

def test_pre_commit_has_ruff():
    """Verify Ruff is configured in pre-commit."""
    with open(PRE_COMMIT_PATH, "r") as f:
        content = f.read()
        assert "astral-sh/ruff" in content or "ruff" in content, "Ruff must be in pre-commit config"

def test_ruff_config_exists():
    """Verify ruff.toml exists in project root."""
    assert os.path.isfile(RUFF_PATH), f"File not found: {RUFF_PATH}"

def test_ruff_config_target_version():
    """Verify ruff.toml targets Python 3.11."""
    with open(RUFF_PATH, "r") as f:
        content = f.read()
        assert "py311" in content, "Ruff config must target Python 3.11"

def test_ruff_config_line_length():
    """Verify ruff.toml sets line length to 88."""
    with open(RUFF_PATH, "r") as f:
        content = f.read()
        assert "line-length = 88" in content, "Ruff line length must be 88"