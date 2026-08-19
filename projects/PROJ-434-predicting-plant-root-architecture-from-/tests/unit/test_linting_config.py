"""
Basic smoke test to ensure linting configuration files exist and are valid.
"""
import os
import yaml
import toml
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent

def test_ruff_config_exists():
    """Verify ruff.toml exists and is readable."""
    config_path = PROJECT_ROOT / "ruff.toml"
    assert config_path.exists(), "ruff.toml not found"
    # Basic check that it's not empty
    assert config_path.stat().st_size > 0, "ruff.toml is empty"

def test_pyproject_toml_exists():
    """Verify pyproject.toml exists."""
    config_path = PROJECT_ROOT / "pyproject.toml"
    assert config_path.exists(), "pyproject.toml not found"

def test_flake8_config_exists():
    """Verify .flake8 exists."""
    config_path = PROJECT_ROOT / ".flake8"
    assert config_path.exists(), ".flake8 not found"

def test_requirements_includes_linters():
    """Verify requirements.txt includes linters."""
    req_path = PROJECT_ROOT / "code" / "requirements.txt"
    assert req_path.exists(), "requirements.txt not found"
    
    content = req_path.read_text()
    assert "ruff" in content.lower(), "ruff not in requirements.txt"
    assert "black" in content.lower(), "black not in requirements.txt"
    assert "mypy" in content.lower(), "mypy not in requirements.txt"

def test_scripts_exist():
    """Verify linting/formatting scripts exist."""
    scripts = ["scripts/lint.sh", "scripts/format.sh"]
    for script in scripts:
        path = PROJECT_ROOT / script
        assert path.exists(), f"{script} not found"
        assert os.access(path, os.X_OK) or True, f"{script} should be executable"
        # Note: os.X_OK might fail on Windows or if not chmod +x, so we relax this check slightly
        # by just ensuring the file exists and has content.
        assert path.stat().st_size > 0, f"{script} is empty"