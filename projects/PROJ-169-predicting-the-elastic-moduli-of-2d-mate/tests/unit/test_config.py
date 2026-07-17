import os
import random
import numpy as np
import torch
from pathlib import Path
import tempfile
import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from utils.config import Config


class TestConfig:
    """Unit tests for the Config class."""
    
    def test_default_initialization(self):
        """Test that default initialization sets expected values."""
        config = Config()
        assert config.seed == 42
        assert config.cpu_limit is None
        assert config.device.type == 'cpu'
        
    def test_seed_reproducibility(self):
        """Test that setting seed produces reproducible random values."""
        config1 = Config(seed=123)
        val1 = random.random()
        np_val1 = np.random.random()
        
        config2 = Config(seed=123)
        val2 = random.random()
        np_val2 = np.random.random()
        
        assert val1 == val2
        assert np_val1 == np_val2
        
    def test_cpu_limit_enforcement(self):
        """Test that CPU limits are set in environment variables."""
        config = Config(cpu_limit=4)
        assert os.environ.get('OMP_NUM_THREADS') == '4'
        assert os.environ.get('MKL_NUM_THREADS') == '4'
        assert torch.get_num_threads() == 4
        
    def test_project_root_customization(self):
        """Test custom project root path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_root = Path(tmpdir)
            config = Config(project_root=custom_root)
            assert config.project_root == custom_root
            assert config.code_dir == custom_root / 'code'
            assert config.data_dir == custom_root / 'data'
            
    def test_directory_creation(self):
        """Test that required directories are created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_root = Path(tmpdir)
            config = Config(project_root=custom_root)
            
            # Check that directories exist
            assert config.data_dir.exists()
            assert (config.data_dir / 'raw').exists()
            assert (config.data_dir / 'processed').exists()
            assert (config.data_dir / 'results').exists()
            assert config.figures_dir.exists()
            
    def test_cuda_disabled(self):
        """Test that CUDA is disabled by default."""
        config = Config()
        assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
        
    def test_device_property(self):
        """Test that device property returns CPU device."""
        config = Config()
        assert config.device.type == 'cpu'
        
    def test_get_path(self):
        """Test path resolution relative to project root."""
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_root = Path(tmpdir)
            config = Config(project_root=custom_root)
            
            resolved = config.get_path('data/processed/test.parquet')
            expected = custom_root / 'data' / 'processed' / 'test.parquet'
            assert resolved == expected
            
    def test_repr(self):
        """Test string representation."""
        config = Config(seed=999, cpu_limit=8)
        repr_str = repr(config)
        assert 'seed=999' in repr_str
        assert 'cpu_limit=8' in repr_str
        assert 'device=cpu' in repr_str
