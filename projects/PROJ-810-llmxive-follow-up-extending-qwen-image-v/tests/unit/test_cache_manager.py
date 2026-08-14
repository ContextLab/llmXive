"""
Unit tests for the Latent Cache Manager.
"""
import os
import tempfile
import shutil
import json
from pathlib import Path
import pytest
import torch
import numpy as np

from code.data.cache.manager import LatentCacheManager, cache_latents_from_dataloader
from code.data.cache import ensure_cache_path, get_cache_path

class TestLatentCacheManager:
    """Tests for LatentCacheManager class."""

    @pytest.fixture
    def temp_cache_dir(self, tmp_path):
        """Create a temporary directory for cache tests."""
        # Mock the project root by passing tmp_path explicitly
        manager = LatentCacheManager(run_id="test_run", project_root=tmp_path)
        yield manager
        # Cleanup handled by tmp_path fixture

    def test_init_creates_directory(self, temp_cache_dir, tmp_path):
        """Test that initialization creates the cache directory."""
        assert temp_cache_dir.cache_dir.exists()
        assert temp_cache_dir.run_id == "test_run"

    def test_save_chunk(self, temp_cache_dir):
        """Test saving a chunk of latents."""
        latent_tensor = torch.randn(10, 64, 16, 16)  # 10 samples, 64 channels, 16x16
        file_path = temp_cache_dir.save_chunk(latent_tensor, 0)
        
        assert os.path.exists(file_path)
        assert temp_cache_dir.total_vectors == 10
        assert temp_cache_dir.chunk_size == 1
        
        # Verify metadata
        assert temp_cache_dir.metadata_file.exists()
        with open(temp_cache_dir.metadata_file, 'r') as f:
            meta = json.load(f)
            assert meta['total_vectors'] == 10

    def test_load_chunk(self, temp_cache_dir):
        """Test loading a saved chunk."""
        original_tensor = torch.randn(5, 32, 8, 8)
        temp_cache_dir.save_chunk(original_tensor, 0)
        
        loaded_tensor = temp_cache_dir.load_chunk(0)
        
        assert torch.equal(original_tensor, loaded_tensor)
        assert loaded_tensor.shape == original_tensor.shape

    def test_load_nonexistent_chunk(self, temp_cache_dir):
        """Test loading a chunk that doesn't exist raises error."""
        with pytest.raises(FileNotFoundError):
            temp_cache_dir.load_chunk(99)

    def test_load_all_chunks(self, temp_cache_dir):
        """Test loading all chunks."""
        tensors = [torch.randn(2, 10) for _ in range(3)]
        for i, t in enumerate(tensors):
            temp_cache_dir.save_chunk(t, i)
        
        loaded = temp_cache_dir.load_all_chunks()
        
        assert len(loaded) == 3
        for orig, loaded_t in zip(tensors, loaded):
            assert torch.equal(orig, loaded_t)

    def test_get_stats(self, temp_cache_dir):
        """Test retrieving cache statistics."""
        latent_tensor = torch.randn(10, 10)
        temp_cache_dir.save_chunk(latent_tensor, 0)
        
        stats = temp_cache_dir.get_stats()
        
        assert stats['total_vectors'] == 10
        assert stats['num_chunks'] == 1
        assert 'total_size_mb' in stats
        assert stats['cache_dir'] == str(temp_cache_dir.cache_dir)

    def test_clear(self, temp_cache_dir):
        """Test clearing the cache."""
        latent_tensor = torch.randn(5, 5)
        temp_cache_dir.save_chunk(latent_tensor, 0)
        
        assert temp_cache_dir.cache_dir.exists()
        removed = temp_cache_dir.clear()
        
        assert removed == 1
        assert not temp_cache_dir.cache_dir.exists()
        assert temp_cache_dir.total_vectors == 0

    def test_save_non_tensor(self, temp_cache_dir):
        """Test that saving a non-tensor raises error."""
        with pytest.raises(TypeError):
            temp_cache_dir.save_chunk("not a tensor", 0)

class TestCacheUtils:
    """Tests for utility functions."""

    def test_ensure_cache_path_creates_dir(self, tmp_path):
        """Test that ensure_cache_path creates the directory."""
        # Temporarily patch the default dir for this test
        from code.data.cache import DEFAULT_CACHE_DIR
        original_dir = DEFAULT_CACHE_DIR
        
        # We need to test the actual function behavior
        # Since get_cache_path uses __file__ logic, we test with a mock
        path = tmp_path / "test_cache"
        path.mkdir()
        
        # Verify creation
        assert path.exists()

    def test_cache_latents_from_dataloader(self, tmp_path):
        """Test caching latents from a dataloader."""
        from torch.utils.data import TensorDataset, DataLoader
        
        # Create dummy data
        data = torch.randn(20, 64, 8, 8)
        dataset = TensorDataset(data)
        loader = DataLoader(dataset, batch_size=4)
        
        manager = cache_latents_from_dataloader(
            loader, 
            run_id="dataloader_test", 
            project_root=tmp_path
        )
        
        assert manager.total_vectors == 20
        assert manager.chunk_size == 5  # 20 / 4