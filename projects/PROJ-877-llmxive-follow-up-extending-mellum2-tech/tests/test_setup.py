"""
Tests for project setup and directory creation.
"""
import pytest
from pathlib import Path
import sys
import os

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from config import get_config, get_project_root, ensure_dirs
from setup_directories import ensure_data_directories, generate_init_files
from setup_logging import setup_logger, log_directory_creation

def test_get_project_root():
    """Test that project root is correctly identified."""
    root = get_project_root()
    assert isinstance(root, Path)
    assert root.exists()

def test_get_config():
    """Test that configuration dictionary is populated correctly."""
    config = get_config()
    assert "project_root" in config
    assert "code_dir" in config
    assert "data_dir" in config
    assert isinstance(config["project_root"], Path)

def test_ensure_dirs():
    """Test that ensure_dirs creates required directories."""
    config = get_config()
    ensure_dirs(config)
    
    # Check that key directories exist
    assert config["code_dir"].exists()
    assert config["data_dir"].exists()
    assert config["tests_dir"].exists()
    assert config["results_dir"].exists()

def test_setup_logger():
    """Test that logger is created correctly."""
    logger = setup_logger("test_logger")
    assert logger is not None
    assert logger.name == "test_logger"
    assert logger.level == 20  # INFO level

def test_ensure_data_directories():
    """Test that data directories are created."""
    config = get_config()
    project_root = config["project_root"]
    
    created_dirs = ensure_data_directories(project_root)
    
    assert len(created_dirs) > 0
    for dir_path in created_dirs:
        assert dir_path.exists()
        assert dir_path.is_dir()

def test_generate_init_files():
    """Test that __init__.py files are generated."""
    config = get_config()
    project_root = config["project_root"]
    created_dirs = ensure_data_directories(project_root)
    
    init_files = generate_init_files(project_root, created_dirs)
    
    assert len(init_files) == len(created_dirs)
    for init_file in init_files:
        assert init_file.exists()
        assert init_file.name == "__init__.py"