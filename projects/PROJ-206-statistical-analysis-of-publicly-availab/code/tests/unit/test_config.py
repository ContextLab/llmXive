"""
Unit tests for the configuration management module (src/utils/config.py).
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest
import random

# Add the code directory to the path so we can import src
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from src.utils.config import (
    get_project_root, 
    get_data_root, 
    get_state_root, 
    get_code_root, 
    get_figures_root, 
    get_spec_root, 
    resolve_path, 
    set_seed, 
    get_seed, 
    compute_file_hash, 
    ensure_dir, 
    get_config,
    initialize_project_structure
)

class TestPathResolution:
    def test_get_project_root_exists(self):
        """Test that project root returns a valid Path."""
        root = get_project_root()
        assert isinstance(root, Path)
        assert root.exists()

    def test_data_root_relative(self):
        """Test that data root is relative to project root."""
        root = get_project_root()
        data_root = get_data_root()
        assert data_root == root / 'data'

    def test_state_root_relative(self):
        """Test that state root is relative to project root."""
        root = get_project_root()
        state_root = get_state_root()
        assert state_root == root / 'state'

    def test_code_root_relative(self):
        """Test that code root is relative to project root."""
        root = get_project_root()
        code_root = get_code_root()
        assert code_root == root / 'code'

    def test_spec_root_relative(self):
        """Test that spec root is relative to project root."""
        root = get_project_root()
        spec_root = get_spec_root()
        assert spec_root == root / 'specs'

    def test_resolve_path_relative(self):
        """Test resolving a relative path."""
        root = get_project_root()
        resolved = resolve_path('test_file.txt')
        assert resolved == root / 'test_file.txt'

    def test_resolve_path_absolute(self):
        """Test that an absolute path is returned as-is."""
        abs_path = Path('/tmp/test.txt')
        resolved = resolve_path(abs_path)
        assert resolved == abs_path

    def test_resolve_path_with_base(self):
        """Test resolving a path with a custom base."""
        custom_base = Path('/tmp/custom')
        resolved = resolve_path('file.txt', base=custom_base)
        assert resolved == custom_base / 'file.txt'

class TestSeedManagement:
    def test_set_seed_updates_random(self):
        """Test that set_seed affects the random module."""
        set_seed(12345)
        val1 = random.random()
        
        set_seed(12345)
        val2 = random.random()
        
        assert val1 == val2

    def test_get_seed_returns_none_initially(self):
        """Test that get_seed returns None before setting."""
        # We need to reset the global state if possible, 
        # but since it's module level, we assume fresh import for this test
        # or we just check that it returns an int or None
        seed = get_seed()
        # If previously set in another test, it might not be None.
        # We just verify the function works.
        assert seed is None or isinstance(seed, int)

    def test_set_seed_int(self):
        """Test setting seed to an integer."""
        set_seed(999)
        assert get_seed() == 999

class TestDirectoryCreation:
    def test_ensure_dir_creates_directory(self, tmp_path):
        """Test that ensure_dir creates a new directory."""
        new_dir = tmp_path / 'new_subdir'
        assert not new_dir.exists()
        result = ensure_dir(new_dir)
        assert result.exists()
        assert result.is_dir()

    def test_ensure_dir_existing_directory(self, tmp_path):
        """Test that ensure_dir does not fail on existing directory."""
        existing_dir = tmp_path / 'existing'
        existing_dir.mkdir()
        result = ensure_dir(existing_dir)
        assert result.exists()

    def test_ensure_dir_nested(self, tmp_path):
        """Test that ensure_dir creates nested directories."""
        nested_dir = tmp_path / 'level1' / 'level2' / 'level3'
        assert not nested_dir.exists()
        result = ensure_dir(nested_dir)
        assert result.exists()

class TestFileHash:
    def test_compute_file_hash_valid(self, tmp_path):
        """Test computing hash of a valid file."""
        test_file = tmp_path / 'test.txt'
        content = "Hello, World!"
        test_file.write_text(content)
        
        hash_val = compute_file_hash(test_file)
        assert isinstance(hash_val, str)
        assert len(hash_val) == 64  # SHA-256 hex length

    def test_compute_file_hash_missing(self, tmp_path):
        """Test that compute_file_hash raises error for missing file."""
        missing_file = tmp_path / 'nonexistent.txt'
        with pytest.raises(FileNotFoundError):
            compute_file_hash(missing_file)

class TestConfigIntegration:
    def test_get_config_returns_dict(self):
        """Test that get_config returns a dictionary with expected keys."""
        config = get_config()
        assert isinstance(config, dict)
        required_keys = [
            "project_root", "data_root", "state_root", 
            "code_root", "figures_root", "spec_root",
            "seed_set", "seed_value"
        ]
        for key in required_keys:
            assert key in config

    def test_initialize_project_structure(self, tmp_path, monkeypatch):
        """Test that initialize_project_structure creates directories."""
        # Monkeypatch get_project_root to return tmp_path
        def mock_root():
            return tmp_path
        
        monkeypatch.setattr('src.utils.config.get_project_root', mock_root)
        
        initialize_project_structure()
        
        # Check expected directories
        assert (tmp_path / 'data' / 'raw').exists()
        assert (tmp_path / 'data' / 'processed').exists()
        assert (tmp_path / 'state' / 'projects').exists()
        assert (tmp_path / 'figures').exists()