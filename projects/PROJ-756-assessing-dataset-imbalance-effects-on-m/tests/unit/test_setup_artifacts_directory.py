import os
import tempfile
from pathlib import Path
import pytest
from setup_artifacts_directory import create_artifacts_directory

def test_create_artifacts_directory_new():
    """Test that create_artifacts_directory creates the directory if it doesn't exist."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        base_path = Path(tmp_dir)
        artifacts_path = base_path / "artifacts"
        
        assert not artifacts_path.exists()
        
        create_artifacts_directory(base_path)
        
        assert artifacts_path.exists()
        assert artifacts_path.is_dir()

def test_create_artifacts_directory_exists():
    """Test that create_artifacts_directory does nothing if directory already exists."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        base_path = Path(tmp_dir)
        artifacts_path = base_path / "artifacts"
        artifacts_path.mkdir(parents=True, exist_ok=True)
        
        assert artifacts_path.exists()
        
        # Should not raise an error
        create_artifacts_directory(base_path)
        
        assert artifacts_path.exists()
        assert artifacts_path.is_dir()

def test_create_artifacts_directory_nested():
    """Test that create_artifacts_directory creates parent directories if needed."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        base_path = Path(tmp_dir)
        # Ensure base_path exists
        base_path.mkdir(parents=True, exist_ok=True)
        
        # The function should create 'artifacts' inside base_path
        create_artifacts_directory(base_path)
        
        artifacts_path = base_path / "artifacts"
        assert artifacts_path.exists()
        assert artifacts_path.is_dir()