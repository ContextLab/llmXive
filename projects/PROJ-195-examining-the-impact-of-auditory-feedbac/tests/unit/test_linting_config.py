"""
Unit tests to verify linting and formatting configuration files exist and are valid.
"""
import os
import toml
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent

def test_flake8_config_exists():
    """Verify .flake8 configuration file exists."""
    config_path = PROJECT_ROOT / "code" / ".flake8"
    assert config_path.exists(), "Missing .flake8 configuration file"

def test_black_config_exists():
    """Verify black configuration exists (either pyproject.toml or setup.cfg)."""
    pyproject_path = PROJECT_ROOT / "code" / "pyproject.toml"
    setup_cfg_path = PROJECT_ROOT / "code" / "setup.cfg"
    
    assert pyproject_path.exists() or setup_cfg_path.exists(), \
        "Missing black configuration (pyproject.toml or setup.cfg)"

def test_pyproject_toml_valid():
    """Verify pyproject.toml is valid TOML and contains required sections."""
    pyproject_path = PROJECT_ROOT / "code" / "pyproject.toml"
    if not pyproject_path.exists():
        pytest.skip("pyproject.toml not present")
    
    try:
        with open(pyproject_path, 'r') as f:
            data = toml.load(f)
        
        assert 'project' in data, "Missing [project] section in pyproject.toml"
        assert 'dependencies' in data['project'], "Missing dependencies in pyproject.toml"
    except Exception as e:
        pytest.fail(f"Invalid pyproject.toml: {e}")

def test_editorconfig_exists():
    """Verify .editorconfig exists for consistent formatting."""
    config_path = PROJECT_ROOT / "code" / ".editorconfig"
    assert config_path.exists(), "Missing .editorconfig file"

def test_black_line_length_consistent():
    """Verify black line length matches flake8 max-line-length."""
    flake8_path = PROJECT_ROOT / "code" / ".flake8"
    pyproject_path = PROJECT_ROOT / "code" / "pyproject.toml"
    setup_cfg_path = PROJECT_ROOT / "code" / "setup.cfg"

    flake8_line_length = None
    black_line_length = None

    if flake8_path.exists():
        with open(flake8_path, 'r') as f:
            for line in f:
                if line.strip().startswith('max-line-length'):
                    flake8_line_length = int(line.split('=')[1].strip())

    if pyproject_path.exists():
        try:
            with open(pyproject_path, 'r') as f:
                data = toml.load(f)
                if 'tool' in data and 'black' in data['tool']:
                    black_line_length = data['tool']['black'].get('line-length')
        except:
            pass
    elif setup_cfg_path.exists():
        import configparser
        config = configparser.ConfigParser()
        config.read(setup_cfg_path)
        if 'black' in config:
            black_line_length = config['black'].get('line-length')

    if flake8_line_length and black_line_length:
        assert flake8_line_length == black_line_length, \
            f"Line length mismatch: flake8={flake8_line_length}, black={black_line_length}"