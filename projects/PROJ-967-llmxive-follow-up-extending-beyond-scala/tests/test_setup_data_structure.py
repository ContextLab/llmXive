"""
Tests for the setup_data_structure module.

These tests verify that the data directory structure is created correctly
and that the .gitignore file is properly configured.
"""
import os
import tempfile
from pathlib import Path
import pytest
from code.setup_data_structure import setup_data_directories, create_gitignore

@pytest.fixture
def temp_project_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_setup_data_directories_creates_folders(temp_project_dir):
    """Test that setup_data_directories creates the required folders."""
    setup_data_directories(temp_project_dir)
    
    data_dir = temp_project_dir / "data"
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"
    
    assert data_dir.exists()
    assert data_dir.is_dir()
    assert raw_dir.exists()
    assert raw_dir.is_dir()
    assert processed_dir.exists()
    assert processed_dir.is_dir()

def test_setup_data_directories_idempotent(temp_project_dir):
    """Test that running setup_data_directories multiple times doesn't cause errors."""
    setup_data_directories(temp_project_dir)
    setup_data_directories(temp_project_dir)
    
    data_dir = temp_project_dir / "data"
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"
    
    assert data_dir.exists()
    assert raw_dir.exists()
    assert processed_dir.exists()

def test_create_gitignore_creates_file(temp_project_dir):
    """Test that create_gitignore creates a .gitignore file."""
    create_gitignore(temp_project_dir)
    
    gitignore_path = temp_project_dir / ".gitignore"
    assert gitignore_path.exists()
    assert gitignore_path.is_file()

def test_create_gitignore_contains_data_patterns(temp_project_dir):
    """Test that .gitignore contains patterns for data directories."""
    create_gitignore(temp_project_dir)
    
    gitignore_path = temp_project_dir / ".gitignore"
    
    with open(gitignore_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    assert "data/raw/" in content
    assert "data/processed/" in content

def test_create_gitignore_idempotent(temp_project_dir):
    """Test that running create_gitignore multiple times doesn't duplicate content."""
    create_gitignore(temp_project_dir)
    
    gitignore_path = temp_project_dir / ".gitignore"
    
    with open(gitignore_path, 'r', encoding='utf-8') as f:
        first_content = f.read()
    
    create_gitignore(temp_project_dir)
    
    with open(gitignore_path, 'r', encoding='utf-8') as f:
        second_content = f.read()
    
    assert first_content == second_content

def test_create_gitignore_preserves_existing(temp_project_dir):
    """Test that create_gitignore preserves existing content."""
    # Create a .gitignore with some existing content
    gitignore_path = temp_project_dir / ".gitignore"
    existing_content = "# Existing comment\n*.pyc\n"
    
    with open(gitignore_path, 'w', encoding='utf-8') as f:
        f.write(existing_content)
    
    create_gitignore(temp_project_dir)
    
    with open(gitignore_path, 'r', encoding='utf-8') as f:
        new_content = f.read()
    
    assert "# Existing comment" in new_content
    assert "*.pyc" in new_content