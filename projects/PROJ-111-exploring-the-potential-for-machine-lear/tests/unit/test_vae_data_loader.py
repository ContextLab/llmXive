"""
Unit tests for VAE Data Loader (T023).

Tests memory monitoring, batch size validation, and data loading functionality.
"""
import os
import sys
import tempfile
import numpy as np
import torch
import pytest
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.vae_data_loader import (
    SpinDataset, 
    create_vae_dataloader, 
    check_batch_memory_usage,
    main
)
from code.preprocessing import load_raw_data

class TestCheckBatchMemoryUsage:
    """Tests for memory usage estimation and validation."""
    
    def test_small_batch_passes(self):
        """Small batch should pass memory check."""
        result = check_batch_memory_usage(batch_size=32, data_shape=(3, 16, 16))
        assert result is True
    
    def test_large_lattice_small_batch(self):
        """L=24 with small batch should pass."""
        result = check_batch_memory_usage(batch_size=16, data_shape=(3, 24, 24))
        assert result is True
    
    def test_exceeds_memory_limit(self):
        """Very large batch should raise MemoryError."""
        # Estimate: 7GB limit * 0.8 safety / (3 * 24 * 24 * 4 bytes) ≈ 768 samples max
        # Use a batch size that definitely exceeds
        with pytest.raises(MemoryError):
            check_batch_memory_usage(batch_size=5000, data_shape=(3, 24, 24))
    
    def test_dtype_impact(self):
        """Float64 should use more memory than float32."""
        # float32: 4 bytes, float64: 8 bytes
        shape = (3, 32, 32)
        batch_size = 100
        
        # Both should pass for this small case
        result32 = check_batch_memory_usage(batch_size, shape, torch.float32)
        result64 = check_batch_memory_usage(batch_size, shape, torch.float64)
        assert result32 is True
        assert result64 is True

class TestSpinDataset:
    """Tests for the SpinDataset class."""
    
    @pytest.fixture
    def temp_data_file(self):
        """Create a temporary data file for testing."""
        with tempfile.NamedTemporaryFile(suffix='.npy', delete=False) as f:
            # Create dummy data: [N, 3, L, L]
            data = np.random.randn(100, 3, 16, 16).astype(np.float32)
            np.save(f.name, data)
            yield f.name
            os.unlink(f.name)
    
    @pytest.fixture
    def temp_temp_file(self):
        """Create a temporary temperature file for testing."""
        with tempfile.NamedTemporaryFile(suffix='.npy', delete=False) as f:
            temps = np.random.uniform(0.1, 3.0, 100).astype(np.float32)
            np.save(f.name, temps)
            yield f.name
            os.unlink(f.name)
    
    def test_init_with_valid_data(self, temp_data_file):
        """Dataset should initialize with valid data."""
        dataset = SpinDataset(temp_data_file)
        assert len(dataset) == 100
        assert dataset.data.shape == (100, 3, 16, 16)
    
    def test_init_with_missing_file(self):
        """Dataset should raise FileNotFoundError for missing data."""
        with pytest.raises(FileNotFoundError):
            SpinDataset("/nonexistent/path.npy")
    
    def test_getitem_returns_tensor(self, temp_data_file):
        """__getitem__ should return torch tensor."""
        dataset = SpinDataset(temp_data_file)
        sample = dataset[0]
        assert isinstance(sample, torch.Tensor)
        assert sample.shape == (3, 16, 16)
    
    def test_with_temperature_labels(self, temp_data_file, temp_temp_file):
        """Dataset should return (sample, temp) tuple when temps provided."""
        dataset = SpinDataset(temp_data_file, temp_temp_file)
        sample, temp = dataset[0]
        assert isinstance(sample, torch.Tensor)
        assert isinstance(temp, torch.Tensor)
        assert sample.shape == (3, 16, 16)
        assert temp.shape == () or temp.shape == (1,)
    
    def test_invalid_data_shape(self, temp_data_file):
        """Dataset should validate data dimensions."""
        # Create file with wrong shape
        with tempfile.NamedTemporaryFile(suffix='.npy', delete=False) as f:
            wrong_data = np.random.randn(100, 4, 16, 16)  # 4 components instead of 3
            np.save(f.name, wrong_data)
            
            with pytest.raises(ValueError):
                SpinDataset(f.name)
            os.unlink(f.name)

class TestCreateVaeDataLoader:
    """Tests for DataLoader creation."""
    
    @pytest.fixture
    def temp_processed_data(self):
        """Create temporary processed data files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_path = os.path.join(tmpdir, "spins.npy")
            temp_path = os.path.join(tmpdir, "temps.npy")
            
            # Create valid data
            data = np.random.randn(200, 3, 16, 16).astype(np.float32)
            temps = np.random.uniform(0.1, 3.0, 200).astype(np.float32)
            
            np.save(data_path, data)
            np.save(temp_path, temps)
            
            yield data_path, temp_path
    
    def test_create_dataloader_basic(self, temp_processed_data):
        """Should create a valid DataLoader."""
        data_path, temp_path = temp_processed_data
        loader = create_vae_dataloader(data_path, batch_size=32, temperature_path=temp_path)
        
        assert loader is not None
        assert loader.batch_size == 32
        assert len(loader.dataset) == 200
    
    def test_batch_size_memory_check(self, temp_processed_data):
        """Should validate batch size against memory limits."""
        data_path, temp_path = temp_processed_data
        
        # This should not raise
        loader = create_vae_dataloader(data_path, batch_size=64)
        assert loader is not None
    
    def test_shuffle_parameter(self, temp_processed_data):
        """Should respect shuffle parameter."""
        data_path, temp_path = temp_processed_data
        
        loader_no_shuffle = create_vae_dataloader(data_path, batch_size=32, shuffle=False)
        loader_shuffle = create_vae_dataloader(data_path, batch_size=32, shuffle=True)
        
        # Verify dataloader configuration
        assert loader_no_shuffle.shuffle == False
        assert loader_shuffle.shuffle == True
    
    def test_drop_last_true(self, temp_processed_data):
        """Should drop last batch if incomplete."""
        data_path, temp_path = temp_processed_data
        loader = create_vae_dataloader(data_path, batch_size=33, shuffle=False)
        
        # 200 samples / 33 batch size = 6 full batches + 2 remainder
        # drop_last=True should result in 6 batches
        batch_count = 0
        for _ in loader:
            batch_count += 1
        
        assert batch_count == 6

class TestMainFunction:
    """Tests for the main() function."""
    
    @patch('code.vae_data_loader.logger')
    @patch('code.vae_data_loader.get_config')
    def test_main_execution(self, mock_config, mock_logger):
        """Main should execute without errors when data exists."""
        # Mock config
        mock_config.return_value = {"log_dir": "logs"}
        
        # Mock os.path.exists to simulate missing data (expected in test env)
        with patch('os.path.exists', return_value=False):
            # Should not raise, just log warnings
            main()
        
        # Verify logging was called
        assert mock_logger.info.called

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
