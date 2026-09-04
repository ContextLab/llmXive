"""
Test to verify that linting and formatting configurations are correctly set up.
"""
import os
import toml
import pytest
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
PYPROJECT = ROOT_DIR / "pyproject.toml"
RUFF_CONFIG = ROOT_DIR / ".ruff.toml"
PRE_COMMIT_CONFIG = ROOT_DIR / ".pre-commit-config.yaml"
REQUIREMENTS = ROOT_DIR / "code" / "requirements.txt"

def test_pyproject_toml_exists():
    assert PYPROJECT.exists(), "pyproject.toml must exist"

def test_pyproject_has_black_config():
    with open(PYPROJECT) as f:
        data = toml.load(f)
    assert "tool" in data
    assert "black" in data["tool"]
    assert data["tool"]["black"]["line-length"] == 120
    assert "py311" in data["tool"]["black"]["target-version"]

def test_ruff_config_exists():
    assert RUFF_CONFIG.exists(), ".ruff.toml must exist"

def test_ruff_config_has_target_version():
    content = RUFF_CONFIG.read_text()
    assert "py311" in content, "Ruff config must target Python 3.11"
    assert "line-length = 120" in content, "Ruff config must set line length to 120"

def test_pre_commit_config_exists():
    assert PRE_COMMIT_CONFIG.exists(), ".pre-commit-config.yaml must exist"

def test_pre_commit_includes_black():
    content = PRE_COMMIT_CONFIG.read_text()
    assert "black" in content, "Pre-commit config must include Black hook"

def test_pre_commit_includes_ruff():
    content = PRE_COMMIT_CONFIG.read_text()
    assert "ruff" in content, "Pre-commit config must include Ruff hook"

def test_requirements_includes_dev_tools():
    content = REQUIREMENTS.read_text()
    assert "ruff" in content, "requirements.txt must include ruff"
    assert "black" in content, "requirements.txt must include black"
    assert "pre-commit" in content, "requirements.txt must include pre-commit"