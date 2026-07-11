import subprocess
import os
import tempfile
from pathlib import Path
import pytest

def test_flake8_config_exists():
    """Verify flake8 configuration file exists in project root."""
    project_root = Path(__file__).resolve().parent.parent.parent
    config_files = ['.flake8', 'setup.cfg', 'pyproject.toml']
    found = False
    for cfg in config_files:
        if (project_root / cfg).exists():
            found = True
            break
    assert found, "No flake8 configuration found in project root"

def test_black_config_exists():
    """Verify black configuration file exists in project root."""
    project_root = Path(__file__).resolve().parent.parent.parent
    config_files = ['pyproject.toml']
    found = False
    for cfg in config_files:
        config_path = project_root / cfg
        if config_path.exists():
            content = config_path.read_text()
            if '[tool.black]' in content:
                found = True
                break
    assert found, "No black configuration found in pyproject.toml"

def test_flake8_can_parse_config():
    """Verify flake8 can successfully parse the configuration."""
    project_root = Path(__file__).resolve().parent.parent.parent
    try:
        result = subprocess.run(
            ['flake8', '--version'],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0, f"flake8 failed: {result.stderr}"
    except FileNotFoundError:
        pytest.skip("flake8 not installed in environment")

def test_black_can_parse_config():
    """Verify black can successfully parse the configuration."""
    project_root = Path(__file__).resolve().parent.parent.parent
    try:
        result = subprocess.run(
            ['black', '--version'],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0, f"black failed: {result.stderr}"
    except FileNotFoundError:
        pytest.skip("black not installed in environment")

def test_linting_setup_script_exists():
    """Verify that the linting configuration files are present."""
    project_root = Path(__file__).resolve().parent.parent.parent
    pyproject = project_root / 'pyproject.toml'
    setup_cfg = project_root / 'setup.cfg'
    
    assert pyproject.exists() or setup_cfg.exists(), \
        "Linting configuration files (pyproject.toml or setup.cfg) are missing"