import os
import tempfile
from pathlib import Path
import pytest

from config.linting import get_project_root, get_ruff_config_path, get_black_config_path, write_ruff_config, write_pyproject_black_config

def test_get_project_root():
    """Test that project root is correctly identified."""
    root = get_project_root()
    assert root.exists()
    assert (root / "code").exists()

def test_ruff_config_exists():
    """Test that .ruff.toml exists or can be created."""
    root = get_project_root()
    config_path = root / ".ruff.toml"
    if not config_path.exists():
        write_ruff_config()
    assert config_path.exists()
    content = config_path.read_text()
    assert "[lint]" in content
    assert "select" in content

def test_black_config_exists():
    """Test that pyproject.toml with black config exists or can be created."""
    root = get_project_root()
    config_path = root / "pyproject.toml"
    if not config_path.exists():
        write_pyproject_black_config()
    assert config_path.exists()
    content = config_path.read_text()
    assert "[tool.black]" in content
    assert "line-length" in content

def test_config_paths():
    """Test that config paths are returned correctly."""
    ruff_path = get_ruff_config_path()
    black_path = get_black_config_path()
    assert ruff_path.exists()
    assert black_path.exists()
    assert ruff_path.suffix == ".toml"
    assert black_path.name == "pyproject.toml"
