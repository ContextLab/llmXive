"""
Unit tests for the download module.

These tests verify that the download functions correctly handle:
- Sample size limits (500 examples)
- Streaming mode
- Error handling for unavailable datasets
- No synthetic fallbacks
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import json
import tempfile
import os

# Add the code directory to the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from src.data.download import (
    download_gsm8k_subset,
    download_minigrid_subset,
    download_all_datasets,
    DEFAULT_SAMPLE_SIZE,
    RAW_DATA_DIR
)

from itertools import islice


class TestDownloadModule:
    """Test suite for the download module."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test outputs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    @patch('src.data.download.load_dataset')
    def test_download_gsm8k_sample_limit(self, mock_load_dataset, temp_dir):
        """Test that GSM8K download respects the 500-example limit."""
        # Create mock dataset with more than 500 examples
        mock_examples = [{"id": i, "question": f"Question {i}", "answer": f"Answer {i}"} for i in range(1000)]
        mock_dataset = MagicMock()
        mock_dataset.__iter__ = MagicMock(return_value=iter(mock_examples))
        mock_load_dataset.return_value = mock_dataset
        
        output_path = temp_dir / "test_gsm8k.jsonl"
        result_path = download_gsm8k_subset(output_path, sample_size=500, streaming=True)
        
        # Verify the file was created
        assert result_path.exists()
        
        # Verify only 500 examples were written
        with open(result_path, 'r') as f:
            lines = f.readlines()
        
        assert len(lines) == 500, f"Expected 500 examples, got {len(lines)}"
        
        # Verify the content matches the first 500 examples
        for i, line in enumerate(lines):
            data = json.loads(line)
            assert data["id"] == i
    
    @patch('src.data.download.load_dataset')
    def test_download_minigrid_sample_limit(self, mock_load_dataset, temp_dir):
        """Test that MiniGrid download respects the 500-example limit."""
        # Create mock dataset with more than 500 examples
        mock_examples = [{"id": i, "grid": f"Grid {i}", "action": f"Action {i}"} for i in range(1000)]
        mock_dataset = MagicMock()
        mock_dataset.__iter__ = MagicMock(return_value=iter(mock_examples))
        mock_load_dataset.return_value = mock_dataset
        
        output_path = temp_dir / "test_minigrid.jsonl"
        result_path = download_minigrid_subset(output_path, sample_size=500, streaming=True)
        
        # Verify the file was created
        assert result_path.exists()
        
        # Verify only 500 examples were written
        with open(result_path, 'r') as f:
            lines = f.readlines()
        
        assert len(lines) == 500, f"Expected 500 examples, got {len(lines)}"
    
    @patch('src.data.download.load_dataset')
    def test_download_gsm8k_streaming_mode(self, mock_load_dataset, temp_dir):
        """Test that GSM8K download uses streaming mode correctly."""
        mock_examples = [{"id": i} for i in range(500)]
        mock_dataset = MagicMock()
        mock_dataset.__iter__ = MagicMock(return_value=iter(mock_examples))
        mock_load_dataset.return_value = mock_dataset
        
        output_path = temp_dir / "test_gsm8k_stream.jsonl"
        download_gsm8k_subset(output_path, sample_size=500, streaming=True)
        
        # Verify load_dataset was called with streaming=True
        mock_load_dataset.assert_called_once()
        call_args = mock_load_dataset.call_args
        assert call_args.kwargs.get('streaming') == True
    
    @patch('src.data.download.load_dataset')
    def test_download_minigrid_streaming_mode(self, mock_load_dataset, temp_dir):
        """Test that MiniGrid download uses streaming mode correctly."""
        mock_examples = [{"id": i} for i in range(500)]
        mock_dataset = MagicMock()
        mock_dataset.__iter__ = MagicMock(return_value=iter(mock_examples))
        mock_load_dataset.return_value = mock_dataset
        
        output_path = temp_dir / "test_minigrid_stream.jsonl"
        download_minigrid_subset(output_path, sample_size=500, streaming=True)
        
        # Verify load_dataset was called with streaming=True
        mock_load_dataset.assert_called_once()
        call_args = mock_load_dataset.call_args
        assert call_args.kwargs.get('streaming') == True
    
    def test_download_gsm8k_connection_error(self):
        """Test that GSM8K download raises ConnectionError on failure."""
        with patch('src.data.download.load_dataset') as mock_load_dataset:
            mock_load_dataset.side_effect = ConnectionError("Network error")
            
            with pytest.raises(ConnectionError, match="Network error"):
                download_gsm8k_subset()
    
    def test_download_minigrid_connection_error(self):
        """Test that MiniGrid download raises ConnectionError on failure."""
        with patch('src.data.download.load_dataset') as mock_load_dataset:
            mock_load_dataset.side_effect = ConnectionError("Network error")
            
            with pytest.raises(ConnectionError, match="Network error"):
                download_minigrid_subset()
    
    def test_download_gsm8k_file_not_found(self):
        """Test that GSM8K download raises FileNotFoundError when dataset not found."""
        with patch('src.data.download.load_dataset') as mock_load_dataset:
            mock_load_dataset.side_effect = FileNotFoundError("Dataset not found")
            
            with pytest.raises(FileNotFoundError, match="Dataset not found"):
                download_gsm8k_subset()
    
    def test_download_minigrid_file_not_found(self):
        """Test that MiniGrid download raises FileNotFoundError when dataset not found."""
        with patch('src.data.download.load_dataset') as mock_load_dataset:
            mock_load_dataset.side_effect = FileNotFoundError("Dataset not found")
            
            with pytest.raises(FileNotFoundError, match="Dataset not found"):
                download_minigrid_subset()
    
    @patch('src.data.download.download_gsm8k_subset')
    @patch('src.data.download.download_minigrid_subset')
    def test_download_all_datasets_success(
        self, mock_minigrid, mock_gsm8k, temp_dir
    ):
        """Test that download_all_datasets correctly downloads both datasets."""
        mock_gsm8k.return_value = temp_dir / "gsm8k.jsonl"
        mock_minigrid.return_value = temp_dir / "minigrid.jsonl"
        
        results = download_all_datasets(
            gsm8k_output=mock_gsm8k.return_value,
            minigrid_output=mock_minigrid.return_value,
            sample_size=500
        )
        
        assert "gsm8k" in results
        assert "minigrid" in results
        assert results["gsm8k"] == temp_dir / "gsm8k.jsonl"
        assert results["minigrid"] == temp_dir / "minigrid.jsonl"
        
        # Verify both download functions were called
        mock_gsm8k.assert_called_once()
        mock_minigrid.assert_called_once()
    
    @patch('src.data.download.download_gsm8k_subset')
    def test_download_all_datasets_gsm8k_failure(self, mock_gsm8k, temp_dir):
        """Test that download_all_datasets raises when GSM8K fails."""
        mock_gsm8k.side_effect = ConnectionError("GSM8K download failed")
        
        with pytest.raises(ConnectionError, match="GSM8K download failed"):
            download_all_datasets()
    
    @patch('src.data.download.download_gsm8k_subset')
    @patch('src.data.download.download_minigrid_subset')
    def test_download_all_datasets_minigrid_failure(
        self, mock_minigrid, mock_gsm8k, temp_dir
    ):
        """Test that download_all_datasets raises when MiniGrid fails."""
        mock_gsm8k.return_value = temp_dir / "gsm8k.jsonl"
        mock_minigrid.side_effect = ConnectionError("MiniGrid download failed")
        
        with pytest.raises(ConnectionError, match="MiniGrid download failed"):
            download_all_datasets()
    
    def test_no_synthetic_fallback(self):
        """
        Test that there is no synthetic fallback in the download functions.
        
        This test verifies that the code does not contain any calls to
        generate_synthetic_* or mock_* functions as fallbacks.
        """
        import inspect
        from src.data.download import download_gsm8k_subset, download_minigrid_subset
        
        # Get the source code of both functions
        gsm8k_source = inspect.getsource(download_gsm8k_subset)
        minigrid_source = inspect.getsource(download_minigrid_subset)
        
        # Check for synthetic fallback patterns
        synthetic_patterns = [
            "generate_synthetic",
            "mock_",
            "np.random",
            "synthetic",
            "fake_"
        ]
        
        for pattern in synthetic_patterns:
            assert pattern not in gsm8k_source, f"Found synthetic fallback in GSM8K: {pattern}"
            assert pattern not in minigrid_source, f"Found synthetic fallback in MiniGrid: {pattern}"
    
    @patch('src.data.download.load_dataset')
    def test_default_sample_size(self, mock_load_dataset, temp_dir):
        """Test that the default sample size is 500."""
        mock_examples = [{"id": i} for i in range(1000)]
        mock_dataset = MagicMock()
        mock_dataset.__iter__ = MagicMock(return_value=iter(mock_examples))
        mock_load_dataset.return_value = mock_dataset
        
        output_path = temp_dir / "test_default.jsonl"
        download_gsm8k_subset(output_path)  # Use default sample_size
        
        with open(output_path, 'r') as f:
            lines = f.readlines()
        
        assert len(lines) == DEFAULT_SAMPLE_SIZE
        assert DEFAULT_SAMPLE_SIZE == 500
    
    @patch('src.data.download.load_dataset')
    def test_custom_sample_size(self, mock_load_dataset, temp_dir):
        """Test that a custom sample size is respected."""
        custom_size = 100
        mock_examples = [{"id": i} for i in range(1000)]
        mock_dataset = MagicMock()
        mock_dataset.__iter__ = MagicMock(return_value=iter(mock_examples))
        mock_load_dataset.return_value = mock_dataset
        
        output_path = temp_dir / "test_custom.jsonl"
        download_gsm8k_subset(output_path, sample_size=custom_size)
        
        with open(output_path, 'r') as f:
            lines = f.readlines()
        
        assert len(lines) == custom_size