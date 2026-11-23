"""
Unit tests for the chunked loader module.
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import os

# Import the module under test
from src.loader import (
    load_slfc_dataset_chunked,
    process_slfc_dataset,
    get_memory_usage_bytes,
    format_memory_bytes,
    MEMORY_LIMIT_GB,
    MEMORY_LIMIT_BYTES
)

class TestMemoryUtils:
    """Tests for memory utility functions."""
    
    def test_format_memory_bytes_b(self):
        """Test formatting bytes to B."""
        assert "1024.00 B" in format_memory_bytes(1024)
    
    def test_format_memory_bytes_kb(self):
        """Test formatting bytes to KB."""
        assert "1.00 KB" in format_memory_bytes(1024 * 1024)
    
    def test_format_memory_bytes_mb(self):
        """Test formatting bytes to MB."""
        assert "1.00 MB" in format_memory_bytes(1024 * 1024 * 1024)
    
    def test_format_memory_bytes_gb(self):
        """Test formatting bytes to GB."""
        assert "1.00 GB" in format_memory_bytes(1024 * 1024 * 1024 * 1024)
    
    def test_get_memory_usage_bytes(self):
        """Test that memory usage function returns a positive integer."""
        mem = get_memory_usage_bytes()
        assert isinstance(mem, int)
        assert mem > 0

class TestLoadSlfcDatasetChunked:
    """Tests for the chunked dataset loader."""
    
    @patch('src.loader.load_dataset')
    def test_load_chunked_streaming(self, mock_load_dataset):
        """Test loading dataset in streaming mode."""
        # Mock dataset iterator
        mock_dataset = iter([
            {'id': 1, 'snr': 10.0, 'morph': 0.5},
            {'id': 2, 'snr': 12.0, 'morph': 0.6},
            {'id': 3, 'snr': 15.0, 'morph': 0.7},
        ])
        mock_load_dataset.return_value = mock_dataset
        
        chunks = list(load_slfc_dataset_chunked(
            dataset_name="test/dataset",
            split="train",
            chunk_size=2,
            streaming=True
        ))
        
        assert len(chunks) == 2
        assert isinstance(chunks[0], pd.DataFrame)
        assert len(chunks[0]) == 2
        assert len(chunks[1]) == 1
        
    @patch('src.loader.load_dataset')
    def test_load_chunked_non_streaming(self, mock_load_dataset):
        """Test loading dataset in non-streaming mode."""
        # Mock dataset
        mock_df = pd.DataFrame({
            'id': [1, 2, 3, 4, 5],
            'snr': [10.0, 12.0, 15.0, 8.0, 20.0],
            'morph': [0.5, 0.6, 0.7, 0.3, 0.9]
        })
        
        mock_dataset = MagicMock()
        mock_dataset.__len__ = Mock(return_value=5)
        mock_dataset.select = Mock(return_value=mock_dataset)
        mock_dataset.to_pandas = Mock(return_value=mock_df)
        mock_load_dataset.return_value = mock_dataset
        
        chunks = list(load_slfc_dataset_chunked(
            dataset_name="test/dataset",
            split="train",
            chunk_size=2,
            streaming=False
        ))
        
        assert len(chunks) == 3
        assert isinstance(chunks[0], pd.DataFrame)
        assert len(chunks[0]) == 2

class TestProcessSlfcDataset:
    """Tests for the dataset processing function."""
    
    def test_process_dataset_creates_memory_profile(self, tmp_path):
        """Test that processing creates memory profile CSV."""
        # Create a temporary directory for output
        original_output_dir = Path("data/processed")
        Path("data/processed").mkdir(parents=True, exist_ok=True)
        
        try:
            # Mock the dataset loading
            with patch('src.loader.load_dataset') as mock_load_dataset:
                mock_dataset = iter([
                    {'id': 1, 'snr': 10.0, 'morph': 0.5},
                    {'id': 2, 'snr': 12.0, 'morph': 0.6},
                ])
                mock_load_dataset.return_value = mock_dataset
                
                # Process with small chunk size
                results = process_slfc_dataset(
                    dataset_name="test/dataset",
                    split="train",
                    chunk_size=1
                )
                
                # Verify results
                assert 'total_rows' in results
                assert 'peak_memory_bytes' in results
                assert 'memory_profile_path' in results
                
                # Check that memory profile file was created
                assert Path(results['memory_profile_path']).exists()
                
        finally:
            # Clean up
            if Path("data/processed/memory_profile.csv").exists():
                Path("data/processed/memory_profile.csv").unlink()
    
    def test_process_dataset_memory_warning(self, tmp_path):
        """Test that memory warning is logged when limit exceeded."""
        # This test verifies the logic path for memory warnings
        # In practice, we can't easily trigger 6GB+ usage in tests
        
        with patch('src.loader.get_memory_usage_bytes') as mock_mem:
            # Simulate high memory usage
            mock_mem.return_value = MEMORY_LIMIT_BYTES * 2
            
            with patch('src.loader.load_dataset') as mock_load_dataset:
                mock_dataset = iter([
                    {'id': 1, 'snr': 10.0, 'morph': 0.5},
                ])
                mock_load_dataset.return_value = mock_dataset
                
                results = process_slfc_dataset(
                    dataset_name="test/dataset",
                    split="train",
                    chunk_size=1
                )
                
                assert results['memory_limit_exceeded'] is True

class TestIntegration:
    """Integration tests for the loader module."""
    
    def test_memory_profile_structure(self, tmp_path):
        """Test the structure of the memory profile CSV."""
        # Create a temporary directory for output
        Path("data/processed").mkdir(parents=True, exist_ok=True)
        
        try:
            # Mock the dataset loading
            with patch('src.loader.load_dataset') as mock_load_dataset:
                mock_dataset = iter([
                    {'id': 1, 'snr': 10.0, 'morph': 0.5},
                    {'id': 2, 'snr': 12.0, 'morph': 0.6},
                    {'id': 3, 'snr': 15.0, 'morph': 0.7},
                ])
                mock_load_dataset.return_value = mock_dataset
                
                # Process dataset
                results = process_slfc_dataset(
                    dataset_name="test/dataset",
                    split="train",
                    chunk_size=1
                )
                
                # Load and verify memory profile
                memory_df = pd.read_csv(results['memory_profile_path'])
                
                # Check required columns
                required_cols = ['chunk_id', 'timestamp', 'memory_bytes', 'memory_gb', 'rows_in_chunk']
                for col in required_cols:
                    assert col in memory_df.columns
                
                # Check data types
                assert memory_df['chunk_id'].dtype in ['int64', 'int32']
                assert memory_df['memory_bytes'].dtype in ['float64', 'int64']
                assert memory_df['memory_gb'].dtype == 'float64'
                
        finally:
            # Clean up
            if Path("data/processed/memory_profile.csv").exists():
                Path("data/processed/memory_profile.csv").unlink()
