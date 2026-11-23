import os
from pathlib import Path
import pytest

from code.setup_data_dirs import create_directories, create_init_files
from code.config import DATA_DIR, ERRORS_DIR, MODELS_DIR, REPORTS_DIR, LOG_DIR


def test_create_directories(tmp_path, monkeypatch):
    """Test that create_directories creates all required directories."""
    # Monkeypatch the config paths to use tmp_path
    monkeypatch.setattr("code.config.DATA_DIR", tmp_path / "data")
    monkeypatch.setattr("code.config.ERRORS_DIR", tmp_path / "errors")
    monkeypatch.setattr("code.config.MODELS_DIR", tmp_path / "models")
    monkeypatch.setattr("code.config.REPORTS_DIR", tmp_path / "reports")
    monkeypatch.setattr("code.config.LOG_DIR", tmp_path / "logs")
    
    # Re-import to pick up new paths
    import importlib
    import code.setup_data_dirs
    importlib.reload(code.setup_data_dirs)
    
    # Create directories
    code.setup_data_dirs.create_directories()
    
    # Verify all directories exist
    assert (tmp_path / "data" / "raw").exists()
    assert (tmp_path / "data" / "curated").exists()
    assert (tmp_path / "data" / "artifacts").exists()
    assert (tmp_path / "data" / "logs").exists()
    assert (tmp_path / "errors").exists()
    assert (tmp_path / "models").exists()
    assert (tmp_path / "reports").exists()
    assert (tmp_path / "logs").exists()


def test_create_init_files(tmp_path, monkeypatch):
    """Test that create_init_files creates __init__.py files."""
    # Create a test directory structure
    test_dir = tmp_path / "code"
    test_dir.mkdir()
    (test_dir / "data").mkdir()
    (test_dir / "utils").mkdir()
    
    # Monkeypatch PROJECT_ROOT
    monkeypatch.setattr("code.setup_data_dirs.PROJECT_ROOT", tmp_path)
    
    # Re-import to pick up new paths
    import importlib
    import code.setup_data_dirs
    importlib.reload(code.setup_data_dirs)
    
    # Create init files
    code.setup_data_dirs.create_init_files()
    
    # Verify __init__.py files exist
    assert (test_dir / "__init__.py").exists()
    assert (test_dir / "data" / "__init__.py").exists()
    assert (test_dir / "utils" / "__init__.py").exists()
