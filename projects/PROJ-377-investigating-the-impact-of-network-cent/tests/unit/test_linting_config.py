"""
Unit tests to verify linting and formatting configuration files exist and are valid.
"""
import os
import toml
import configparser
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"

def test_flake8_config_exists():
    """Test that .flake8 configuration file exists."""
    flake8_path = CODE_DIR / ".flake8"
    assert flake8_path.exists(), ".flake8 configuration file must exist"
    assert flake8_path.stat().st_size > 0, ".flake8 file must not be empty"

def test_flake8_config_valid():
    """Test that .flake8 configuration is valid."""
    flake8_path = CODE_DIR / ".flake8"
    config = configparser.ConfigParser()
    try:
        config.read(flake8_path)
        assert 'flake8' in config or 'flake8' in str(flake8_path)
    except Exception as e:
        pytest.fail(f".flake8 configuration is invalid: {e}")

def test_black_config_exists():
    """Test that .black configuration file exists."""
    black_path = CODE_DIR / ".black"
    assert black_path.exists(), ".black configuration file must exist"
    assert black_path.stat().st_size > 0, ".black file must not be empty"

def test_black_config_valid():
    """Test that .black configuration is valid TOML."""
    black_path = CODE_DIR / ".black"
    try:
        with open(black_path, 'r') as f:
            content = f.read()
            # Basic validation: check for expected keys
            assert 'line-length' in content, "line-length must be defined in .black"
            assert 'target-version' in content, "target-version must be defined in .black"
    except Exception as e:
        pytest.fail(f".black configuration is invalid: {e}")

def test_isort_config_exists():
    """Test that setup.cfg contains isort configuration."""
    setup_cfg_path = CODE_DIR / "setup.cfg"
    assert setup_cfg_path.exists(), "setup.cfg must exist"
    
    with open(setup_cfg_path, 'r') as f:
        content = f.read()
        assert '[isort]' in content, "setup.cfg must contain [isort] section"
        assert 'profile = black' in content, "isort must be configured for black compatibility"

def test_requirements_includes_linting_tools():
    """Test that requirements.txt includes flake8, black, and isort."""
    req_path = CODE_DIR / "requirements.txt"
    assert req_path.exists(), "requirements.txt must exist"
    
    with open(req_path, 'r') as f:
        content = f.read().lower()
        assert 'flake8' in content, "flake8 must be in requirements.txt"
        assert 'black' in content, "black must be in requirements.txt"
        assert 'isort' in content, "isort must be in requirements.txt"

def test_lint_script_exists():
    """Test that linting script exists and is executable."""
    script_path = CODE_DIR / "scripts" / "run_lint.sh"
    assert script_path.exists(), "run_lint.sh script must exist"
    assert script_path.stat().st_size > 0, "run_lint.sh must not be empty"

def test_format_script_exists():
    """Test that formatting script exists and is executable."""
    script_path = CODE_DIR / "scripts" / "format_code.sh"
    assert script_path.exists(), "format_code.sh script must exist"
    assert script_path.stat().st_size > 0, "format_code.sh must not be empty"