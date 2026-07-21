"""
Unit tests for the download module.

Tests verify that:
1. Functions exist and have correct signatures
2. Error handling works correctly (fail loudly)
3. No synthetic fallbacks are used
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import json
import tempfile
import os

from src.data.download import (
    download_gsm8k_subset,
    download_minigrid_subset,
    download_all_datasets,
    GSM8K_MAX_EXAMPLES,
    MINIGRID_MAX_EXAMPLES
)

class TestDownloadModule:
    """Test suite for download module functions."""
    
    def test_download_gsm8k_subset_signature(self):
        """Test that download_gsm8k_subset has the correct signature."""
        import inspect
        sig = inspect.signature(download_gsm8k_subset)
        params = list(sig.parameters.keys())
        assert "output_dir" in params
        assert "max_examples" in params
    
    def test_download_minigrid_subset_signature(self):
        """Test that download_minigrid_subset has the correct signature."""
        import inspect
        sig = inspect.signature(download_minigrid_subset)
        params = list(sig.parameters.keys())
        assert "output_dir" in params
        assert "max_examples" in params
        assert "environment" in params
    
    def test_constants_defined(self):
        """Test that max example constants are defined."""
        assert GSM8K_MAX_EXAMPLES == 500
        assert MINIGRID_MAX_EXAMPLES == 500
    
    @patch('src.data.download.load_dataset')
    def test_download_gsm8k_creates_output(self, mock_load_dataset):
        """Test that GSM8K download creates output files."""
        # Mock the dataset iterator
        mock_dataset = MagicMock()
        mock_dataset.__iter__ = MagicMock(return_value=iter([
            {"question": "Test question 1", "answer": "Test answer 1"},
            {"question": "Test question 2", "answer": "Test answer 2"},
        ]))
        mock_load_dataset.return_value = mock_dataset
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = download_gsm8k_subset(output_dir=tmpdir, max_examples=2)
            
            # Check that output directory exists
            assert Path(output_path).exists()
            
            # Check that JSONL file was created
            jsonl_file = Path(output_path) / "gsm8k_subset.jsonl"
            assert jsonl_file.exists()
            
            # Check that metadata file was created
            metadata_file = Path(output_path) / "metadata.json"
            assert metadata_file.exists()
            
            # Verify metadata content
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            assert metadata["dataset"] == "gsm8k"
            assert metadata["total_examples"] == 2
    
    @patch('src.data.download.load_dataset')
    def test_download_minigrid_creates_output(self, mock_load_dataset):
        """Test that MiniGrid download creates output files."""
        # Mock the dataset iterator
        mock_dataset = MagicMock()
        mock_dataset.__iter__ = MagicMock(return_value=iter([
            {"grid": [[0, 1, 2]], "goal": "reach goal"},
            {"grid": [[3, 4, 5]], "goal": "reach goal"},
        ]))
        mock_load_dataset.return_value = mock_dataset
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = download_minigrid_subset(output_dir=tmpdir, max_examples=2)
            
            # Check that output directory exists
            assert Path(output_path).exists()
            
            # Check that JSONL file was created
            jsonl_file = Path(output_path) / "minigrid_subset.jsonl"
            assert jsonl_file.exists()
            
            # Check that metadata file was created
            metadata_file = Path(output_path) / "metadata.json"
            assert metadata_file.exists()
    
    @patch('src.data.download.load_dataset')
    def test_download_gsm8k_respects_max_examples(self, mock_load_dataset):
        """Test that GSM8K download respects max_examples limit."""
        # Create more mock examples than requested
        mock_examples = [{"question": f"Q{i}", "answer": f"A{i}"} for i in range(100)]
        mock_dataset = MagicMock()
        mock_dataset.__iter__ = MagicMock(return_value=iter(mock_examples))
        mock_load_dataset.return_value = mock_dataset
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = download_gsm8k_subset(output_dir=tmpdir, max_examples=10)
            
            # Read the output file
            jsonl_file = Path(output_path) / "gsm8k_subset.jsonl"
            with open(jsonl_file, 'r') as f:
                lines = f.readlines()
            
            # Verify only max_examples were written
            assert len(lines) == 10
    
    def test_fail_loudly_on_network_error(self):
        """Test that network errors raise ConnectionError (fail loudly)."""
        with patch('src.data.download.load_dataset') as mock_load:
            mock_load.side_effect = ConnectionError("Network error")
            
            with tempfile.TemporaryDirectory() as tmpdir:
                with pytest.raises(ConnectionError) as exc_info:
                    download_gsm8k_subset(output_dir=tmpdir, max_examples=10)
                
                assert "Network error" in str(exc_info.value)
    
    def test_fail_loudly_on_dataset_not_found(self):
        """Test that missing dataset raises FileNotFoundError (fail loudly)."""
        with patch('src.data.download.load_dataset') as mock_load:
            mock_load.side_effect = FileNotFoundError("Dataset not found")
            
            with tempfile.TemporaryDirectory() as tmpdir:
                with pytest.raises(FileNotFoundError) as exc_info:
                    download_minigrid_subset(output_dir=tmpdir, max_examples=10)
                
                assert "Dataset not found" in str(exc_info.value)
    
    def test_no_synthetic_fallback(self):
        """Test that no synthetic data generation functions are called."""
        # Check that the module does not contain synthetic generation functions
        import src.data.download as download_module
        
        # These should NOT exist in the module
        assert not hasattr(download_module, 'generate_synthetic_gsm8k')
        assert not hasattr(download_module, 'generate_synthetic_minigrid')
        assert not hasattr(download_module, 'mock_gsm8k_data')
        assert not hasattr(download_module, 'mock_minigrid_data')
    
    @patch('src.data.download.load_dataset')
    def test_download_all_datasets(self, mock_load_dataset):
        """Test download_all_datasets function."""
        # Mock both datasets
        mock_gsm8k = MagicMock()
        mock_gsm8k.__iter__ = MagicMock(return_value=iter([
            {"question": "Q1", "answer": "A1"},
        ]))
        
        mock_minigrid = MagicMock()
        mock_minigrid.__iter__ = MagicMock(return_value=iter([
            {"grid": [[1, 2]], "goal": "goal"},
        ]))
        
        # Set up side effect to return different datasets based on name
        def dataset_side_effect(name, *args, **kwargs):
            if name == "gsm8k":
                return mock_gsm8k
            elif name == "minigrid":
                return mock_minigrid
            else:
                raise ValueError(f"Unknown dataset: {name}")
        
        mock_load_dataset.side_effect = dataset_side_effect
        
        with tempfile.TemporaryDirectory() as tmpdir:
            results = download_all_datasets(output_base_dir=tmpdir)
            
            assert "gsm8k" in results
            assert "minigrid" in results
            assert Path(results["gsm8k"]).exists()
            assert Path(results["minigrid"]).exists()
    
    def test_download_gsm8k_empty_dataset_raises(self):
        """Test that empty dataset raises RuntimeError."""
        with patch('src.data.download.load_dataset') as mock_load:
            # Return an empty iterator
            mock_dataset = MagicMock()
            mock_dataset.__iter__ = MagicMock(return_value=iter([]))
            mock_load.return_value = mock_dataset
            
            with tempfile.TemporaryDirectory() as tmpdir:
                with pytest.raises(RuntimeError) as exc_info:
                    download_gsm8k_subset(output_dir=tmpdir, max_examples=10)
                
                assert "No examples were fetched" in str(exc_info.value)
    
    def test_download_minigrid_empty_dataset_raises(self):
        """Test that empty MiniGrid dataset raises RuntimeError."""
        with patch('src.data.download.load_dataset') as mock_load:
            # Return an empty iterator
            mock_dataset = MagicMock()
            mock_dataset.__iter__ = MagicMock(return_value=iter([]))
            mock_load.return_value = mock_dataset
            
            with tempfile.TemporaryDirectory() as tmpdir:
                with pytest.raises(RuntimeError) as exc_info:
                    download_minigrid_subset(output_dir=tmpdir, max_examples=10)
                
                assert "No examples were fetched" in str(exc_info.value)