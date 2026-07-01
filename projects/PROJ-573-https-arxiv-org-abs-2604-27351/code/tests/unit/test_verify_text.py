"""
Unit tests for verify_text.py functionality.
"""
import pytest
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.research.verify_text import compute_dataset_checksum, estimate_dataset_size_mb

class TestVerifyTextUtils:
    
    def test_compute_dataset_checksum(self):
        """Test checksum computation on a mock dataset."""
        mock_ds = MagicMock()
        mock_ds.__len__ = MagicMock(return_value=100)
        mock_ds.select = MagicMock(return_value=["row1", "row2"])
        
        checksum = compute_dataset_checksum(mock_ds)
        
        assert isinstance(checksum, str)
        assert len(checksum) > 0
        mock_ds.select.assert_called_once()
    
    def test_estimate_dataset_size_mb(self):
        """Test size estimation on a mock dataset."""
        mock_ds = MagicMock()
        mock_ds.__len__ = MagicMock(return_value=1000)
        mock_ds.select = MagicMock(return_value=["a" * 100]) # 100 chars per row
        
        size_mb = estimate_dataset_size_mb(mock_ds)
        
        # 100 chars * 1000 rows = 100,000 bytes = ~0.095 MB
        # We expect a small positive number
        assert size_mb > 0
        assert size_mb < 1.0
        mock_ds.select.assert_called_once()
    
    @patch('src.research.verify_text.load_dataset')
    def test_verify_dataset_success(self, mock_load):
        """Test successful dataset verification."""
        mock_ds = MagicMock()
        mock_ds.__len__ = MagicMock(return_value=100)
        mock_ds.features = {"text": "string", "label": "int"}
        mock_load.return_value = mock_ds
        
        from src.research.verify_text import verify_dataset
        
        dataset_info = {
            "name": "TEST",
            "hf_id": "test_ds",
            "url": "http://test.com"
        }
        
        result = verify_dataset(dataset_info)
        
        assert result["verification_status"] == "verified"
        assert "text" in result["variables"]
        assert result["size_mb"] >= 0
        mock_load.assert_called_once_with("test_ds", split="train")
    
    @patch('src.research.verify_text.load_dataset')
    def test_verify_dataset_failure(self, mock_load):
        """Test failed dataset verification."""
        mock_load.side_effect = Exception("Connection error")
        
        from src.research.verify_text import verify_dataset
        
        dataset_info = {
            "name": "FAIL",
            "hf_id": "fail_ds",
            "url": "http://fail.com"
        }
        
        result = verify_dataset(dataset_info)
        
        assert result["verification_status"] == "failed"
        assert result["error"] is not None
        assert "Connection error" in result["error"]
