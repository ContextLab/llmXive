"""
Unit tests for download_weights.py
"""
import os
import sys
import tempfile
import numpy as np
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.ingestion.download_weights import (
    load_real_weights,
    generate_proxy_weights,
    save_weights,
    process_dataset
)

class TestGenerateProxyWeights:
    """Tests for proxy weight generation."""
    
    def test_proxy_weights_seed_reproducibility(self):
        """Test that proxy weights are reproducible with seed=42."""
        # Generate twice
        weights1 = generate_proxy_weights('test', (10, 5))
        weights2 = generate_proxy_weights('test', (10, 5))
        
        # Check that A and B matrices are identical
        np.testing.assert_array_equal(weights1['A'], weights2['A'])
        np.testing.assert_array_equal(weights1['B'], weights2['B'])
    
    def test_proxy_weights_statistics(self):
        """Test that proxy weights have correct statistical properties."""
        weights = generate_proxy_weights('test', (100, 50))
        
        # Check mean is approximately 0
        assert abs(np.mean(weights['A'])) < 0.5
        assert abs(np.mean(weights['B'])) < 0.5
        
        # Check std is approximately 1
        assert 0.5 < np.std(weights['A']) < 1.5
        assert 0.5 < np.std(weights['B']) < 1.5
    
    def test_proxy_weights_shape(self):
        """Test that proxy weights have correct shapes."""
        expected_shape = (64, 32)
        weights = generate_proxy_weights('test', expected_shape)
        
        # A should be (down_dim, hidden_dim)
        # B should be (hidden_dim, up_dim)
        assert weights['A'].ndim == 2
        assert weights['B'].ndim == 2
        assert weights['A'].shape[0] == expected_shape[0]
        assert weights['B'].shape[1] == expected_shape[1]
    
    def test_proxy_metadata(self):
        """Test that proxy weights include correct metadata."""
        weights = generate_proxy_weights('test_dataset', (10, 5))
        
        assert weights['is_proxy'] == True
        assert weights['generation_seed'] == 42
        assert weights['mean'] == 0.0
        assert weights['std'] == 1.0
        assert weights['dataset_name'] == 'test_dataset'

class TestSaveWeights:
    """Tests for weight saving functionality."""
    
    def test_save_weights_creates_file(self):
        """Test that save_weights creates the output file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'test_weights.npz'
            weights = {
                'A': np.random.randn(10, 5).astype(np.float32),
                'B': np.random.randn(5, 10).astype(np.float32),
                'is_proxy': False
            }
            
            result_path = save_weights(weights, str(output_path), is_proxy=False)
            
            assert Path(result_path).exists()
            assert result_path.endswith('.npz')
    
    def test_save_weights_metadata(self):
        """Test that save_weights creates metadata JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'test_weights.npz'
            weights = {
                'A': np.random.randn(10, 5).astype(np.float32),
                'B': np.random.randn(5, 10).astype(np.float32),
                'is_proxy': True,
                'generation_seed': 42
            }
            
            save_weights(weights, str(output_path), is_proxy=True)
            
            metadata_path = Path(str(output_path).replace('.npz', '.json'))
            assert metadata_path.exists()
            
            import json
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            assert metadata['is_proxy'] == True
            assert metadata['generation_seed'] == 42
    
    def test_save_weights_loadable(self):
        """Test that saved weights can be loaded back."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'test_weights.npz'
            original_weights = {
                'A': np.random.randn(10, 5).astype(np.float32),
                'B': np.random.randn(5, 10).astype(np.float32),
                'is_proxy': True
            }
            
            save_weights(original_weights, str(output_path), is_proxy=True)
            
            # Load back
            loaded = np.load(output_path)
            
            np.testing.assert_array_almost_equal(
                loaded['A'], original_weights['A']
            )
            np.testing.assert_array_almost_equal(
                loaded['B'], original_weights['B']
            )
            assert loaded['is_proxy'] == True

class TestLoadRealWeights:
    """Tests for real weight loading (mocked)."""
    
    @patch('src.ingestion.download_weights.load_dataset')
    def test_load_real_weights_success(self, mock_load_dataset):
        """Test successful loading of real weights."""
        # Mock dataset
        mock_dataset = MagicMock()
        mock_item = {
            'weights_A': np.random.randn(10, 5).tolist(),
            'weights_B': np.random.randn(5, 10).tolist()
        }
        mock_dataset.__iter__ = MagicMock(return_value=iter([mock_item]))
        mock_load_dataset.return_value = mock_dataset
        
        result = load_real_weights('test/dataset', 'weights/*.npz')
        
        assert result is not None
        weights, is_proxy = result
        assert is_proxy == False
        assert 'weights_A' in weights
        assert 'weights_B' in weights
    
    def test_load_real_weights_failure(self):
        """Test failure to load real weights returns None."""
        # This should fail since dataset doesn't exist
        result = load_real_weights('nonexistent/dataset', 'weights/*.npz')
        assert result is None
