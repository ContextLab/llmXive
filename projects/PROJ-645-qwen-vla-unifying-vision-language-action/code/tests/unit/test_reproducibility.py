"""
Unit tests for src/utils/reproducibility.py
"""
import json
import os
import tempfile
import pytest
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.utils.reproducibility import (
    generate_seeds,
    set_global_seeds,
    save_seeds,
    load_seeds,
    get_git_commit_hash,
    get_python_version,
    create_reproducibility_manifest,
    log_manifest_to_file,
    DEFAULT_SEED_COUNT
)


class TestGenerateSeeds:
    def test_generate_seeds_default_count(self):
        """Test that default seed count is generated."""
        seeds = generate_seeds()
        assert len(seeds) == DEFAULT_SEED_COUNT
        assert all(isinstance(s, int) for s in seeds)
    
    def test_generate_seeds_custom_count(self):
        """Test custom seed count."""
        seeds = generate_seeds(10)
        assert len(seeds) == 10
    
    def test_generate_seeds_deterministic_with_base(self):
        """Test that same base seed produces same results."""
        seeds1 = generate_seeds(5, base_seed=12345)
        seeds2 = generate_seeds(5, base_seed=12345)
        assert seeds1 == seeds2
    
    def test_generate_seeds_different_base(self):
        """Test that different base seeds produce different results."""
        seeds1 = generate_seeds(5, base_seed=11111)
        seeds2 = generate_seeds(5, base_seed=22222)
        assert seeds1 != seeds2
    
    def test_seed_range_validity(self):
        """Test that seeds are within valid 32-bit integer range."""
        seeds = generate_seeds(100)
        for s in seeds:
            assert 0 <= s <= 2**31 - 1


class TestSaveAndLoadSeeds:
    def test_save_and_load_seeds(self):
        """Test saving and loading seeds to/from file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test_seeds.json")
            seeds = [1, 2, 3, 4, 5]
            
            save_seeds(seeds, path)
            loaded = load_seeds(path)
            
            assert loaded == seeds
    
    def test_save_seeds_creates_directory(self):
        """Test that save_seeds creates parent directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_path = os.path.join(tmpdir, "subdir", "nested", "seeds.json")
            save_seeds([1, 2], nested_path)
            assert os.path.exists(nested_path)
    
    def test_load_seeds_file_not_found(self):
        """Test error when file does not exist."""
        with pytest.raises(FileNotFoundError):
            load_seeds("/nonexistent/path/seeds.json")
    
    def test_save_seeds_json_structure(self):
        """Test the JSON structure of saved seeds."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "seeds.json")
            seeds = [100, 200, 300]
            
            save_seeds(seeds, path)
            
            with open(path, "r") as f:
                data = json.load(f)
            
            assert "seeds" in data
            assert "generated_at" in data
            assert "seed_count" in data
            assert data["seed_count"] == 3
            assert data["seeds"] == seeds


class TestSetGlobalSeeds:
    def test_set_global_seeds_basic(self):
        """Test setting global seeds with a single seed."""
        seeds = [42]
        result = set_global_seeds(seeds, 0)
        
        assert result["seed"] == 42
        assert result["seed_index"] == 0
        assert result["python_random"] == 42
    
    def test_set_global_seeds_invalid_index(self):
        """Test error when seed_index is out of range."""
        seeds = [1, 2, 3]
        with pytest.raises(ValueError):
            set_global_seeds(seeds, 5)
    
    def test_set_global_seeds_preserves_list(self):
        """Test that the seed list is preserved in result."""
        seeds = [111, 222, 333]
        result = set_global_seeds(seeds, 1)
        
        assert result["seed"] == 222
        assert result["seed_index"] == 1


class TestReproducibilityManifest:
    def test_create_manifest_creates_file(self):
        """Test that create_reproducibility_manifest creates a valid file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "manifest.yaml")
            seeds = [1, 2, 3]
            hyperparams = {"lr": 0.001, "batch_size": 32}
            
            result_path = create_reproducibility_manifest(seeds, hyperparams, path)
            
            assert os.path.exists(result_path)
            assert result_path == Path(path)
    
    def test_manifest_contains_required_fields(self):
        """Test that manifest contains all required sections."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "manifest.yaml")
            seeds = [123]
            hyperparams = {"test": True}
            
            create_reproducibility_manifest(seeds, hyperparams, path)
            
            with open(path, "r") as f:
                import yaml
                manifest = yaml.safe_load(f)
            
            assert "metadata" in manifest
            assert "environment" in manifest
            assert "random_seeds" in manifest
            assert "hyperparameters" in manifest
            
            assert manifest["random_seeds"]["values"] == seeds
            assert manifest["hyperparameters"]["test"] is True
    
    def test_manifest_git_commit(self):
        """Test that git commit is included or marked disabled."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "manifest.yaml")
            seeds = [1]
            
            # Test with git included
            create_reproducibility_manifest(seeds, {}, path, include_git=True)
            
            with open(path, "r") as f:
                import yaml
                manifest = yaml.safe_load(f)
            
            assert "version_control" in manifest
            assert "git_commit" in manifest["version_control"]
            # Commit should be a string (hash or "unknown")
            assert isinstance(manifest["version_control"]["git_commit"], str)
    
    def test_log_manifest_to_file(self):
        """Test the full pipeline of logging manifest."""
        with tempfile.TemporaryDirectory() as tmpdir:
            seeds_path = os.path.join(tmpdir, "seeds.json")
            manifest_path = os.path.join(tmpdir, "manifest.yaml")
            
            seeds = [999, 888]
            hyperparams = {"model": "qwen-vla"}
            
            result = log_manifest_to_file(seeds, hyperparams, manifest_path)
            
            assert os.path.exists(result)
            assert os.path.exists(seeds_path)
            
            # Verify seeds were saved
            loaded_seeds = load_seeds(seeds_path)
            assert loaded_seeds == seeds


class TestUtilityFunctions:
    def test_get_python_version_format(self):
        """Test that python version string is formatted correctly."""
        version = get_python_version()
        parts = version.split(".")
        assert len(parts) == 3
        assert all(p.isdigit() for p in parts)
    
    @patch('subprocess.run')
    def test_get_git_commit_hash_success(self, mock_run):
        """Test git commit hash retrieval on success."""
        mock_run.return_value = MagicMock(returncode=0, stdout="abc123\n")
        commit = get_git_commit_hash()
        assert commit == "abc123"
    
    @patch('subprocess.run')
    def test_get_git_commit_hash_failure(self, mock_run):
        """Test git commit hash retrieval on failure."""
        mock_run.return_value = MagicMock(returncode=1, stderr="error")
        commit = get_git_commit_hash()
        assert commit == "unknown"
    
    @patch('subprocess.run', side_effect=FileNotFoundError)
    def test_get_git_commit_hash_no_git(self, mock_run):
        """Test git commit hash when git is not installed."""
        commit = get_git_commit_hash()
        assert commit == "unknown"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
