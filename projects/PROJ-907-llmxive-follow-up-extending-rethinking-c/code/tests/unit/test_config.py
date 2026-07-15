"""
Unit tests for configuration management (T008).
Tests seed management, path resolution, and environment variable handling.
"""
import os
import pytest
from unittest.mock import patch
import sys
import random
import numpy as np

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.config import (
    set_seed, get_seed, get_imagenet_path, get_routing_cache_path,
    get_results_path, ensure_directories_exist, get_config_summary,
    ENV_SEED, ENV_IMAGENET_PATH, ENV_ROUTING_CACHE_PATH, ENV_RESULTS_PATH,
    DEFAULT_SEED, DEFAULT_IMAGENET_PATH, DEFAULT_ROUTING_CACHE_PATH, DEFAULT_RESULTS_PATH
)
from pathlib import Path

class TestSeedManagement:
    """Tests for random seed configuration."""

    def test_set_seed_explicit(self):
        """Test setting an explicit seed value."""
        seed_value = 12345
        result = set_seed(seed_value)
        assert result == seed_value
        
        # Verify randomness is affected
        random_val = random.random()
        np_val = np.random.random()
        torch_val = torch.random.random() if 'torch' in sys.modules else 0
        
        # Reset and check consistency
        set_seed(seed_value)
        assert random.random() == random_val
        assert np.random.random() == np_val

    def test_set_seed_from_env(self):
        """Test that seed is read from environment variable."""
        test_seed = 99999
        with patch.dict(os.environ, {ENV_SEED: str(test_seed)}):
            result = set_seed()
            assert result == test_seed

    def test_set_seed_default(self):
        """Test that default seed is used when no env var is set."""
        # Clear env var if it exists
        with patch.dict(os.environ, {ENV_SEED: ""}, clear=True):
            if ENV_SEED in os.environ:
                del os.environ[ENV_SEED]
            
            result = set_seed()
            assert result == DEFAULT_SEED

    def test_get_seed(self):
        """Test getting the current seed."""
        test_seed = 54321
        with patch.dict(os.environ, {ENV_SEED: str(test_seed)}):
            assert get_seed() == test_seed

class TestPathManagement:
    """Tests for path configuration."""

    def test_get_imagenet_path_default(self):
        """Test default ImageNet path."""
        with patch.dict(os.environ, {ENV_IMAGENET_PATH: ""}, clear=True):
            if ENV_IMAGENET_PATH in os.environ:
                del os.environ[ENV_IMAGENET_PATH]
            
            path = get_imagenet_path()
            assert path == Path(DEFAULT_IMAGENET_PATH)

    def test_get_imagenet_path_env(self):
        """Test ImageNet path from environment."""
        custom_path = "/custom/path/imagenet"
        with patch.dict(os.environ, {ENV_IMAGENET_PATH: custom_path}):
            path = get_imagenet_path()
            assert path == Path(custom_path)

    def test_get_routing_cache_path_default(self):
        """Test default routing cache path."""
        with patch.dict(os.environ, {ENV_ROUTING_CACHE_PATH: ""}, clear=True):
            if ENV_ROUTING_CACHE_PATH in os.environ:
                del os.environ[ENV_ROUTING_CACHE_PATH]
            
            path = get_routing_cache_path()
            assert path == Path(DEFAULT_ROUTING_CACHE_PATH)

    def test_get_routing_cache_path_env(self):
        """Test routing cache path from environment."""
        custom_path = "/custom/cache/path"
        with patch.dict(os.environ, {ENV_ROUTING_CACHE_PATH: custom_path}):
            path = get_routing_cache_path()
            assert path == Path(custom_path)

    def test_get_results_path_default(self):
        """Test default results path."""
        with patch.dict(os.environ, {ENV_RESULTS_PATH: ""}, clear=True):
            if ENV_RESULTS_PATH in os.environ:
                del os.environ[ENV_RESULTS_PATH]
            
            path = get_results_path()
            assert path == Path(DEFAULT_RESULTS_PATH)

    def test_get_results_path_env(self):
        """Test results path from environment."""
        custom_path = "/custom/results/path"
        with patch.dict(os.environ, {ENV_RESULTS_PATH: custom_path}):
            path = get_results_path()
            assert path == Path(custom_path)

    def test_ensure_directories_exist(self):
        """Test that ensure_directories_exist creates necessary folders."""
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Set paths to temp directory
            test_paths = {
                ENV_IMAGENET_PATH: f"{tmpdir}/imagenet",
                ENV_ROUTING_CACHE_PATH: f"{tmpdir}/cache",
                ENV_RESULTS_PATH: f"{tmpdir}/results"
            }
            
            with patch.dict(os.environ, test_paths):
                ensure_directories_exist()
                
                # Verify directories were created
                for key, val in test_paths.items():
                    assert Path(val).exists(), f"Directory {val} was not created"

    def test_get_config_summary(self):
        """Test configuration summary generation."""
        test_seed = 77777
        with patch.dict(os.environ, {
            ENV_SEED: str(test_seed),
            ENV_IMAGENET_PATH: "/test/imagenet",
            ENV_ROUTING_CACHE_PATH: "/test/cache",
            ENV_RESULTS_PATH: "/test/results"
        }):
            summary = get_config_summary()
            
            assert summary["seed"] == test_seed
            assert summary["imagenet_path"] == "/test/imagenet"
            assert summary["routing_cache_path"] == "/test/cache"
            assert summary["results_path"] == "/test/results"
            assert summary["environment"]["seed_set"] is True
            assert summary["environment"]["imagenet_path_set"] is True
            assert summary["environment"]["routing_cache_path_set"] is True
            assert summary["environment"]["results_path_set"] is True
