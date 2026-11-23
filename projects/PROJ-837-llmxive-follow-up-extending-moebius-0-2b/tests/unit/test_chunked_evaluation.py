"""
Unit tests for chunked FID/LPIPS evaluation (T040).

Tests the memory-safe chunked processing logic to ensure it stays within
the 7GB RAM limit and correctly computes metrics in batches.
"""
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import numpy as np
import pytest
import torch
from PIL import Image

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from eval.chunked_fid_lpips import (
    InceptionFeatureExtractor,
    LPIPSWrapper,
    get_available_ram_gb,
    estimate_memory_usage,
    run_chunked_evaluation
)
from eval.metrics import InpaintingEvalDataset
from utils.seed import set_seed

class TestChunkedEvaluation:
    """Test suite for chunked evaluation logic."""
    
    @pytest.fixture
    def temp_dataset_dir(self, tmp_path):
        """Create a temporary dataset directory with dummy images."""
        dataset_dir = tmp_path / 'masked_images'
        dataset_dir.mkdir()
        
        # Create dummy images
        for i in range(10):
            # Original image
            orig_img = Image.new('RGB', (256, 256), color=(128, 128, 128))
            orig_img.save(dataset_dir / f'orig_{i:04d}.png')
            
            # Masked image
            masked_img = Image.new('RGB', (256, 256), color=(64, 64, 64))
            masked_img.save(dataset_dir / f'masked_{i:04d}.png')
            
            # GT image
            gt_img = Image.new('RGB', (256, 256), color=(192, 192, 192))
            gt_img.save(dataset_dir / f'gt_{i:04d}.png')
        
        return dataset_dir
    
    def test_get_available_ram_gb(self):
        """Test that RAM estimation returns a positive value."""
        ram = get_available_ram_gb()
        assert isinstance(ram, float)
        assert ram > 0
    
    def test_estimate_memory_usage(self):
        """Test memory estimation function."""
        # Test with default batch size
        mem = estimate_memory_usage(batch_size=32)
        assert isinstance(mem, float)
        assert mem > 0
        assert mem < 1.0  # Should be less than 1GB for typical batch
        
        # Test with larger batch size
        mem_large = estimate_memory_usage(batch_size=128)
        assert mem_large > mem  # Larger batch should use more memory
    
    @patch('eval.chunked_fid_lpips.inception_v3')
    def test_inception_feature_extractor_init(self, mock_inception):
        """Test Inception feature extractor initialization."""
        # Mock the model
        mock_model = MagicMock()
        mock_model.children.return_value = [MagicMock()] * 10
        mock_inception.return_value = mock_model
        
        extractor = InceptionFeatureExtractor(device='cpu')
        
        assert extractor.device == 'cpu'
        assert extractor.model is not None
    
    def test_run_chunked_evaluation_structure(self, temp_dataset_dir):
        """Test that chunked evaluation returns the expected structure."""
        # Create a small dataset
        dataset = InpaintingEvalDataset(root_dir=str(temp_dataset_dir))
        
        # Run evaluation with small batch size
        results = run_chunked_evaluation(
            dataset=dataset,
            batch_size=2,
            chunk_size=2,
            device='cpu'
        )
        
        # Verify result structure
        assert isinstance(results, dict)
        assert 'fid' in results
        assert 'lpips' in results
        assert 'latency_per_sample' in results
        assert 'total_samples' in results
        assert 'total_batches' in results
        assert 'memory_safe' in results
        
        # Verify values are reasonable
        assert results['total_samples'] > 0
        assert results['total_batches'] > 0
        assert results['memory_safe'] is True
    
    def test_chunked_vs_full_processing(self, temp_dataset_dir):
        """Test that chunked processing produces consistent results with full processing."""
        # This is a structural test; actual numerical consistency would require
        # mocking the feature extractors to return deterministic values
        
        dataset = InpaintingEvalDataset(root_dir=str(temp_dataset_dir))
        
        # Run with different chunk sizes
        results_small = run_chunked_evaluation(dataset, batch_size=2, chunk_size=1, device='cpu')
        results_large = run_chunked_evaluation(dataset, batch_size=2, chunk_size=4, device='cpu')
        
        # Both should process the same number of samples
        assert results_small['total_samples'] == results_large['total_samples']
        assert results_small['total_batches'] == results_large['total_batches']
    
    def test_memory_constraint_enforcement(self, temp_dataset_dir):
        """Test that evaluation respects memory constraints."""
        dataset = InpaintingEvalDataset(root_dir=str(temp_dataset_dir))
        
        # Run with very small chunk size to test memory handling
        results = run_chunked_evaluation(
            dataset=dataset,
            batch_size=1,
            chunk_size=1,
            device='cpu'
        )
        
        # Should complete without memory errors
        assert results['memory_safe'] is True
        assert results['total_samples'] == len(dataset)

if __name__ == '__main__':
    pytest.main([__file__, '-v'])