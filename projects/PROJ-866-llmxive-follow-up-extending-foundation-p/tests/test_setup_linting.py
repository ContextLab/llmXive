"""
Tests for the setup_linting module.
Verifies that configuration files are created correctly.
"""
import os
import pytest
from pathlib import Path
from code.setup_linting import (
    create_linting_config,
    create_formatting_config,
    create_ruffignore,
    create_gitignore_update,
)

@pytest.fixture(autouse=True)
def cleanup_config_files():
    """Clean up config files before and after each test."""
    files_to_clean = [
        "ruff.toml",
        "pyproject.toml",
        ".ruffignore",
        ".gitignore",
    ]
    
    # Clean before
    for file_path in files_to_clean:
        path = Path(file_path)
        if path.exists():
            path.unlink()
    
    yield
    
    # Clean after
    for file_path in files_to_clean:
        path = Path(file_path)
        if path.exists():
            path.unlink()

def test_create_linting_config():
    """Test that ruff.toml is created with correct content."""
    path = create_linting_config()
    
    assert path.exists()
    assert path.name == "ruff.toml"
    
    content = path.read_text()
    assert "[lint]" in content
    assert 'select = [' in content
    assert '"E"' in content
    assert '"F"' in content
    assert "ignore = [" in content
    assert '"E501"' in content

def test_create_formatting_config_new():
    """Test that pyproject.toml is created with Black config when it doesn't exist."""
    path = create_formatting_config()
    
    assert path.exists()
    assert path.name == "pyproject.toml"
    
    content = path.read_text()
    assert "[tool.black]" in content
    assert "line-length = 88" in content
    assert "target-version" in content

def test_create_ruffignore():
    """Test that .ruffignore is created with correct content."""
    path = create_ruffignore()
    
    assert path.exists()
    assert path.name == ".ruffignore"
    
    content = path.read_text()
    assert "__pycache__/" in content
    assert ".venv/" in content
    assert "venv/" in content
    assert ".git/" in content

def test_create_gitignore_update():
    """Test that .gitignore is created/updated with linting entries."""
    path = create_gitignore_update()
    
    assert path.exists()
    assert path.name == ".gitignore"
    
    content = path.read_text()
    assert ".ruff_cache/" in content
    assert "__pycache__/" in content
    assert "*.py[cod]" in content