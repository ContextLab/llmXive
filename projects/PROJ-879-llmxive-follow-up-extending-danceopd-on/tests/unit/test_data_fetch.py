#!/usr/bin/env python
"""
Unit tests for the real data streaming fetcher in code/00_data_fetch.py
"""
import pytest
import sys
from pathlib import Path
import tempfile
import json
import yaml
from unittest.mock import patch, MagicMock
import io

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.utils.config import get_config
from code._00_data_fetch import (
    calculate_sha256_stream,
    fetch_real_data,
    calculate_sha256
)

class TestDataFetcher:
    """Test cases for the data fetcher module."""
    
    def test_calculate_sha256_stream(self):
        """Test SHA256 calculation on a byte stream."""
        test_data = b"Hello, World!"
        stream = io.BytesIO(test_data)
        
        hash_result = calculate_sha256_stream(stream)
        
        # Expected SHA256 for "Hello, World!"
        expected_hash = "315f5bdb76d078c43b8ac0064e4a0164612b1fce77c869345bfc94c75894edd3"
        assert hash_result == expected_hash
    
    def test_calculate_sha256_stream_empty(self):
        """Test SHA256 calculation on empty stream."""
        stream = io.BytesIO(b"")
        hash_result = calculate_sha256_stream(stream)
        
        # SHA256 of empty string
        expected_hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        assert hash_result == expected_hash
    
    @patch('code._00_data_fetch.load_dataset')
    @patch('code._00_data_fetch.pd.DataFrame')
    @patch('code._00_data_fetch.Path')
    def test_fetch_real_data_success(self, mock_path, mock_df, mock_load_dataset):
        """Test successful data fetch with mocked dataset."""
        # Mock config
        mock_config = MagicMock()
        mock_config.get_path.return_value = "/tmp/test_state"
        
        # Mock dataset iterator
        mock_item = {
            "image": MagicMock(),
            "label": 0
        }
        mock_item["image"].save = MagicMock()
        
        mock_ds = MagicMock()
        mock_ds.__iter__ = MagicMock(return_value=iter([mock_item] * 10))
        mock_load_dataset.return_value = mock_ds
        
        # Mock DataFrame
        mock_df_instance = MagicMock()
        mock_df.return_value = mock_df_instance
        
        # Create temporary directories
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            output_path = tmp_path / "test_output.parquet"
            state_path = tmp_path / "state"
            state_path.mkdir()
            
            # Mock Path operations
            mock_path_instance = MagicMock()
            mock_path_instance.mkdir = MagicMock()
            mock_path_instance.exists = MagicMock(return_value=False)
            mock_path_instance.__truediv__ = lambda self, x: tmp_path / x
            mock_path.return_value = mock_path_instance
            
            # Call fetch_real_data
            result = fetch_real_data(
                source_name="test",
                dataset_id="test/dataset",
                output_path=output_path,
                target_n=10,
                config=mock_config,
                stream_hash_key="test_hash"
            )
            
            # Verify result
            assert result["status"] == "success"
            assert result["samples_fetched"] == 10
            assert "stream_hash" in result
            assert "output_path" in result
    
    @patch('code._00_data_fetch.load_dataset')
    def test_fetch_real_data_empty_stream(self, mock_load_dataset):
        """Test fetch with empty dataset stream."""
        mock_config = MagicMock()
        mock_config.get_path.return_value = "/tmp/test_state"
        
        # Mock empty dataset
        mock_ds = MagicMock()
        mock_ds.__iter__ = MagicMock(return_value=iter([]))
        mock_load_dataset.return_value = mock_ds
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            output_path = tmp_path / "test_output.parquet"
            
            # Should raise RuntimeError for empty stream
            with pytest.raises(RuntimeError, match="No samples fetched"):
                fetch_real_data(
                    source_name="test",
                    dataset_id="test/dataset",
                    output_path=output_path,
                    target_n=10,
                    config=mock_config,
                    stream_hash_key="test_hash"
                )
    
    def test_calculate_sha256_file(self):
        """Test SHA256 calculation on a file."""
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            f.write(b"Test data")
            temp_path = Path(f.name)
        
        try:
            hash_result = calculate_sha256(temp_path)
            
            # Expected SHA256 for "Test data"
            expected_hash = "d5579c46dfcc7f18207013e65b44e4cb4e2c2298f4ac457ba8f82743f31e930b"
            assert hash_result == expected_hash
        finally:
            temp_path.unlink()
