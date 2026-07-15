"""
Unit tests for the data_loader module.

These tests verify that:
1. The loader attempts to fetch real data.
2. The loader raises an exception if the real source is unreachable.
3. No synthetic fallback is used.
"""

import pytest
from unittest.mock import patch, MagicMock
import sys

# Import the module under test
from src import data_loader

class TestDataLoader:
    """Test cases for data_loader module."""

    def test_load_imagenet_validation_streaming_imports_correctly(self):
        """Verify the function exists and has correct signature."""
        assert callable(data_loader.load_imagenet_validation_streaming)
        
        # Check parameters
        import inspect
        sig = inspect.signature(data_loader.load_imagenet_validation_streaming)
        params = list(sig.parameters.keys())
        assert 'streaming' in params
        assert 'num_samples' in params

    def test_load_imagenet_raises_on_real_source_failure(self):
        """
        Verify that the loader raises an exception when the real source fails.
        
        This is the CRITICAL test: it ensures no synthetic fallback is used.
        """
        # Mock load_dataset to raise an exception (simulating network failure)
        with patch('src.data_loader.load_dataset') as mock_load:
            mock_load.side_effect = Exception("Connection failed to Hugging Face Hub")
            
            # The function should raise a RuntimeError, not return synthetic data
            with pytest.raises(RuntimeError) as exc_info:
                list(data_loader.load_imagenet_validation_streaming(num_samples=1))
            
            # Verify the error message indicates real source failure
            assert "Unable to fetch real ImageNet-1k data" in str(exc_info.value)
            assert "Hugging Face Hub" in str(exc_info.value)

    def test_load_imagenet_no_synthetic_fallback(self):
        """
        Verify that NO synthetic data generation functions are called.
        
        This ensures the loader does not fall back to mock/synthetic data.
        """
        # Check that no synthetic generation functions exist in the module
        synthetic_funcs = [
            'generate_synthetic_data',
            'mock_data',
            'fake_imagenet',
            'synthetic_fallback'
        ]
        
        for func_name in synthetic_funcs:
            assert not hasattr(data_loader, func_name), (
                f"Synthetic fallback function '{func_name}' found in data_loader. "
                f"This violates the CRITICAL constraint: no synthetic fallbacks allowed."
            )

    def test_sample_structure_validation(self):
        """Test the validate_sample_structure function."""
        # Valid sample
        valid_sample = {'image': MagicMock(), 'label': 5}
        assert data_loader.validate_sample_structure(valid_sample) is True
        
        # Invalid sample - missing keys
        invalid_sample = {'image': MagicMock()}
        assert data_loader.validate_sample_structure(invalid_sample) is False
        
        invalid_sample2 = {'label': 5}
        assert data_loader.validate_sample_structure(invalid_sample2) is False

    def test_get_sample_image_data_extract_correctly(self):
        """Test extraction of image and label from sample."""
        mock_image = MagicMock()
        mock_label = 42
        
        sample = {'image': mock_image, 'label': mock_label}
        
        image, label = data_loader.get_sample_image_data(sample)
        
        assert image is mock_image
        assert label == mock_label

    def test_get_sample_image_data_raises_on_missing_keys(self):
        """Test that missing keys raise KeyError."""
        incomplete_sample = {'image': MagicMock()}
        
        with pytest.raises(KeyError) as exc_info:
            data_loader.get_sample_image_data(incomplete_sample)
        
        assert "missing required keys" in str(exc_info.value)

    def test_load_imagenet_with_num_samples_limit(self):
        """Test that num_samples limits the number of yielded items."""
        # Mock dataset with a limited iterator
        mock_sample = {'image': MagicMock(), 'label': 0}
        mock_iterator = [mock_sample, mock_sample, mock_sample]
        
        with patch('src.data_loader.load_dataset') as mock_load:
            mock_dataset = MagicMock()
            mock_dataset.__iter__ = MagicMock(return_value=iter(mock_iterator))
            mock_load.return_value = mock_dataset
            
            # Load with limit
            results = list(data_loader.load_imagenet_validation_streaming(num_samples=2))
            
            # Should only get 2 samples
            assert len(results) == 2