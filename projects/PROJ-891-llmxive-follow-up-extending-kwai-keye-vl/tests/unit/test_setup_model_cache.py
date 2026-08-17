"""
Unit tests for setup_model_cache.py
"""
import os
import tempfile
from pathlib import Path
import pytest

# Import the function to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from setup_model_cache import ensure_model_cache_directory


class TestEnsureModelCacheDirectory:
    def test_creates_directory_if_not_exists(self, tmp_path):
        """Test that the function creates the models directory if it doesn't exist."""
        models_dir = tmp_path / "models"
        assert not models_dir.exists()
        
        result = ensure_model_cache_directory(tmp_path)
        
        assert models_dir.exists()
        assert models_dir.is_dir()
        assert result == models_dir

    def test_returns_existing_directory(self, tmp_path):
        """Test that the function returns the existing directory if it already exists."""
        models_dir = tmp_path / "models"
        models_dir.mkdir()
        
        result = ensure_model_cache_directory(tmp_path)
        
        assert result == models_dir

    def test_creates_gitkeep_file(self, tmp_path):
        """Test that a .gitkeep file is created inside the models directory."""
        models_dir = tmp_path / "models"
        
        ensure_model_cache_directory(tmp_path)
        
        gitkeep_file = models_dir / ".gitkeep"
        assert gitkeep_file.exists()
        assert gitkeep_file.is_file()

    def test_uses_current_working_directory_if_no_base_path(self, tmp_path):
        """Test that the function uses the current working directory if base_path is None."""
        # Change to tmp_path
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = ensure_model_cache_directory()
            
            models_dir = tmp_path / "models"
            assert result == models_dir
            assert models_dir.exists()
        finally:
            os.chdir(original_cwd)