"""
Unit tests for download_weights.py
"""
import os
import tempfile
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from src.ingestion.download_weights import (
    verify_source_existence,
    generate_proxy_weights,
    download_real_weights,
    DATASET_IDS
)

class TestVerifySourceExistence:
    """Tests for verify_source_existence function."""
    
    @patch('src.ingestion.download_weights.HfApi')
    def test_existing_dataset(self, mock_hf_api):
        """Test with an existing dataset."""
        mock_api_instance = MagicMock()
        mock_hf_api.return_value = mock_api_instance
        mock_api_instance.list_repo_files.return_value = ['file1.npy', 'file2.npy']
        
        result = verify_source_existence('test/dataset')
        
        assert result is True
        mock_api_instance.list_repo_files.assert_called_once_with(
            'test/dataset', 
            repo_type="dataset"
        )
    
    @patch('src.ingestion.download_weights.HfApi')
    def test_nonexistent_dataset(self, mock_hf_api):
        """Test with a non-existing dataset."""
        mock_api_instance = MagicMock()
        mock_hf_api.return_value = mock_api_instance
        mock_api_instance.list_repo_files.side_effect = Exception("Dataset not found")
        
        result = verify_source_existence('nonexistent/dataset')
        
        assert result is False

class TestGenerateProxyWeights:
    """Tests for generate_proxy_weights function."""
    
    def test_generate_proxy_weights_creates_files(self):
        """Test that proxy weights are generated correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            expected_shapes = {
                'A': (64, 32),
                'B': (32, 64)
            }
            
            metadata = generate_proxy_weights(
                'test/dataset',
                output_dir,
                expected_shapes
            )
            
            # Check metadata structure
            assert 'A' in metadata
            assert 'B' in metadata
            assert metadata['A']['shape'] == [64, 32]
            assert metadata['B']['shape'] == [32, 64]
            assert metadata['A']['dtype'] == 'float32'
            assert metadata['A']['is_proxy'] is True
            assert metadata['B']['is_proxy'] is True
            
            # Check files exist
            assert (output_dir / 'A.npy').exists()
            assert (output_dir / 'B.npy').exists()
            
            # Verify file contents
            A_data = np.load(output_dir / 'A.npy')
            B_data = np.load(output_dir / 'B.npy')
            
            assert A_data.shape == (64, 32)
            assert B_data.shape == (32, 64)
            assert A_data.dtype == np.float32
            assert B_data.dtype == np.float32
            
            # Verify values are from normal distribution (not zeros)
            assert np.any(A_data != 0)
            assert np.any(B_data != 0)

class TestDownloadRealWeights:
    """Tests for download_real_weights function."""
    
    @patch('src.ingestion.download_weights.load_dataset')
    def test_download_real_weights_success(self, mock_load_dataset):
        """Test successful download of real weights."""
        # Mock dataset with samples
        mock_sample1 = {'A': np.random.rand(64, 32).tolist(), 'B': np.random.rand(32, 64).tolist()}
        mock_sample2 = {'A': np.random.rand(64, 32).tolist(), 'B': np.random.rand(32, 64).tolist()}
        
        mock_dataset = MagicMock()
        mock_dataset.__iter__ = MagicMock(return_value=iter([mock_sample1, mock_sample2]))
        mock_load_dataset.return_value = mock_dataset
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            
            metadata, success = download_real_weights('test/dataset', output_dir)
            
            assert success is True
            assert metadata['dataset_id'] == 'test/dataset'
            assert metadata['is_proxy'] is False
            assert len(metadata['weights']) == 2
            
            # Check that files were created
            assert (output_dir / 'adapter_1_A.npy').exists()
            assert (output_dir / 'adapter_1_B.npy').exists()
            assert (output_dir / 'adapter_2_A.npy').exists()
            assert (output_dir / 'adapter_2_B.npy').exists()
    
    @patch('src.ingestion.download_weights.load_dataset')
    def test_download_real_weights_failure(self, mock_load_dataset):
        """Test handling of download failure."""
        mock_load_dataset.side_effect = Exception("Download failed")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            
            metadata, success = download_real_weights('test/dataset', output_dir)
            
            assert success is False
            assert metadata == {}