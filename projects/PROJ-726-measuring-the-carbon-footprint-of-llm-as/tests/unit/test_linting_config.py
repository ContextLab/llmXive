import os
import tempfile
from pathlib import Path

def test_black_config_exists():
    """Test that pyproject.toml contains Black configuration."""
    pyproject_path = Path("pyproject.toml")
    assert pyproject_path.exists(), "pyproject.toml should exist"
    
    content = pyproject_path.read_text(encoding="utf-8")
    assert "[tool.black]" in content, "pyproject.toml should contain [tool.black] section"
    assert "line-length" in content, "Black config should specify line-length"
    assert "target-version" in content, "Black config should specify target-version"

def test_ruff_config_exists():
    """Test that pyproject.toml contains Ruff configuration."""
    pyproject_path = Path("pyproject.toml")
    assert pyproject_path.exists(), "pyproject.toml should exist"
    
    content = pyproject_path.read_text(encoding="utf-8")
    assert "[tool.ruff]" in content, "pyproject.toml should contain [tool.ruff] section"
    assert "select" in content, "Ruff config should specify rules to select"
    assert "ignore" in content, "Ruff config should specify rules to ignore"

def test_config_files_are_valid_toml():
    """Test that pyproject.toml is valid TOML."""
    try:
        import tomllib
    except ImportError:
        try:
            import tomli as tomllib
        except ImportError:
            import pytest
            pytest.skip("tomllib or tomli not available for testing")
    
    pyproject_path = Path("pyproject.toml")
    with open(pyproject_path, "rb") as f:
        # Should not raise an exception
        tomllib.load(f)